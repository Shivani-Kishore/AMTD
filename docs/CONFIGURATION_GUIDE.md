# AMTD Configuration Guide

**Version:** 1.0  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Overview](#overview)
- [Configuration Hierarchy](#configuration-hierarchy)
- [Application Configuration](#application-configuration)
- [Scan Configuration](#scan-configuration)
- [Authentication Configuration](#authentication-configuration)
- [Notification Configuration](#notification-configuration)
- [Environment Variables](#environment-variables)
- [Advanced Configuration](#advanced-configuration)
- [Configuration Examples](#configuration-examples)

---

## Overview

AMTD uses a hierarchical YAML-based configuration system that allows for flexible, environment-specific settings. Configuration files are validated on load and support variable substitution for secrets.

### Configuration Principles

1. **Convention over Configuration:** Sensible defaults for most settings
2. **Environment-Specific:** Override defaults per environment
3. **Secure by Default:** Secrets never in plain text
4. **Validation:** All configs validated against schema
5. **Documentation:** Self-documenting with inline comments

---

## Configuration Hierarchy

```
config/
├── global.yaml                  # Global defaults (lowest priority)
├── environments/
│   ├── development.yaml         # Dev environment overrides
│   ├── staging.yaml             # Staging environment overrides
│   └── production.yaml          # Production environment overrides
├── applications/
│   ├── app1.yaml                # App-specific configuration
│   ├── app2.yaml
│   └── template.yaml            # Template for new apps
├── scan-policies/
│   ├── default.yaml             # Default scan policy
│   ├── aggressive.yaml          # Aggressive scanning
│   ├── passive-only.yaml        # Passive only
│   └── quick.yaml               # Quick scan policy
├── notifications/
│   ├── email-templates/
│   ├── slack-templates/
│   └── notification-rules.yaml
└── secrets/
    └── .gitkeep                 # Secrets managed via env vars

```

### Configuration Loading Order

1. Load `global.yaml` (base configuration)
2. Load environment-specific config (e.g., `environments/production.yaml`)
3. Load application-specific config (e.g., `applications/myapp.yaml`)
4. Apply environment variable overrides
5. Validate merged configuration

**Note:** Later configs override earlier ones.

---

## Application Configuration

### Basic Application Config

**File:** `config/applications/my-app.yaml`

```yaml
# Application metadata
application:
  name: "My Web Application"
  description: "Customer-facing web application"
  url: "https://app.example.com"
  
  # Ownership information
  owner: "security-team@example.com"
  team: "Platform Engineering"
  
  # Business criticality
  criticality: high  # Options: critical, high, medium, low
  
  # Tags for organization
  tags:
    - production
    - customer-facing
    - pci-compliant
  
  # Scan configuration
  scan:
    # Schedule (cron syntax)
    schedule: "0 2 * * *"  # Daily at 2 AM
    
    # Scan type: full, quick, incremental
    type: full
    
    # Timeout in seconds (default: 7200 = 2 hours)
    timeout: 7200
    
    # Reference to scan policy
    policy: default
    
    # Vulnerability thresholds (fail build if exceeded)
    thresholds:
      critical: 0   # Zero critical vulnerabilities allowed
      high: 5       # Max 5 high severity
      medium: 20    # Max 20 medium severity
      low: null     # No limit on low severity
    
  # Notification settings
  notifications:
    email:
      - security-team@example.com
      - dev-team@example.com
    
    slack:
      enabled: true
      channel: "#security-alerts"
      webhook_url: "${SLACK_WEBHOOK_URL}"
    
    github:
      enabled: true
      create_issues: true
      issue_severity: ["critical", "high"]
      comment_on_pr: true
```

### Configuration Schema Reference

#### Application Metadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Application display name |
| `description` | string | No | Brief description |
| `url` | string | Yes | Base URL to scan |
| `owner` | string | Yes | Email of application owner |
| `team` | string | No | Team responsible for app |
| `criticality` | enum | No | Business impact level |
| `tags` | array | No | Organizational tags |

#### Scan Configuration

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `schedule` | string | No | null | Cron expression for scheduling |
| `type` | enum | No | full | Scan type (full, quick, incremental) |
| `timeout` | integer | No | 7200 | Timeout in seconds |
| `policy` | string | No | default | Scan policy name |

#### Thresholds

| Field | Type | Description |
|-------|------|-------------|
| `critical` | integer/null | Max critical vulnerabilities |
| `high` | integer/null | Max high vulnerabilities |
| `medium` | integer/null | Max medium vulnerabilities |
| `low` | integer/null | Max low vulnerabilities |

---

## Scan Configuration

### Scan Policies

Scan policies define how ZAP performs the scan.

**File:** `config/scan-policies/custom-policy.yaml`

```yaml
policy:
  name: "Custom Scan Policy"
  description: "Balanced scan for production applications"
  
  # Spider configuration
  spider:
    enabled: true
    max_depth: 5
    max_children: 10
    max_duration: 30  # minutes
    thread_count: 5
    
    # URL patterns to exclude from spidering
    excluded_patterns:
      - ".*logout.*"
      - ".*delete.*"
      - ".*admin.*"
  
  # AJAX spider for JavaScript-heavy apps
  ajax_spider:
    enabled: true
    max_duration: 15  # minutes
    max_crawl_states: 10
    browser: firefox-headless
    
  # Passive scanning
  passive_scan:
    enabled: true
    
    # Scan rules (default: all enabled)
    rules:
      - id: 10010
        enabled: true
        threshold: medium
      - id: 10015
        enabled: false  # Disable specific rule
  
  # Active scanning
  active_scan:
    enabled: true
    
    # Scan intensity: low, medium, high
    intensity: medium
    
    # Thread count for parallel requests
    thread_count: 5
    
    # Delay between requests (ms)
    delay_in_ms: 0
    
    # Active scan rules
    policy_type: default  # Options: default, sql-injection, xss
    
    # Rule threshold: off, low, medium, high
    threshold: medium
    
    # Specific rules to enable/disable
    rules:
      - name: "SQL Injection"
        enabled: true
        strength: high
      
      - name: "Cross Site Scripting"
        enabled: true
        strength: high
      
      - name: "Path Traversal"
        enabled: true
        strength: medium
  
  # Authentication (if required)
  authentication:
    enabled: false
  
  # Scope
  scope:
    # Include only URLs matching these patterns
    include_in_context:
      - "https://app.example.com/.*"
    
    # Exclude URLs matching these patterns
    exclude_from_context:
      - "https://app.example.com/logout"
      - "https://app.example.com/admin/.*"
      - ".*\\.pdf$"
      - ".*\\.jpg$"
      - ".*\\.png$"
```

### Predefined Policies

#### Default Policy
```yaml
# config/scan-policies/default.yaml
policy:
  name: "Default"
  spider:
    enabled: true
    max_depth: 5
  ajax_spider:
    enabled: true
  active_scan:
    enabled: true
    intensity: medium
  passive_scan:
    enabled: true
```

#### Quick Policy
```yaml
# config/scan-policies/quick.yaml
policy:
  name: "Quick Scan"
  spider:
    enabled: true
    max_depth: 3
    max_duration: 10
  ajax_spider:
    enabled: false
  active_scan:
    enabled: true
    intensity: low
  passive_scan:
    enabled: true
```

#### Passive Only Policy
```yaml
# config/scan-policies/passive-only.yaml
policy:
  name: "Passive Only"
  spider:
    enabled: true
    max_depth: 5
  ajax_spider:
    enabled: true
  active_scan:
    enabled: false
  passive_scan:
    enabled: true
```

---

## Authentication Configuration

### Form-Based Authentication

```yaml
authentication:
  type: form
  
  # Login URL
  login_url: "https://app.example.com/login"
  
  # Form fields
  username_field: "email"
  password_field: "password"
  
  # Credentials (use environment variables for secrets)
  credentials:
    username: "${SCAN_USERNAME}"
    password: "${SCAN_PASSWORD}"
  
  # Success indicator (text that appears after successful login)
  success_indicator: "Welcome"
  
  # Or use regex for success indicator
  success_regex: ".*Welcome.*|.*Dashboard.*"
  
  # Logged out indicator (optional)
  logged_out_indicator: "Login"
  
  # Logged out regex
  logged_out_regex: ".*Login.*|.*Sign In.*"
  
  # Additional form parameters (if needed)
  extra_parameters:
    remember_me: "true"
```

### OAuth 2.0 Authentication

```yaml
authentication:
  type: oauth2
  
  # OAuth flow: authorization_code, client_credentials, password
  flow: authorization_code
  
  # OAuth endpoints
  authorization_url: "https://auth.example.com/oauth/authorize"
  token_url: "https://auth.example.com/oauth/token"
  
  # Client credentials
  client_id: "${OAUTH_CLIENT_ID}"
  client_secret: "${OAUTH_CLIENT_SECRET}"
  
  # Scopes
  scopes:
    - read
    - write
  
  # Redirect URI (for authorization code flow)
  redirect_uri: "https://scanner.example.com/callback"
  
  # Token location in requests
  token_location: header  # Options: header, query, cookie
  token_header_name: "Authorization"
  token_prefix: "Bearer "
```

### API Key Authentication

```yaml
authentication:
  type: api_key
  
  # API key location: header, query, cookie
  location: header
  
  # Header/parameter name
  key_name: "X-API-Key"
  
  # API key value
  key_value: "${API_KEY}"
```

### Basic Authentication

```yaml
authentication:
  type: basic
  
  credentials:
    username: "${BASIC_AUTH_USERNAME}"
    password: "${BASIC_AUTH_PASSWORD}"
```

### Session-Based Authentication

```yaml
authentication:
  type: session
  
  # Session cookie name
  session_cookie_name: "SESSIONID"
  
  # Session value (can be obtained from manual login)
  session_value: "${SESSION_COOKIE_VALUE}"
  
  # Session validation URL (to check if session is valid)
  validation_url: "https://app.example.com/api/user/profile"
  
  # Expected response for valid session
  validation_response_contains: "user_id"
```

---

## Notification Configuration

### Email Notifications

```yaml
email:
  # Enable/disable email notifications
  enabled: true
  
  # SMTP configuration
  smtp:
    host: "smtp.gmail.com"
    port: 587
    tls: true
    username: "${SMTP_USERNAME}"
    password: "${SMTP_PASSWORD}"
  
  # Sender information
  from:
    name: "AMTD Security Scanner"
    address: "security@example.com"
  
  # Default recipients
  recipients:
    - security-team@example.com
    - devops-team@example.com
  
  # Email templates
  templates:
    scan_complete: "templates/email/scan-complete.html"
    scan_failed: "templates/email/scan-failed.html"
    critical_alert: "templates/email/critical-alert.html"
  
  # Notification rules
  rules:
    # Send on scan completion
    - event: scan.completed
      severity: all
      template: scan_complete
      attach_report: true
    
    # Send immediate alert for critical vulnerabilities
    - event: vulnerability.detected
      severity: critical
      template: critical_alert
      immediate: true
    
    # Daily summary
    - event: daily_summary
      schedule: "0 9 * * *"
      template: daily_summary
```

### Slack Notifications

```yaml
slack:
  enabled: true
  
  # Slack webhook URL
  webhook_url: "${SLACK_WEBHOOK_URL}"
  
  # Default channel
  channel: "#security-alerts"
  
  # Bot username
  username: "AMTD Security"
  
  # Bot icon
  icon_emoji: ":shield:"
  
  # Mention users/groups for critical findings
  mentions:
    critical: "@security-team"
    high: "@channel"
  
  # Notification rules
  rules:
    - event: scan.completed
      severity: all
      include_summary: true
      include_link: true
    
    - event: vulnerability.detected
      severity: [critical, high]
      immediate: true
  
  # Message format
  format:
    use_blocks: true
    include_charts: false
```

### GitHub Notifications

```yaml
github:
  enabled: true
  
  # GitHub API token
  token: "${GITHUB_TOKEN}"
  
  # Repository
  owner: "your-org"
  repo: "your-repo"
  
  # Issue creation
  issues:
    # Create issues for vulnerabilities
    create_for_severity: [critical, high]
    
    # Issue labels
    labels:
      - security
      - vulnerability
      - automated
    
    # Default assignees
    assignees:
      - security-lead
    
    # Issue template
    template: ".github/ISSUE_TEMPLATE/security_vulnerability.md"
    
    # Auto-close fixed vulnerabilities
    auto_close_fixed: true
  
  # Pull request comments
  pull_requests:
    # Comment on PRs with scan results
    enabled: true
    
    # Comment format
    format: summary  # Options: summary, detailed
    
    # Block PR merge if thresholds exceeded
    block_merge: false
    
    # Required checks
    status_checks:
      - name: "AMTD Security Scan"
        strict: true
```

### Webhook Notifications

```yaml
webhooks:
  - name: "External SIEM"
    url: "https://siem.example.com/webhook/amtd"
    
    # Events to send
    events:
      - scan.completed
      - vulnerability.detected
    
    # Webhook secret for signature verification
    secret: "${WEBHOOK_SECRET}"
    
    # Custom headers
    headers:
      X-Custom-Header: "value"
    
    # Retry configuration
    retry:
      max_attempts: 3
      backoff: exponential
```

---

## Environment Variables

### Required Environment Variables

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=amtd
DB_USER=amtd
DB_PASSWORD=your_secure_password

# Object Storage (MinIO/S3)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=your_secure_password
MINIO_BUCKET=amtd-reports

# Jenkins
JENKINS_URL=http://localhost:8080
JENKINS_USER=admin
JENKINS_TOKEN=your_jenkins_token

# SMTP (for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# GitHub Integration (optional)
GITHUB_TOKEN=ghp_your_github_token
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# Slack Integration (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Credentials (for scanning)
SCAN_USERNAME=test_user
SCAN_PASSWORD=test_password
```

### Environment-Specific Variables

**Development (.env.development):**
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug
SCAN_CONCURRENT_LIMIT=2
```

**Production (.env.production):**
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
SCAN_CONCURRENT_LIMIT=10
ENABLE_RATE_LIMITING=true
```

---

## Advanced Configuration

### Global Configuration

**File:** `config/global.yaml`

```yaml
# Global system configuration
system:
  # System name
  name: "AMTD Security Scanner"
  
  # Environment: development, staging, production
  environment: "${ENVIRONMENT:-development}"
  
  # Logging
  logging:
    level: "${LOG_LEVEL:-info}"  # debug, info, warning, error
    format: json
    output: stdout
    
    # Log rotation
    rotation:
      max_size: 100  # MB
      max_files: 10
      max_age: 30  # days
  
  # Performance
  performance:
    # Max concurrent scans
    max_concurrent_scans: "${SCAN_CONCURRENT_LIMIT:-5}"
    
    # Worker threads
    worker_threads: 4
    
    # Request timeout
    default_timeout: 30  # seconds
  
  # Security
  security:
    # Enable rate limiting
    rate_limiting:
      enabled: "${ENABLE_RATE_LIMITING:-false}"
      requests_per_minute: 60
    
    # API authentication
    api:
      token_expiry: 3600  # seconds
      require_https: true
  
  # Database
  database:
    host: "${DB_HOST:-localhost}"
    port: "${DB_PORT:-5432}"
    name: "${DB_NAME:-amtd}"
    user: "${DB_USER:-amtd}"
    password: "${DB_PASSWORD}"
    
    # Connection pool
    pool:
      min_size: 5
      max_size: 20
      timeout: 30
  
  # Object storage
  storage:
    type: "minio"  # minio, s3
    endpoint: "${MINIO_ENDPOINT:-localhost:9000}"
    access_key: "${MINIO_ACCESS_KEY}"
    secret_key: "${MINIO_SECRET_KEY}"
    bucket: "${MINIO_BUCKET:-amtd-reports}"
    secure: false  # Use HTTPS
  
  # Jenkins integration
  jenkins:
    url: "${JENKINS_URL}"
    user: "${JENKINS_USER}"
    token: "${JENKINS_TOKEN}"
```

---

## Configuration Examples

### Example 1: Simple Web Application

```yaml
# config/applications/simple-webapp.yaml
application:
  name: "Simple Web App"
  url: "https://simple.example.com"
  owner: "dev-team@example.com"
  criticality: medium
  
  scan:
    schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM
    type: quick
    timeout: 3600
    
    thresholds:
      critical: 0
      high: 10
      medium: 50
  
  notifications:
    email:
      - dev-team@example.com
```

### Example 2: E-commerce Application (High Security)

```yaml
# config/applications/ecommerce.yaml
application:
  name: "E-Commerce Platform"
  url: "https://shop.example.com"
  owner: "security-team@example.com"
  team: "E-Commerce"
  criticality: critical
  
  tags:
    - production
    - pci-compliant
    - customer-data
  
  scan:
    schedule: "0 2 * * *"  # Daily at 2 AM
    type: full
    timeout: 10800  # 3 hours
    policy: aggressive
    
    authentication:
      type: form
      login_url: "https://shop.example.com/login"
      username_field: "email"
      password_field: "password"
      credentials:
        username: "${ECOMMERCE_SCAN_USER}"
        password: "${ECOMMERCE_SCAN_PASS}"
      success_indicator: "My Account"
    
    exclusions:
      - "/checkout/complete"
      - "/payment/process"
      - "/admin/.*"
    
    thresholds:
      critical: 0
      high: 0
      medium: 5
      low: 20
  
  notifications:
    email:
      - security-team@example.com
      - ecommerce-leads@example.com
    
    slack:
      enabled: true
      channel: "#security-critical"
    
    github:
      enabled: true
      create_issues: true
      issue_severity: [critical, high, medium]
```

### Example 3: Internal API (Minimal Scanning)

```yaml
# config/applications/internal-api.yaml
application:
  name: "Internal API"
  url: "https://api-internal.example.com"
  owner: "api-team@example.com"
  criticality: low
  
  scan:
    schedule: "0 4 * * 1"  # Weekly on Monday at 4 AM
    type: quick
    policy: passive-only
    
    authentication:
      type: api_key
      location: header
      key_name: "X-API-Key"
      key_value: "${INTERNAL_API_KEY}"
    
    thresholds:
      critical: 1
      high: 5
      medium: null
  
  notifications:
    email:
      - api-team@example.com
```

---

## Configuration Validation

### Validate Configuration

```bash
# Validate a specific application config
python scripts/validate-config.py config/applications/my-app.yaml

# Validate all configurations
python scripts/validate-config.py --all

# Validate and show merged config
python scripts/validate-config.py config/applications/my-app.yaml --show-merged
```

### Configuration Schema

Configuration is validated against JSON Schema. Schema files are in `config/schemas/`.

---

## Configuration Best Practices

1. **Use Environment Variables for Secrets**
   - Never commit secrets to Git
   - Use `${VAR_NAME}` syntax for substitution

2. **Start with Templates**
   - Copy `config/applications/template.yaml`
   - Customize for your needs

3. **Test Configurations**
   - Validate before committing
   - Test in development first

4. **Document Custom Settings**
   - Add comments to explain non-obvious settings
   - Keep README updated

5. **Version Control**
   - Commit all non-secret configs to Git
   - Use `.gitignore` for secret files

6. **Regular Reviews**
   - Review configs quarterly
   - Remove obsolete applications
   - Update thresholds based on trends

---

**Configuration Version:** 1.0  
**Last Updated:** November 26, 2025
