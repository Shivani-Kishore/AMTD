# AMTD Development Setup Guide

**Version:** 1.0  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Setup](#local-development-setup)
- [IDE Configuration](#ide-configuration)
- [Running Tests](#running-tests)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Debugging](#debugging)
- [Contributing](#contributing)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Git** | 2.30+ | Version control |
| **Docker** | 20.10+ | Containerization |
| **Docker Compose** | 1.29+ | Multi-container orchestration |
| **Python** | 3.9+ | Scripts and automation |
| **Node.js** | 16+ | Dashboard (if developing UI) |
| **Java** | 11+ | Jenkins plugins |
| **Make** | 4.0+ | Build automation |

### Optional Tools

- **VS Code** or **IntelliJ IDEA** - IDE
- **Postman** - API testing
- **DBeaver** - Database management
- **k9s** - Kubernetes management (if using K8s)

---

## Local Development Setup

### 1. Clone Repository

```bash
# Clone the repo
git clone https://github.com/your-org/amtd.git
cd amtd

# Create development branch
git checkout -b feature/your-feature-name
```

### 2. Environment Setup

```bash
# Copy environment template
cp .env.example .env.development

# Edit with your settings
nano .env.development
```

**.env.development:**
```bash
# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=amtd_dev
DB_USER=amtd_dev
DB_PASSWORD=dev_password

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=amtd-dev

# Jenkins
JENKINS_URL=http://localhost:8080
JENKINS_USER=admin
JENKINS_TOKEN=your_dev_token

# Scan limits (reduced for dev)
SCAN_CONCURRENT_LIMIT=2
```

### 3. Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 5. Initialize Database

```bash
# Run migrations
python scripts/init-db.py

# Load test data
python scripts/load-test-data.py
```

### 6. Configure Jenkins

```bash
# Get initial password
docker exec amtd-jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Access Jenkins
open http://localhost:8080

# Install required plugins (automated)
python scripts/setup-jenkins.py
```

### 7. Verify Setup

```bash
# Run health checks
make health-check

# Run a test scan
make test-scan
```

---

## IDE Configuration

### VS Code

**Install Extensions:**
- Python (Microsoft)
- Docker (Microsoft)
- YAML (Red Hat)
- GitLens
- Markdown All in One
- Jenkins Pipeline Linter

**Settings (.vscode/settings.json):**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "[python]": {
    "editor.formatOnSave": true,
    "editor.rulers": [88]
  },
  "[yaml]": {
    "editor.defaultFormatter": "redhat.vscode-yaml"
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true
  }
}
```

### IntelliJ IDEA / PyCharm

1. Import project as Python project
2. Configure Python interpreter (use venv)
3. Install plugins:
   - Docker
   - Jenkins Control
   - YAML/Ansible support
4. Set code style to PEP 8

---

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scan_manager.py

# Run with coverage
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Integration Tests

```bash
# Run integration tests (requires running services)
pytest tests/integration/

# Run with markers
pytest -m integration
pytest -m "not slow"
```

### End-to-End Tests

```bash
# Run full pipeline test
make test-e2e

# Or manually
python tests/e2e/test_full_pipeline.py
```

### Linting

```bash
# Python linting
flake8 src/
pylint src/

# YAML linting
yamllint config/

# Shell script linting
shellcheck scripts/*.sh

# Fix auto-fixable issues
black src/
isort src/
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/scan-optimization
```

### 2. Make Changes

```bash
# Edit files
# Add tests
# Update documentation
```

### 3. Run Tests Locally

```bash
# Run tests
pytest

# Run linters
make lint

# Check code style
make format-check
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "feat: optimize scan performance

- Reduce memory usage by 30%
- Improve scan speed for large apps
- Add caching for repeated requests

Closes #123"
```

### 5. Push and Create PR

```bash
# Push to remote
git push origin feature/scan-optimization

# Create PR on GitHub
# - Fill in PR template
# - Link related issues
# - Request reviews
```

### 6. Address Review Comments

```bash
# Make changes
# Commit fixes
git commit -m "fix: address review comments"

# Push updates
git push origin feature/scan-optimization
```

---

## Code Style Guidelines

### Python

**Follow PEP 8:**
```python
# Good
def scan_application(app_id: str, scan_type: str = "full") -> dict:
    """
    Scan an application for vulnerabilities.
    
    Args:
        app_id: Application identifier
        scan_type: Type of scan (full, quick, incremental)
        
    Returns:
        Dictionary with scan results
    """
    logger.info(f"Starting {scan_type} scan for app {app_id}")
    return {"status": "completed"}

# Use type hints
# Use docstrings
# Clear variable names
# Max line length: 88 (Black default)
```

### Groovy (Jenkins Pipelines)

```groovy
// Use declarative pipeline when possible
pipeline {
    agent any
    
    stages {
        stage('Scan') {
            steps {
                script {
                    // Clear comments
                    // Descriptive variable names
                    def scanResult = triggerScan(params.TARGET_URL)
                    
                    if (scanResult.vulnerabilities.critical > 0) {
                        error "Critical vulnerabilities found"
                    }
                }
            }
        }
    }
}
```

### YAML Configuration

```yaml
# Use consistent indentation (2 spaces)
# Add comments for non-obvious settings
application:
  name: "My App"
  url: "https://example.com"
  
  # Scan configuration
  scan:
    # Daily at 2 AM UTC
    schedule: "0 2 * * *"
    type: full
```

### Shell Scripts

```bash
#!/bin/bash
# Use bash strict mode
set -euo pipefail

# Add script description
# Usage: ./script.sh <arg1> <arg2>

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <arg1> <arg2>"
    exit 1
fi

# Use meaningful variable names
readonly TARGET_URL="$1"
readonly SCAN_TYPE="$2"

# Add error handling
scan_application() {
    if ! zap-cli scan "$TARGET_URL"; then
        echo "Error: Scan failed" >&2
        return 1
    fi
}
```

---

## Debugging

### Debugging Python Scripts

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pdb for debugging
import pdb; pdb.set_trace()

# Or use ipdb (better interface)
import ipdb; ipdb.set_trace()
```

**VS Code Launch Configuration (.vscode/launch.json):**
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "env": {
        "DEBUG": "true",
        "LOG_LEVEL": "debug"
      }
    },
    {
      "name": "Python: Scan Script",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/scripts/scan-executor.py",
      "args": ["--target", "http://localhost:3000"],
      "console": "integratedTerminal"
    }
  ]
}
```

### Debugging Jenkins Pipeline

```groovy
// Add debug output
echo "DEBUG: Variable value = ${myVariable}"

// Use try-catch
try {
    scanApplication()
} catch (Exception e) {
    echo "Error: ${e.getMessage()}"
    echo "Stack trace: ${e.getStackTrace()}"
    throw e
}
```

### Debugging Docker Containers

```bash
# View logs
docker logs amtd-jenkins -f

# Enter container
docker exec -it amtd-jenkins bash

# Check container resource usage
docker stats

# Inspect container
docker inspect amtd-jenkins
```

### Debugging Database Issues

```bash
# Connect to database
docker exec -it amtd-postgres psql -U amtd

# View tables
\dt

# Query data
SELECT * FROM scans ORDER BY created_at DESC LIMIT 10;

# Check connections
SELECT * FROM pg_stat_activity;
```

---

## Contributing

### Development Checklist

Before submitting a PR:

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Linters passing
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Commit messages follow convention
- [ ] PR description complete

### Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(scan): add incremental scanning support

Implement incremental scanning to reduce scan time for 
large applications by only scanning changed pages.

Closes #456

fix(report): correct CVSS score calculation

The CVSS score was being calculated incorrectly for
vulnerabilities with modified attack vector.

Fixes #789
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] CHANGELOG updated
```

---

## Useful Commands

### Makefile Targets

```bash
# Setup
make setup                 # Initial setup
make install              # Install dependencies

# Development
make dev                  # Start dev environment
make dev-down            # Stop dev environment
make logs                # View logs

# Testing
make test                # Run all tests
make test-unit           # Unit tests only
make test-integration    # Integration tests
make test-e2e            # End-to-end tests
make coverage            # Generate coverage report

# Code Quality
make lint                # Run all linters
make format              # Format code
make type-check          # Run type checker

# Database
make db-migrate          # Run migrations
make db-reset            # Reset database
make db-seed             # Load test data

# Utilities
make clean               # Clean temporary files
make health-check        # Check system health
make test-scan           # Run test scan
```

### Quick Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Run specific test
pytest tests/test_file.py::test_function

# Format Python code
black src/
isort src/

# Check types
mypy src/

# Generate requirements
pip freeze > requirements.txt

# Update dependencies
pip install --upgrade -r requirements.txt

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

---

## Troubleshooting Development Issues

### Port Already in Use

```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port
export JENKINS_PORT=8081
```

### Docker Issues

```bash
# Clean up Docker
docker system prune -a

# Reset Docker volumes
docker-compose down -v
docker-compose up -d
```

### Database Connection Issues

```bash
# Reset database
make db-reset

# Check database logs
docker logs amtd-postgres
```

### Import Errors

```bash
# Reinstall in development mode
pip install -e .

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
```

---

## Resources

### Documentation
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Jenkins Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [OWASP ZAP API](https://www.zaproxy.org/docs/api/)

### Tools
- [Black - Code Formatter](https://black.readthedocs.io/)
- [Pytest - Testing Framework](https://docs.pytest.org/)
- [Pre-commit - Git Hooks](https://pre-commit.com/)

---

**Document Version:** 1.0  
**Last Updated:** November 26, 2025
