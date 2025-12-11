#!/usr/bin/env groovy

/**
 * Validate target application accessibility
 *
 * @param application Application name
 */
def call(String application) {
    echo "Validating target application: ${application}"

    // Load application configuration
    def config = readYaml file: "config/applications/${application}.yaml"

    if (!config?.application?.url) {
        error("No URL found in application configuration")
    }

    def targetUrl = config.application.url

    echo "Target URL: ${targetUrl}"

    // Try to reach the target
    def statusCode = sh(
        script: "curl -s -o /dev/null -w '%{http_code}' --max-time 10 '${targetUrl}' || echo '000'",
        returnStdout: true
    ).trim()

    if (statusCode == '000') {
        echo "WARNING: Unable to reach target URL: ${targetUrl}"
        echo "The scan will proceed, but may fail if the target is not accessible"
    } else {
        echo "Target is accessible (HTTP ${statusCode})"
    }

    return statusCode
}
