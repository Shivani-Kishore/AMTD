# AMTD - Automated Malware Target Detection

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](CHANGELOG.md)

> Enterprise-grade security automation platform for continuous vulnerability detection in web applications

##  Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Documentation](#documentation)
- [Development](#development)
- [License](#license)

---

##  Overview

AMTD is a comprehensive security automation pipeline that integrates OWASP ZAP with Jenkins CI/CD for continuous vulnerability scanning of web applications. Built for DevSecOps teams, it shifts security left in the development lifecycle.

### Why AMTD?

- **Automated Security** - Schedule scans or trigger on every commit
- **CI/CD Native** - Seamless Jenkins integration
- **Comprehensive** - Powered by OWASP ZAP
- **Rich Reporting** - HTML, JSON, PDF reports
- **Scalable** - Docker-based, concurrent scans
- **Enterprise Ready** - RBAC, SSO, compliance reporting

---

##  Features

### Core Capabilities

- **Automated Vulnerability Scanning**
  - OWASP Top 10 detection
  - SQL Injection, XSS, CSRF detection
  - Authentication/Authorization testing

- **CI/CD Integration**
  - Jenkins declarative pipeline support
  - Git webhook triggers
  - Build pass/fail based on thresholds

- **Advanced Reporting**
  - HTML reports with visual charts
  - JSON output for automation
  - PDF reports for executives

- **Notification System**
  - Email alerts
  - Slack/Teams integration
  - GitHub Issue creation

- **Enterprise Features**
  - Role-based access control (RBAC)
  - SSO integration (LDAP/SAML)
  - Compliance reporting (PCI-DSS, HIPAA, SOC 2)
  - Audit trails and logging

---

##  Architecture

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

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

##  Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8-16 GB |
| **Storage** | 50 GB | 250+ GB |

### Software Requirements

- **Docker** 20.10+
- **Docker Compose** 1.29+
- **Git** 2.30+
- **Python** 3.9+ (for scripts)
- **Make** (optional, for convenience commands)

---

##  Installation

### Option 1: Quick Start (Recommended)

```bash
# Clone and setup
git clone https://github.com/your-org/amtd.git
cd amtd
make quick-start

# Wait for services to start (30-60 seconds)
# Access Jenkins at http://localhost:8080
```

### Option 2: Manual Setup

```bash
# 1. Clone repository
git clone https://github.com/your-org/amtd.git
cd amtd

# 2. Create environment file
cp .env.example .env
# Edit .env with your configurations

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Start services
docker-compose up -d

# 5. Initialize database
make db-init

# 6. Verify services
make health
```

### Post-Installation

1. Access Jenkins: [http://localhost:8080](http://localhost:8080)
2. Initial password: `docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
3. Complete Jenkins setup wizard
4. Configure your first application scan

---

##  Usage

### Running Scans

#### Manual Scan via CLI

```bash
# Scan OWASP Juice Shop (test application)
make scan-juice-shop

# Scan specific application
make scan APP=my-application

# Using Python script directly
python scripts/scan-executor.py --application juice-shop --scan-type full
```

#### Automated Scan via Git Commit

Configure a webhook in your application's Git repository to trigger scans on commits.

#### Scheduled Scans

Configure in `config/applications/your-app.yaml`:

```yaml
scan:
  schedule: "0 2 * * *"  # Daily at 2 AM
```

### Viewing Results

#### Jenkins UI

1. Navigate to Jenkins dashboard
2. Click on your scan job
3. View "ZAP Security Report"

#### Command Line

```bash
# List all reports
make reports

# Open latest report
make view-latest-report

# View JSON report
cat reports/latest/report.json | jq '.vulnerabilities[]'
```

### Common Commands

```bash
# Service management
make up              # Start all services
make down            # Stop all services
make restart         # Restart services
make logs            # View logs

# Database operations
make db-backup       # Backup database
make db-restore      # Restore database
make shell-db        # Open database shell

# Development
make test            # Run tests
make lint            # Run linters
make format          # Format code

# Monitoring
make health          # Check service health
make metrics         # Show system metrics

# Help
make help            # Show all available commands
```

---

##  Configuration

### Application Configuration

Create a YAML file in `config/applications/`:

```yaml
application:
  name: "My Web Application"
  url: "https://app.example.com"
  owner: "security-team@example.com"

  scan:
    schedule: "0 2 * * *"
    type: full

    thresholds:
      critical: 0
      high: 5
      medium: 20

  notifications:
    email:
      - security-team@example.com
    slack:
      enabled: true
      channel: "#security-alerts"
```

### Scan Policies

Pre-configured policies in `config/scan-policies/`:

- **default.yaml** - Balanced scan for most applications
- **quick.yaml** - Fast scan for CI/CD pipelines
- **passive-only.yaml** - Non-intrusive scanning

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DB_PASSWORD=your_secure_password

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_password

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# GitHub (optional)
GITHUB_TOKEN=ghp_your_token
```

For complete configuration reference, see [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md).

---

##  Documentation

### Core Documentation

- [**Architecture**](docs/ARCHITECTURE.md) - System design and components
- [**API Reference**](docs/API_REFERENCE.md) - REST API documentation
- [**Configuration Guide**](docs/CONFIGURATION_GUIDE.md) - Configuration options
- [**Deployment Guide**](docs/DEPLOYMENT_GUIDE.md) - Deployment instructions
- [**Testing Guide**](docs/TESTING_GUIDE.md) - Testing strategies
- [**Security**](docs/SECURITY.md) - Security considerations
- [**PRD**](docs/AMTD_PRD.md) - Product requirements

### Additional Resources

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

##  Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt

# Start development services
make dev

# Run tests
make test

# Run linters
make lint

# Format code
make format
```

### Project Structure

```
amtd/
├── config/              # Configuration files
│   ├── applications/    # Application configs
│   ├── scan-policies/   # Scan policy configs
│   └── global.yaml      # Global configuration
├── src/                 # Source code
│   ├── api/             # REST API
│   ├── scan_manager/    # Scan management
│   ├── report_generator/# Report generation
│   ├── config_manager/  # Configuration management
│   └── notification_service/ # Notifications
├── scripts/             # Utility scripts
├── tests/               # Test suite
├── docs/                # Documentation
├── Jenkinsfile          # Jenkins pipeline
└── docker-compose.yml   # Docker services
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# With coverage report
make test-coverage
```

### Code Quality

```bash
# Run linters
make lint

# Format code
make format

# Type checking
make type-check
```

---

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `make test`
5. Commit: `git commit -m "Add amazing feature"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request


##  Security

### Reporting Vulnerabilities

If you discover a security vulnerability, please email: security@example.com

**Do not** open public GitHub issues for security vulnerabilities.

### Security Features

- TLS 1.3 for all communications
- AES-256 encryption for secrets
- RBAC and SSO support
- Audit logging
- Container isolation

---

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

##  Acknowledgments

- **OWASP ZAP** - For the security scanning engine
- **Jenkins** - For the CI/CD platform
- **Docker** - For containerization

---


[⬆ Back to Top](#amtd---automated-malware-target-detection)
