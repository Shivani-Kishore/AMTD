#!/usr/bin/env groovy

/**
 * Execute AMTD security scan
 * Main wrapper function for running scans
 *
 * @param config Configuration map with:
 *   - application: Application name (required)
 *   - scanType: Scan type (full, quick, incremental)
 *   - environment: Environment name
 *   - notifications: Whether to send notifications
 */
def call(Map config) {
    // Validate required parameters
    if (!config.application) {
        error("Application name is required")
    }

    // Set defaults
    def application = config.application
    def scanType = config.scanType ?: 'full'
    def environment = config.environment ?: 'development'
    def notifications = config.notifications != null ? config.notifications : true

    echo "=" * 80
    echo "AMTD Security Scan"
    echo "=" * 80
    echo "Application: ${application}"
    echo "Scan Type: ${scanType}"
    echo "Environment: ${environment}"
    echo "Notifications: ${notifications}"
    echo "=" * 80

    def scanResults = null

    try {
        // Stage 1: Validate
        stage('Validate Configuration') {
            validateConfiguration(application)
        }

        // Stage 2: Execute Scan
        stage('Execute Scan') {
            scanResults = executeScan(application, scanType, environment)
        }

        // Stage 3: Process Results
        stage('Process Results') {
            processResults(scanResults)
        }

        // Stage 4: Notifications
        if (notifications) {
            stage('Send Notifications') {
                amtdSendNotifications(
                    application: application,
                    scanResults: scanResults.reportPath,
                    buildUrl: env.BUILD_URL,
                    buildStatus: currentBuild.result ?: 'SUCCESS'
                )
            }
        }

        return scanResults

    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        echo "Scan failed: ${e.message}"
        throw e
    }
}

private void validateConfiguration(String application) {
    echo "Validating configuration for ${application}..."

    def configFile = "config/applications/${application}.yaml"

    if (!fileExists(configFile)) {
        error("Configuration file not found: ${configFile}")
    }

    // Validate using Python script
    sh """
        python3 scripts/scan-executor.py \\
            --application ${application} \\
            --validate-only
    """

    echo "Configuration validated successfully"
}

private Map executeScan(String application, String scanType, String environment) {
    echo "Executing ${scanType} scan for ${application}..."

    def reportDir = "${env.WORKSPACE}/reports/${env.BUILD_NUMBER}"
    sh "mkdir -p ${reportDir}"

    // Execute scan
    def status = sh(
        script: """
            python3 scripts/scan-executor.py \\
                --application ${application} \\
                --scan-type ${scanType} \\
                --environment ${environment} \\
                --output-dir ${reportDir} \\
                --verbose
        """,
        returnStatus: true
    )

    // Find generated report
    def reportPath = sh(
        script: "find ${reportDir} -name '*.json' -type f | head -1",
        returnStdout: true
    ).trim()

    if (!reportPath) {
        error("No scan results generated")
    }

    // Read results
    def results = readJSON file: reportPath

    return [
        status: status,
        reportPath: reportPath,
        results: results,
        statistics: results.statistics ?: [:]
    ]
}

private void processResults(Map scanResults) {
    echo "Processing scan results..."

    def stats = scanResults.statistics

    echo "Vulnerability Summary:"
    echo "  Critical: ${stats.critical ?: 0}"
    echo "  High: ${stats.high ?: 0}"
    echo "  Medium: ${stats.medium ?: 0}"
    echo "  Low: ${stats.low ?: 0}"
    echo "  Info: ${stats.info ?: 0}"
    echo "  Total: ${stats.total ?: 0}"

    // Archive reports
    archiveArtifacts(
        artifacts: "reports/${env.BUILD_NUMBER}/**/*",
        allowEmptyArchive: false,
        fingerprint: true
    )

    // Check thresholds
    if (stats.critical > 0) {
        currentBuild.result = 'UNSTABLE'
        echo "WARNING: Found ${stats.critical} critical vulnerabilities"
    }

    if (stats.high > 5) {
        currentBuild.result = 'UNSTABLE'
        echo "WARNING: Found ${stats.high} high severity vulnerabilities (threshold: 5)"
    }
}
