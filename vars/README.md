# AMTD Jenkins Shared Library

This directory contains the Jenkins shared library functions for AMTD security scanning.

## Available Functions

### amtdScan

Main function to execute a security scan.

**Usage:**
```groovy
@Library('amtd-shared-library') _

amtdScan(
    application: 'my-app',
    scanType: 'full',
    environment: 'production',
    notifications: true
)
```

**Parameters:**
- `application` (String, required) - Application name (config file without .yaml)
- `scanType` (String, optional) - Scan type: 'full', 'quick', or 'incremental'. Default: 'full'
- `environment` (String, optional) - Environment name. Default: 'development'
- `notifications` (Boolean, optional) - Send notifications. Default: true

**Example:**
```groovy
pipeline {
    agent any

    stages {
        stage('Security Scan') {
            steps {
                script {
                    amtdScan(
                        application: 'juice-shop',
                        scanType: 'full'
                    )
                }
            }
        }
    }
}
```

### amtdValidateTarget

Validates that the target application is accessible.

**Usage:**
```groovy
amtdValidateTarget('my-app')
```

**Parameters:**
- `application` (String) - Application name

**Returns:**
- HTTP status code (String)

**Example:**
```groovy
def status = amtdValidateTarget('juice-shop')
if (status != '200') {
    echo "Warning: Target may not be fully accessible"
}
```

### amtdSendNotifications

Sends notifications based on scan results.

**Usage:**
```groovy
amtdSendNotifications(
    application: 'my-app',
    scanResults: '/path/to/results.json',
    buildUrl: env.BUILD_URL,
    buildStatus: 'SUCCESS'
)
```

**Parameters:**
- `application` (String) - Application name
- `scanResults` (String) - Path to JSON results file
- `buildUrl` (String) - Jenkins build URL
- `buildStatus` (String) - Build status: 'SUCCESS', 'UNSTABLE', or 'FAILURE'

**Example:**
```groovy
post {
    always {
        amtdSendNotifications(
            application: params.APPLICATION,
            scanResults: "${WORKSPACE}/reports/scan.json",
            buildUrl: env.BUILD_URL,
            buildStatus: currentBuild.result ?: 'SUCCESS'
        )
    }
}
```

## Configuration

### Jenkins Global Library Configuration

1. Navigate to **Manage Jenkins** > **Configure System**
2. Scroll to **Global Pipeline Libraries**
3. Add a new library:
   - **Name:** `amtd-shared-library`
   - **Default version:** `main` (or your branch name)
   - **Retrieval method:** Modern SCM
   - **Source Code Management:** Git
   - **Project Repository:** `https://github.com/your-org/amtd.git`

### Environment Variables

Set these in Jenkins credentials or environment:

```groovy
// For Slack notifications
SLACK_WEBHOOK_URL = credentials('slack-webhook-url')

// For GitHub integration
GITHUB_TOKEN = credentials('github-token')

// For email notifications (usually configured in Jenkins)
// No additional variables needed
```

## Complete Pipeline Example

```groovy
@Library('amtd-shared-library') _

pipeline {
    agent {
        label 'docker'
    }

    parameters {
        string(name: 'APPLICATION', defaultValue: 'juice-shop')
        choice(name: 'SCAN_TYPE', choices: ['full', 'quick', 'incremental'])
        string(name: 'ENVIRONMENT', defaultValue: 'development')
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '30'))
        timestamps()
        timeout(time: 2, unit: 'HOURS')
    }

    stages {
        stage('Validate') {
            steps {
                script {
                    def status = amtdValidateTarget(params.APPLICATION)
                    echo "Target status: ${status}"
                }
            }
        }

        stage('Scan') {
            steps {
                script {
                    def results = amtdScan(
                        application: params.APPLICATION,
                        scanType: params.SCAN_TYPE,
                        environment: params.ENVIRONMENT,
                        notifications: false
                    )

                    // Access results
                    echo "Found ${results.statistics.total} vulnerabilities"
                }
            }
        }

        stage('Notify') {
            steps {
                script {
                    amtdSendNotifications(
                        application: params.APPLICATION,
                        scanResults: "${WORKSPACE}/reports/${BUILD_NUMBER}/*.json",
                        buildUrl: env.BUILD_URL,
                        buildStatus: currentBuild.result ?: 'SUCCESS'
                    )
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

## Multibranch Pipeline

For scanning on pull requests:

```groovy
@Library('amtd-shared-library') _

pipeline {
    agent any

    stages {
        stage('Security Scan') {
            when {
                changeRequest()
            }
            steps {
                script {
                    amtdScan(
                        application: env.CHANGE_TARGET, // Use branch name
                        scanType: 'quick', // Use quick scan for PRs
                        notifications: true
                    )
                }
            }
        }
    }
}
```

## Scheduled Scans

For nightly scans:

```groovy
@Library('amtd-shared-library') _

pipeline {
    agent any

    triggers {
        cron('H 2 * * *') // Run at 2 AM daily
    }

    stages {
        stage('Nightly Scans') {
            steps {
                script {
                    def apps = ['app1', 'app2', 'app3']

                    apps.each { app ->
                        stage("Scan ${app}") {
                            amtdScan(
                                application: app,
                                scanType: 'full',
                                notifications: true
                            )
                        }
                    }
                }
            }
        }
    }
}
```

## Troubleshooting

### Library Not Found

If you see "Library 'amtd-shared-library' not found":
1. Check the library is configured in Jenkins
2. Verify the repository URL and credentials
3. Ensure the `vars/` directory is in the root of the repository

### Function Not Found

If a function like `amtdScan` is not found:
1. Verify the `.groovy` file exists in `vars/` directory
2. Check file permissions
3. Restart Jenkins to reload libraries

### Scan Failures

If scans fail:
1. Check the Python script is executable
2. Verify Docker is accessible from Jenkins agent
3. Check application configuration file exists
4. Review Jenkins console output for detailed errors

## Best Practices

1. **Use Parameters:** Make pipelines configurable with parameters
2. **Error Handling:** Wrap scans in try-catch blocks
3. **Cleanup:** Always clean up Docker containers in post actions
4. **Notifications:** Send notifications for all build statuses
5. **Artifacts:** Archive scan reports for historical analysis
6. **Thresholds:** Define vulnerability thresholds in application config
7. **Parallel Scans:** Use parallel stages for multiple applications

## Support

For issues or questions:
- Check Jenkins console output
- Review scan logs in `reports/` directory
- See main AMTD documentation in `docs/`
- Contact: support@example.com
