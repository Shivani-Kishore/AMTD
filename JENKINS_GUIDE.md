# AMTD Jenkins Integration Guide

Complete guide for setting up and using AMTD with Jenkins CI/CD.

## Quick Start

```bash
# 1. Start Jenkins
make up

# 2. Access Jenkins
open http://localhost:8080

# 3. Get initial password
docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# 4. Run setup script
bash scripts/setup-jenkins.sh
```

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Pipeline Configuration](#pipeline-configuration)
- [Running Scans](#running-scans)
- [Scheduled Scans](#scheduled-scans)
- [Integration with Git](#integration-with-git)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker and Docker Compose installed
- Jenkins 2.400+ running
- Python 3.9+ available on Jenkins agents
- Docker available on Jenkins agents
- Git configured

---

## Initial Setup

### 1. Start Jenkins

```bash
# Using Docker Compose
docker-compose up -d jenkins

# Or using Make
make up
```

### 2. Complete Jenkins Setup Wizard

1. Access Jenkins at http://localhost:8080
2. Get initial admin password:
   ```bash
   docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
   ```
3. Install suggested plugins
4. Create admin user
5. Configure Jenkins URL

### 3. Install Required Plugins

Navigate to **Manage Jenkins** > **Manage Plugins** > **Available**

Install these plugins:
- Pipeline
- Docker Pipeline
- Git Plugin
- GitHub Plugin
- HTML Publisher
- Email Extension
- Slack Notification (optional)
- Credentials Binding

### 4. Configure Shared Library

1. Go to **Manage Jenkins** > **Configure System**
2. Scroll to **Global Pipeline Libraries**
3. Click **Add**
4. Configure:
   - **Name:** `amtd-shared-library`
   - **Default version:** `main`
   - **Retrieval method:** Modern SCM
   - **Source Code Management:** Git
   - **Project Repository:** Your repository URL
5. Click **Save**

### 5. Add Credentials

Navigate to **Manage Jenkins** > **Manage Credentials** > **Global** > **Add Credentials**

Add the following:

#### GitHub Token (for issue creation)
- **Kind:** Secret text
- **ID:** `github-token`
- **Secret:** Your GitHub Personal Access Token
- **Description:** GitHub API Token

#### Slack Webhook (optional)
- **Kind:** Secret text
- **ID:** `slack-webhook-url`
- **Secret:** Your Slack Webhook URL
- **Description:** Slack Webhook URL

#### Docker Registry (if using private registry)
- **Kind:** Username with password
- **ID:** `docker-credentials`
- **Username:** Your username
- **Password:** Your password
- **Description:** Docker Registry Credentials

---

## Pipeline Configuration

### Option 1: Using Main Jenkinsfile

Create a new Pipeline job:

1. Click **New Item**
2. Enter name: `amtd-scan`
3. Select **Pipeline**
4. Click **OK**
5. Under **Pipeline**, select **Pipeline script from SCM**
6. Configure:
   - **SCM:** Git
   - **Repository URL:** Your repository URL
   - **Script Path:** `Jenkinsfile`
7. Click **Save**

### Option 2: Using Simplified Jenkinsfile

For a simpler pipeline, use `Jenkinsfile.simple`:

1. Follow steps 1-5 above
2. Set **Script Path:** `Jenkinsfile.simple`
3. Click **Save**

### Option 3: Inline Pipeline

Create a pipeline with inline script:

```groovy
@Library('amtd-shared-library') _

pipeline {
    agent any

    parameters {
        string(name: 'APPLICATION', defaultValue: 'juice-shop')
        choice(name: 'SCAN_TYPE', choices: ['full', 'quick', 'incremental'])
    }

    stages {
        stage('Scan') {
            steps {
                script {
                    amtdScan(
                        application: params.APPLICATION,
                        scanType: params.SCAN_TYPE
                    )
                }
            }
        }
    }
}
```

---

## Running Scans

### Manual Scan via Jenkins UI

1. Navigate to your pipeline job
2. Click **Build with Parameters**
3. Configure parameters:
   - **APPLICATION:** Application name (e.g., `juice-shop`)
   - **SCAN_TYPE:** Choose scan type
   - **ENVIRONMENT:** Select environment
4. Click **Build**

### Scan via Jenkins CLI

```bash
# Download Jenkins CLI
wget http://localhost:8080/jnlpJars/jenkins-cli.jar

# Trigger scan
java -jar jenkins-cli.jar -s http://localhost:8080 -auth admin:password \\
    build amtd-scan \\
    -p APPLICATION=juice-shop \\
    -p SCAN_TYPE=full
```

### Scan via API

```bash
# Using curl
curl -X POST "http://localhost:8080/job/amtd-scan/buildWithParameters" \\
    --user "admin:password" \\
    --data "APPLICATION=juice-shop" \\
    --data "SCAN_TYPE=full"
```

---

## Scheduled Scans

### Option 1: Using Jenkins Triggers

Add to your Jenkinsfile:

```groovy
pipeline {
    agent any

    triggers {
        cron('H 2 * * *')  // Run daily at 2 AM
    }

    // ... rest of pipeline
}
```

### Option 2: Multi-Application Scan

Create a pipeline to scan multiple applications:

```groovy
@Library('amtd-shared-library') _

pipeline {
    agent any

    triggers {
        cron('H 2 * * 1-5')  // Weekdays at 2 AM
    }

    stages {
        stage('Nightly Scans') {
            steps {
                script {
                    def applications = [
                        'juice-shop',
                        'my-app-1',
                        'my-app-2'
                    ]

                    applications.each { app ->
                        stage("Scan ${app}") {
                            try {
                                amtdScan(
                                    application: app,
                                    scanType: 'full',
                                    notifications: true
                                )
                            } catch (Exception e) {
                                echo "Scan failed for ${app}: ${e.message}"
                            }
                        }
                    }
                }
            }
        }
    }
}
```

---

## Integration with Git

### Trigger on Git Push

Configure webhook in your Git repository:

1. Go to repository settings
2. Add webhook:
   - **URL:** `http://jenkins-url:8080/github-webhook/`
   - **Content type:** `application/json`
   - **Events:** Push events
3. Save webhook

Add to Jenkinsfile:

```groovy
pipeline {
    agent any

    triggers {
        githubPush()  // Trigger on push
    }

    stages {
        stage('Scan on Push') {
            steps {
                script {
                    amtdScan(
                        application: env.GIT_BRANCH,  // Use branch name
                        scanType: 'quick'             // Use quick scan
                    )
                }
            }
        }
    }
}
```

### Scan on Pull Requests

```groovy
pipeline {
    agent any

    stages {
        stage('PR Security Scan') {
            when {
                changeRequest()  // Only for PRs
            }
            steps {
                script {
                    def results = amtdScan(
                        application: env.CHANGE_TARGET,
                        scanType: 'quick',
                        notifications: false
                    )

                    // Comment on PR
                    if (env.CHANGE_ID) {
                        def stats = results.statistics
                        def comment = """
                        ## AMTD Security Scan Results

                        | Severity | Count |
                        |----------|-------|
                        | Critical | ${stats.critical} |
                        | High | ${stats.high} |
                        | Medium | ${stats.medium} |

                        [View Full Report](${env.BUILD_URL})
                        """

                        // Post comment to PR
                        // (requires GitHub plugin configuration)
                    }
                }
            }
        }
    }
}
```

---

## Viewing Results

### HTML Report

After scan completion:

1. Go to build page
2. Click **Security Scan Report** in left menu
3. View interactive HTML report

### JSON Results

Download JSON report:

```bash
# Via browser
http://localhost:8080/job/amtd-scan/lastBuild/artifact/reports/latest/report.json

# Via curl
curl -o report.json \\
    http://localhost:8080/job/amtd-scan/lastBuild/artifact/reports/latest/report.json
```

### Build Status Badge

Add to README.md:

```markdown
[![Security Scan](http://jenkins:8080/buildStatus/icon?job=amtd-scan)](http://jenkins:8080/job/amtd-scan/)
```

---

## Troubleshooting

### Pipeline Not Found

**Error:** `Library 'amtd-shared-library' not found`

**Solution:**
1. Verify shared library is configured
2. Check repository URL and credentials
3. Ensure `vars/` directory exists
4. Restart Jenkins

### Docker Not Available

**Error:** `docker: command not found`

**Solution:**
1. Install Docker on Jenkins agent
2. Add Jenkins user to docker group:
   ```bash
   sudo usermod -aG docker jenkins
   ```
3. Restart Jenkins

### Python Script Fails

**Error:** `python3: command not found`

**Solution:**
1. Install Python on Jenkins agent
2. Install required packages:
   ```bash
   pip3 install -r requirements.txt
   ```

### Target Not Accessible

**Error:** `Unable to reach target URL`

**Solution:**
1. Verify target application is running
2. Check network connectivity from Jenkins
3. Ensure firewall allows connections
4. Use Docker network if target is in Docker

### Scan Timeout

**Error:** `Scan exceeded timeout`

**Solution:**
1. Increase timeout in Jenkinsfile:
   ```groovy
   timeout(time: 4, unit: 'HOURS')
   ```
2. Use `quick` scan type for faster results
3. Reduce scan depth in application config

---

## Best Practices

1. **Use Parameters:** Make pipelines configurable
2. **Archive Reports:** Always archive scan results
3. **Set Timeouts:** Prevent hanging pipelines
4. **Clean Workspace:** Clean up after scans
5. **Parallel Scans:** Use parallel stages for efficiency
6. **Notifications:** Send alerts on failures
7. **Thresholds:** Define clear vulnerability limits
8. **Credentials:** Never hardcode secrets
9. **Logging:** Enable verbose logging for debugging
10. **Testing:** Test pipeline changes in development first

---

## Example Pipelines

See `examples/` directory for:
- Basic scan pipeline
- Multi-application pipeline
- PR scanning pipeline
- Scheduled scanning pipeline
- Parallel scanning pipeline

---

## Support

- **Documentation:** `docs/`
- **Issues:** GitHub Issues
- **Email:** support@example.com

---

**Last Updated:** December 2025
