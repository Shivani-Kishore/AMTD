# AMTD - Automated Malware Target Detection

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://jenkins.example.com/job/amtd)

> Enterprise-grade security automation platform for continuous vulnerability detection in web applications

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

---

## 🌟 Overview

AMTD (Automated Malware Target Detection) is a comprehensive security automation pipeline designed to scan, detect, and report potential vulnerabilities and malware behavior in web applications. Built for DevSecOps teams, it seamlessly integrates with CI/CD workflows to shift security left in the development lifecycle.

### Why AMTD?

- **Automated Security:** Schedule vulnerability scans or trigger them on every commit
- **CI/CD Native:** Seamless Jenkins integration with pipeline-as-code
- **Comprehensive Scanning:** Powered by OWASP ZAP for industry-standard detection
- **Rich Reporting:** HTML, JSON, and PDF reports with actionable insights
- **Scalable Architecture:** Docker-based isolation with concurrent scan support
- **Enterprise Ready:** RBAC, SSO, compliance reporting, and audit trails

### Key Use Cases

- **DevSecOps Integration:** Automate security testing in CI/CD pipelines
- **Continuous Monitoring:** Schedule regular scans for production applications
- **Compliance:** Generate reports for PCI-DSS, SOC 2, HIPAA requirements
- **Red Team Operations:** Identify vulnerabilities before attackers do
- **Security Posture Management:** Track vulnerabilities across application portfolio

---

## Features

### Core Capabilities

- **Automated Vulnerability Scanning**
  - OWASP Top 10 detection
  - SQL Injection, XSS, CSRF detection
  - Authentication/Authorization testing
  - Security misconfiguration detection

- **CI/CD Integration**
  - Jenkins declarative pipeline support
  - Git webhook triggers
  - Build pass/fail based on thresholds
  - Scheduled scans with cron syntax

- **Advanced Reporting**
  - HTML reports with visual charts
  - JSON output for automation
  - PDF reports for executives
  - Trend analysis and metrics

- **Notification System**
  - Email alerts on scan completion
  - Slack/Teams integration
  - GitHub Issue creation
  - Pull Request comments

- **Enterprise Features**
  - Role-based access control (RBAC)
  - SSO integration (LDAP/SAML)
  - Compliance reporting
  - Audit trails and logging

### Scanning Features

| Feature | Description |
|---------|-------------|
| **Active Scanning** | Aggressive vulnerability detection with attack payloads |
| **Passive Scanning** | Non-intrusive analysis of application responses |
| **Spider** | Intelligent web crawling to discover all endpoints |
| **AJAX Spider** | JavaScript-heavy application support |
| **Authentication** | Scan authenticated sections (Forms, OAuth, API keys) |
| **Custom Policies** | Define scan depth, rules, and exclusions |
| **Incremental Scans** | Delta scanning for faster results |
| **Concurrent Execution** | Run multiple scans in parallel |

---

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Jenkins 2.400+
- Git
- 4GB RAM minimum (8GB recommended)

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/amtd.git
cd amtd

# 2. Start the infrastructure
docker-compose up -d

# 3. Access Jenkins
open http://localhost:8080

# 4. Run your first scan
# Create a new pipeline job and point to Jenkinsfile

# 5. View results
# Reports will be available in Jenkins UI and archived in reports/
```

### First Scan Example

```yaml
# config/applications/juice-shop.yaml
application:
  name: "OWASP Juice Shop"
  url: "http://juice-shop:3000"
  scan:
    schedule: "0 2 * * *"  # Daily at 2 AM
    type: full
```

```bash
# Trigger scan manually
jenkins-cli build amtd-scan -p TARGET=juice-shop

# Or via Jenkins UI
# Navigate to: Jenkins > AMTD > Build with Parameters
```

---

## 🏗️ Architecture

AMTD follows a modular, microservices-inspired architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Jenkins UI / Dashboard)                    │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                  Pipeline Orchestrator                   │
│         (Jenkinsfile + Groovy Shared Library)           │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌─────▼──────┐ ┌───────▼────────┐
│ Scan Manager   │ │  Report    │ │  Notification  │
│  (ZAP Docker)  │ │ Generator  │ │    Service     │
└────────────────┘ └────────────┘ └────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                      Data Layer                          │
│         (PostgreSQL / MinIO / File Storage)             │
└─────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📦 Requirements

### System Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 2 cores | 4+ cores | More cores = more concurrent scans |
| **RAM** | 4 GB | 8-16 GB | Each scan uses ~2GB |
| **Storage** | 50 GB | 250+ GB | For reports and logs |
| **Network** | 10 Mbps | 100 Mbps | For target application access |

### Software Requirements

- **Docker:** 20.10 or later
- **Docker Compose:** 1.29 or later
- **Jenkins:** 2.400 or later
- **Git:** 2.30 or later
- **Python:** 3.9+ (for scripts)
- **Bash:** 4.0+ (for automation scripts)

### Jenkins Plugins

The following Jenkins plugins are required:

- Pipeline: Declarative (2.2143+)
- Docker Pipeline (572.v950f58993843)
- HTML Publisher (1.31)
- Email Extension (2.96)
- Git Plugin (5.0.0)
- GitHub Plugin (1.37.0)
- Credentials Binding (523.vd859a_4b_122e6)

### Network Requirements

- Outbound HTTPS (443) to Docker Hub
- Access to target applications (HTTP/HTTPS)
- SMTP access for email notifications (optional)
- GitHub API access (optional, for integrations)

---

## 💾 Installation

### Option 1: Docker Compose (Recommended for Dev/Test)

```bash
# Clone repository
git clone https://github.com/your-org/amtd.git
cd amtd

