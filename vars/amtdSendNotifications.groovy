#!/usr/bin/env groovy

/**
 * Send notifications based on scan results
 *
 * @param config Configuration map with:
 *   - application: Application name
 *   - scanResults: Path to JSON results file
 *   - buildUrl: Jenkins build URL
 *   - buildStatus: Build status (SUCCESS, UNSTABLE, FAILURE)
 */
def call(Map config) {
    echo "Sending notifications for ${config.application}..."

    // Read scan results
    def results = readJSON file: config.scanResults
    def stats = results.statistics ?: [:]

    // Determine notification severity
    def severity = 'info'
    if (stats.critical > 0) {
        severity = 'critical'
    } else if (stats.high > 5) {
        severity = 'high'
    } else if (stats.medium > 20) {
        severity = 'medium'
    }

    // Send email notification
    sendEmailNotification(config, stats, severity)

    // Send Slack notification if configured
    if (env.SLACK_WEBHOOK_URL) {
        sendSlackNotification(config, stats, severity)
    }
}

private void sendEmailNotification(Map config, Map stats, String severity) {
    def subject = "AMTD Scan: ${config.application} - ${config.buildStatus}"

    def severityColor = [
        'critical': '#DC3545',
        'high': '#FD7E14',
        'medium': '#FFC107',
        'low': '#28A745',
        'info': '#17A2B8'
    ]

    def color = severityColor[severity] ?: '#6C757D'

    def body = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: ${color}; color: white; padding: 20px; }
                .content { padding: 20px; }
                .stats { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
                .stat-item { margin: 10px 0; }
                .critical { color: #DC3545; font-weight: bold; }
                .high { color: #FD7E14; font-weight: bold; }
                .medium { color: #FFC107; font-weight: bold; }
                .button { background-color: #007BFF; color: white; padding: 10px 20px;
                         text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>AMTD Security Scan Report</h2>
                <p>Application: ${config.application}</p>
            </div>
            <div class="content">
                <h3>Scan Summary</h3>
                <div class="stats">
                    <div class="stat-item critical">Critical: ${stats.critical ?: 0}</div>
                    <div class="stat-item high">High: ${stats.high ?: 0}</div>
                    <div class="stat-item medium">Medium: ${stats.medium ?: 0}</div>
                    <div class="stat-item">Low: ${stats.low ?: 0}</div>
                    <div class="stat-item">Info: ${stats.info ?: 0}</div>
                    <div class="stat-item"><strong>Total: ${stats.total ?: 0}</strong></div>
                </div>
                <p><strong>Build Status:</strong> ${config.buildStatus}</p>
                <a href="${config.buildUrl}Security_Scan_Report/" class="button">View Full Report</a>
            </div>
        </body>
        </html>
    """

    emailext(
        subject: subject,
        body: body,
        recipientProviders: [developers(), requestor()],
        mimeType: 'text/html',
        attachLog: config.buildStatus == 'FAILURE'
    )

    echo "Email notification sent"
}

private void sendSlackNotification(Map config, Map stats, String severity) {
    def severityEmoji = [
        'critical': ':red_circle:',
        'high': ':orange_circle:',
        'medium': ':yellow_circle:',
        'low': ':green_circle:',
        'info': ':blue_circle:'
    ]

    def emoji = severityEmoji[severity] ?: ':white_circle:'

    def color = [
        'SUCCESS': 'good',
        'UNSTABLE': 'warning',
        'FAILURE': 'danger'
    ]

    def message = """
        ${emoji} *AMTD Security Scan: ${config.application}*

        *Status:* ${config.buildStatus}

        *Vulnerabilities:*
        • Critical: ${stats.critical ?: 0}
        • High: ${stats.high ?: 0}
        • Medium: ${stats.medium ?: 0}
        • Low: ${stats.low ?: 0}
        • Total: ${stats.total ?: 0}

        <${config.buildUrl}Security_Scan_Report/|View Report>
    """

    try {
        sh """
            curl -X POST '${env.SLACK_WEBHOOK_URL}' \\
                -H 'Content-Type: application/json' \\
                -d '{
                    "text": "${message.replaceAll('"', '\\\\"').replaceAll('\n', '\\\\n')}",
                    "color": "${color[config.buildStatus] ?: 'warning'}"
                }'
        """
        echo "Slack notification sent"
    } catch (Exception e) {
        echo "Failed to send Slack notification: ${e.message}"
    }
}
