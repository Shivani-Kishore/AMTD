// AMTD - Automated Malware Target Detection
// Jenkins Pipeline for Security Scanning

@Library('amtd-shared-library') _

pipeline {
    agent {
        label 'docker'
    }

    parameters {
        string(
            name: 'APPLICATION',
            defaultValue: 'juice-shop',
            description: 'Application name (config file without .yaml)'
        )
        choice(
            name: 'SCAN_TYPE',
            choices: ['full', 'quick', 'incremental'],
            description: 'Type of scan to perform'
        )
        string(
            name: 'ENVIRONMENT',
            defaultValue: 'development',
            description: 'Environment (development, staging, production)'
        )
        booleanParam(
            name: 'SEND_NOTIFICATIONS',
            defaultValue: true,
            description: 'Send notifications on scan completion'
        )
        booleanParam(
            name: 'CREATE_GITHUB_ISSUES',
            defaultValue: false,
            description: 'Create GitHub issues for critical/high vulnerabilities'
        )
    }

    environment {
        // Application configuration
        APP_CONFIG = "${WORKSPACE}/config/applications/${params.APPLICATION}.yaml"

        // Python environment
        PYTHONPATH = "${WORKSPACE}"
        PYTHON_BIN = 'python3'

        // Report directory
        REPORT_DIR = "${WORKSPACE}/reports/${BUILD_NUMBER}"

        // Docker configuration
        DOCKER_NETWORK = 'amtd-network'

        // Scan metadata
        SCAN_ID = "${BUILD_NUMBER}_${params.APPLICATION}_${new Date().format('yyyyMMdd_HHmmss')}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '10'))
        timestamps()
        timeout(time: 3, unit: 'HOURS')
        disableConcurrentBuilds()
    }

    stages {
        stage('Preparation') {
            steps {
                script {
                    echo "=" * 80
                    echo "AMTD Security Scan Pipeline"
                    echo "=" * 80
                    echo "Build Number: ${BUILD_NUMBER}"
                    echo "Application: ${params.APPLICATION}"
                    echo "Scan Type: ${params.SCAN_TYPE}"
                    echo "Environment: ${params.ENVIRONMENT}"
                    echo "Scan ID: ${SCAN_ID}"
                    echo "=" * 80

                    // Validate application configuration exists
                    if (!fileExists(env.APP_CONFIG)) {
                        error("Application configuration not found: ${env.APP_CONFIG}")
                    }

                    // Create report directory
                    sh "mkdir -p ${REPORT_DIR}"

                    // Display configuration summary
                    sh """
                        ${PYTHON_BIN} scripts/scan-executor.py \\
                            --application ${params.APPLICATION} \\
                            --environment ${params.ENVIRONMENT} \\
                            --validate-only
                    """
                }
            }
        }

        stage('Environment Setup') {
            steps {
                script {
                    echo "Setting up scan environment..."

                    // Install Python dependencies if needed
                    sh """
                        pip3 install --quiet -r requirements.txt
                    """

                    // Verify Docker connectivity
                    sh 'docker ps'

                    // Check target application accessibility
                    amtdValidateTarget(params.APPLICATION)
                }
            }
        }

        stage('Security Scan') {
            steps {
                script {
                    echo "Starting security scan..."
                    echo "This may take 30-120 minutes depending on application size"

                    // Execute scan using Python script
                    def scanStatus = sh(
                        script: """
                            ${PYTHON_BIN} scripts/scan-executor.py \\
                                --application ${params.APPLICATION} \\
                                --scan-type ${params.SCAN_TYPE} \\
                                --environment ${params.ENVIRONMENT} \\
                                --output-dir ${REPORT_DIR} \\
                                --verbose
                        """,
                        returnStatus: true
                    )

                    // Store scan status for later use
                    env.SCAN_STATUS = scanStatus

                    if (scanStatus == 0) {
                        echo "Scan completed successfully with no threshold violations"
                    } else if (scanStatus == 1) {
                        echo "WARNING: Scan completed but vulnerability thresholds exceeded"
                        currentBuild.result = 'UNSTABLE'
                    } else {
                        error("Scan execution failed with status: ${scanStatus}")
                    }
                }
            }
        }

        stage('Process Results') {
            steps {
                script {
                    echo "Processing scan results..."

                    // Find the generated JSON report
                    def jsonReport = sh(
                        script: "find ${REPORT_DIR} -name '*.json' -type f | head -1",
                        returnStdout: true
                    ).trim()

                    if (jsonReport) {
                        echo "Found report: ${jsonReport}"

                        // Parse and display summary
                        def results = readJSON file: jsonReport
                        def stats = results.statistics ?: [:]

                        echo "=" * 80
                        echo "Vulnerability Summary:"
                        echo "  Critical: ${stats.critical ?: 0}"
                        echo "  High:     ${stats.high ?: 0}"
                        echo "  Medium:   ${stats.medium ?: 0}"
                        echo "  Low:      ${stats.low ?: 0}"
                        echo "  Info:     ${stats.info ?: 0}"
                        echo "  Total:    ${stats.total ?: 0}"
                        echo "=" * 80

                        // Store results for later stages
                        env.SCAN_RESULTS = jsonReport
                        env.CRITICAL_COUNT = stats.critical ?: 0
                        env.HIGH_COUNT = stats.high ?: 0
                        env.MEDIUM_COUNT = stats.medium ?: 0
                    } else {
                        error("No scan results found in ${REPORT_DIR}")
                    }
                }
            }
        }

        stage('Generate Reports') {
            steps {
                script {
                    echo "Generating additional report formats..."

                    // Archive all reports
                    archiveArtifacts(
                        artifacts: "reports/${BUILD_NUMBER}/**/*",
                        allowEmptyArchive: false,
                        fingerprint: true
                    )

                    // Publish HTML report if exists
                    def htmlReports = findFiles(glob: "reports/${BUILD_NUMBER}/*.html")
                    if (htmlReports.length > 0) {
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: "reports/${BUILD_NUMBER}",
                            reportFiles: htmlReports[0].name,
                            reportName: 'Security Scan Report',
                            reportTitles: "AMTD Security Scan - ${params.APPLICATION}"
                        ])
                    }
                }
            }
        }

        stage('Store Results') {
            when {
                expression { return fileExists('scripts/store-results.py') }
            }
            steps {
                script {
                    echo "Storing results in database..."

                    // Store scan results in PostgreSQL
                    sh """
                        ${PYTHON_BIN} scripts/store-results.py \\
                            --scan-id ${SCAN_ID} \\
                            --application ${params.APPLICATION} \\
                            --results ${env.SCAN_RESULTS} \\
                            --build-number ${BUILD_NUMBER} \\
                            --build-url ${BUILD_URL}
                    """
                }
            }
        }

        stage('GitHub Integration') {
            when {
                allOf {
                    expression { return params.CREATE_GITHUB_ISSUES }
                    expression { return env.CRITICAL_COUNT.toInteger() > 0 || env.HIGH_COUNT.toInteger() > 0 }
                }
            }
            steps {
                script {
                    echo "Creating GitHub issues for critical/high vulnerabilities..."

                    withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                        sh """
                            export GITHUB_TOKEN='${GITHUB_TOKEN}'
                            ${PYTHON_BIN} scripts/create-github-issues.py \\
                                --results ${env.SCAN_RESULTS} \\
                                --application ${params.APPLICATION} \\
                                --severity critical,high
                        """
                    }
                }
            }
        }

        stage('Notifications') {
            when {
                expression { return params.SEND_NOTIFICATIONS }
            }
            steps {
                script {
                    echo "Sending notifications..."

                    // Send notifications based on scan results
                    amtdSendNotifications(
                        application: params.APPLICATION,
                        scanResults: env.SCAN_RESULTS,
                        buildUrl: env.BUILD_URL,
                        buildStatus: currentBuild.result ?: 'SUCCESS'
                    )
                }
            }
        }

        stage('Quality Gate') {
            steps {
                script {
                    echo "Checking quality gate thresholds..."

                    def criticalCount = env.CRITICAL_COUNT.toInteger()
                    def highCount = env.HIGH_COUNT.toInteger()

                    // Fail build if critical vulnerabilities found
                    if (criticalCount > 0) {
                        echo "FAILED: Found ${criticalCount} critical vulnerabilities"
                        currentBuild.result = 'FAILURE'
                        error("Critical vulnerabilities detected - failing build")
                    }

                    // Mark unstable if high vulnerabilities exceed threshold
                    if (highCount > 5) {
                        echo "UNSTABLE: Found ${highCount} high severity vulnerabilities (threshold: 5)"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                echo "Cleaning up..."

                // Clean up Docker containers
                sh '''
                    docker ps -a --filter "label=amtd-scan" --filter "label=scan-id=${SCAN_ID}" -q | xargs -r docker rm -f
                '''

                // Record build metrics
                if (fileExists('scripts/record-metrics.py')) {
                    sh """
                        ${PYTHON_BIN} scripts/record-metrics.py \\
                            --build-number ${BUILD_NUMBER} \\
                            --duration \${BUILD_DURATION} \\
                            --status \${currentBuild.result}
                    """
                }
            }
        }

        success {
            echo "Scan completed successfully!"
            echo "View report at: ${BUILD_URL}Security_Scan_Report/"
        }

        unstable {
            echo "Scan completed with warnings - vulnerability thresholds exceeded"
            echo "View report at: ${BUILD_URL}Security_Scan_Report/"
        }

        failure {
            echo "Scan failed! Check console output for details."

            // Send failure notification
            emailext(
                subject: "AMTD Scan Failed: ${params.APPLICATION}",
                body: """
                    <h2>AMTD Security Scan Failed</h2>
                    <p><strong>Application:</strong> ${params.APPLICATION}</p>
                    <p><strong>Build:</strong> #${BUILD_NUMBER}</p>
                    <p><strong>Status:</strong> FAILED</p>
                    <p><a href="${BUILD_URL}console">View Console Output</a></p>
                """,
                recipientProviders: [developers(), requestor()],
                mimeType: 'text/html'
            )
        }

        cleanup {
            // Clean workspace if needed
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'reports/**', type: 'EXCLUDE'],
                    [pattern: '**/*.log', type: 'INCLUDE']
                ]
            )
        }
    }
}