# Create environment file
cp .env.example .env
# Edit .env with your configurations

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Access Jenkins
open http://localhost:8080

# Initial Jenkins password
docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### Option 2: Manual Installation

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Install Jenkins
# Follow: https://www.jenkins.io/doc/book/installing/

# 3. Configure Jenkins
# Install required plugins
# Set up credentials
# Create pipeline job

# 4. Clone AMTD repository
git clone https://github.com/your-org/amtd.git

# 5. Configure scan targets
cp config/applications/example.yaml config/applications/my-app.yaml
# Edit my-app.yaml
```

### Option 3: Kubernetes Deployment

```bash
# See DEPLOYMENT_GUIDE.md for Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/jenkins/
kubectl apply -f k8s/postgresql/
kubectl apply -f k8s/minio/

# Verify deployment
kubectl get pods -n amtd
```

### Post-Installation Setup

1. **Configure Jenkins:**
   ```bash
   # Add Docker credentials
   # Set up GitHub webhook
   # Configure email notifications
   ```

2. **Create First Pipeline:**
   ```bash
   # Jenkins > New Item > Pipeline
   # Point to: https://github.com/your-org/amtd
   # Pipeline script from SCM
   ```

3. **Configure Target Application:**
   ```bash
   # Edit config/applications/your-app.yaml
   # Commit and push to trigger scan
   ```

---

## 🎯 Usage

### Running Scans

#### Manual Scan via Jenkins UI

1. Navigate to Jenkins dashboard
2. Click on "AMTD Scan Pipeline"
3. Click "Build with Parameters"
4. Configure:
   - **Target URL:** `http://your-app.example.com`
   - **Scan Type:** `full`, `quick`, or `incremental`
   - **Send Notifications:** Check to enable alerts
5. Click "Build"

#### Automated Scan via Git Commit

```bash
# Any commit to configured applications triggers scan
git commit -m "Update feature X"
git push origin main
# Scan automatically triggered
```

#### Scheduled Scans

Configure in `config/applications/your-app.yaml`:

```yaml
scan:
  schedule: "0 2 * * *"  # Daily at 2 AM
```

#### API-Triggered Scan

```bash
# Using Jenkins CLI
java -jar jenkins-cli.jar -s http://jenkins:8080 \
  build amtd-scan \
  -p TARGET_URL=http://example.com \
  -p SCAN_TYPE=full

# Using curl
curl -X POST http://jenkins:8080/job/amtd-scan/buildWithParameters \
  --user user:token \
  --data TARGET_URL=http://example.com \
  --data SCAN_TYPE=full
```

### Viewing Results

#### Jenkins UI

1. Go to scan build page
2. Click "ZAP Security Report" in left menu
3. Browse interactive HTML report

#### Command Line

```bash
# View latest report
cat reports/latest/report.json | jq '.vulnerabilities[] | select(.severity=="High")'

# List all reports
ls -lh reports/

# Archive reports
tar -czf reports-backup.tar.gz reports/
```

#### Dashboard (if deployed)

```bash
# Access web dashboard
open http://dashboard.amtd.example.com

# View metrics
# - Total scans
# - Vulnerability trends
# - Application portfolio
```

### Common Workflows

#### Workflow 1: New Application Onboarding

```bash
# 1. Create configuration
cp config/applications/template.yaml config/applications/new-app.yaml

# 2. Edit configuration
vim config/applications/new-app.yaml

# 3. Commit configuration
git add config/applications/new-app.yaml
git commit -m "Add new-app scanning"
git push

# 4. Trigger initial scan
# Via Jenkins UI or wait for schedule
```

#### Workflow 2: Vulnerability Triage

```bash
# 1. Review scan report in Jenkins

# 2. Export vulnerabilities
curl http://jenkins:8080/job/amtd-scan/lastBuild/artifact/reports/report.json \
  > vulnerabilities.json

# 3. Filter critical issues
jq '.vulnerabilities[] | select(.severity=="Critical")' vulnerabilities.json

# 4. Create GitHub issues (if enabled)
# Issues automatically created for Critical/High findings

# 5. Track remediation in issue tracker
```

#### Workflow 3: Compliance Reporting

```bash
# Generate monthly report
python scripts/generate-compliance-report.py \
  --start-date 2025-11-01 \
  --end-date 2025-11-30 \
  --format pdf \
  --output compliance-report-nov-2025.pdf

# Review report
open compliance-report-nov-2025.pdf
```

---

## Configuration

### Application Configuration

Basic configuration in `config/applications/your-app.yaml`:

```yaml
application:
  name: "My Web Application"
  url: "https://app.example.com"
  owner: "security-team@example.com"
  
  scan:
    schedule: "0 2 * * *"
    type: full
    timeout: 7200
    
    thresholds:
      critical: 0  # Fail build if any critical found
      high: 5      # Fail if more than 5 high severity
      medium: 20   # Fail if more than 20 medium
```

### Advanced Configuration

For authentication, custom headers, exclusions:

```yaml
scan:
  authentication:
    type: "form"
    login_url: "https://app.example.com/login"
    username_field: "email"
    password_field: "password"
    credentials:
      username: "${SCAN_USERNAME}"
      password: "${SCAN_PASSWORD}"
      
  custom_headers:
    User-Agent: "AMTD Security Scanner"
    
  exclusions:
    - "/admin/.*"
    - ".*\\.pdf$"
```

For complete configuration reference, see [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md).

### Environment Variables

```bash
# .env file
JENKINS_ADMIN_USER=admin
JENKINS_ADMIN_PASSWORD=changeme
DB_PASSWORD=secure_password
MINIO_PASSWORD=secure_password
SMTP_HOST=smtp.example.com
SMTP_USER=notifications@example.com
SMTP_PASSWORD=smtp_password
```

---

## 📚 Documentation

### Core Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[API_REFERENCE.md](API_REFERENCE.md)** - REST API documentation
- **[CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)** - Configuration options
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment instructions
- **[DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md)** - Developer setup guide
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing strategies
- **[SECURITY.md](SECURITY.md)** - Security considerations

### Additional Resources

- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[FAQ.md](FAQ.md)** - Frequently asked questions
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues

### External Links

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Contribution Guide

```bash
# 1. Fork the repository
# 2. Create feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and commit
git commit -m "Add amazing feature"

# 4. Push to branch
git push origin feature/amazing-feature

# 5. Open Pull Request
```

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/amtd.git
cd amtd

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linters
flake8 src/
pylint src/
```

### Code Style

- Python: PEP 8
- Shell scripts: ShellCheck compliant
- Groovy: Jenkins Pipeline conventions
- Documentation: Markdown with consistent formatting

---

## 📊 Project Status

### Current Version: 1.0.0

**Status:** Production Ready 

### Recent Updates

- Core scanning engine implemented
- Jenkins pipeline integration complete
- HTML/JSON/PDF reporting
- Email notifications
- GitHub integration
- 🚧 Dashboard UI (in progress)
- 🚧 Slack/Teams integration (in progress)
- 📋 ML-based false positive reduction (planned)

### Roadmap

**Q1 2026:**
- Web dashboard with analytics
- Slack/Teams integration
- Enhanced authentication support

**Q2 2026:**
- Machine learning for false positive reduction
- Multi-scanner support (beyond ZAP)
- Advanced compliance reporting

**Q3 2026:**
- SaaS offering
- Mobile app for notifications
- Integration marketplace

---

## 🔒 Security

### Reporting Vulnerabilities

If you discover a security vulnerability, please email: security@example.com

**Do not** open public GitHub issues for security vulnerabilities.

### Security Features

- TLS 1.3 for all communications
- AES-256 encryption for secrets
- RBAC and SSO support
- Audit logging
- Container isolation
- Rate limiting

For detailed security documentation, see [SECURITY.md](SECURITY.md).

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Your Organization

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

[Full license text...]
```

---

## 💬 Support

### Getting Help

- **Documentation:** Start with [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/your-org/amtd/issues)
- **Discussions:** [GitHub Discussions](https://github.com/your-org/amtd/discussions)
- **Email:** support@example.com

### Community

- **Slack:** [Join our Slack](https://slack.amtd.example.com)
- **Twitter:** [@amtd_security](https://twitter.com/amtd_security)
- **Blog:** [blog.amtd.example.com](https://blog.amtd.example.com)

### Commercial Support

For enterprise support, SLA, and custom features:
- **Email:** enterprise@example.com
- **Website:** [www.amtd.example.com/enterprise](https://www.amtd.example.com/enterprise)

---

## 🙏 Acknowledgments

- **OWASP ZAP** - For the powerful security scanning engine
- **Jenkins** - For the robust CI/CD platform
- **Docker** - For containerization technology
- **Contributors** - Thank you to all our contributors!

---

## 📞 Contact

**Project Maintainers:**
- Lead: John Doe (john.doe@example.com)
- DevOps: Jane Smith (jane.smith@example.com)
- Security: Bob Johnson (bob.johnson@example.com)

**Organization:**
- Website: https://www.example.com
- GitHub: https://github.com/your-org
- Email: contact@example.com

---

## Star History

If you find AMTD useful, please consider giving it a star on GitHub!

[![Star History](https://img.shields.io/github/stars/your-org/amtd?style=social)](https://github.com/your-org/amtd)

---

**Made by the AMTD Team**

[⬆ Back to Top](#amtd---automated-malware-target-detection)
