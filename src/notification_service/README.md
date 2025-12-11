# AMTD Notification Service Module

Multi-channel notification system for security scan results.

## Overview

The Notification Service module provides comprehensive notification capabilities across multiple channels:
- **Email** - SMTP-based email notifications with HTML/text templates
- **Slack** - Webhook-based Slack notifications with rich formatting
- **GitHub** - Issue creation, SARIF uploads, and Check Runs
- **Webhook** - Custom HTTP webhooks with retry logic

## Module Structure

```
src/notification_service/
├── __init__.py              # Module initialization
├── email_notifier.py        # Email notifications via SMTP
├── slack_notifier.py        # Slack webhook notifications
├── github_notifier.py       # GitHub API integration
├── webhook_notifier.py      # HTTP webhook notifications
├── notification_manager.py  # Coordinates all notifiers
└── README.md               # This file

templates/notifications/
├── scan_notification.html   # HTML email template for scan completion
├── scan_notification.txt    # Text email template for scan completion
├── scan_failure.html        # HTML email template for failures
├── scan_failure.txt         # Text email template for failures
├── threshold_alert.html     # HTML email template for threshold alerts
└── threshold_alert.txt      # Text email template for threshold alerts
```

## Components

### 1. EmailNotifier

Sends email notifications via SMTP with HTML and plain text versions.

**Features:**
- SMTP with TLS support
- HTML and text email templates
- File attachments (PDF, JSON reports)
- Template rendering with Jinja2
- Custom severity colors

**Usage:**
```python
from notification_service import EmailNotifier

notifier = EmailNotifier(
    smtp_host='smtp.gmail.com',
    smtp_port=587,
    smtp_user='your-email@gmail.com',
    smtp_password='your-password',
    from_address='noreply@example.com'
)

# Send scan notification
notifier.send_scan_notification(
    recipients=['security@example.com'],
    scan_info=scan_info,
    statistics=statistics,
    report_url='http://jenkins/reports/scan-123',
    attachments=['report.pdf']
)

# Test connection
if notifier.test_connection():
    print("SMTP configured correctly")
```

**Configuration:**
```python
# Via environment variables
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@example.com
```

### 2. SlackNotifier

Sends Slack notifications via webhooks with rich formatting.

**Features:**
- Webhook-based messaging
- Rich message formatting with attachments
- Severity-based color coding
- Interactive buttons
- Channel targeting

**Usage:**
```python
from notification_service import SlackNotifier

notifier = SlackNotifier(
    webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL',
    channel='#security-alerts'
)

# Send scan notification
notifier.send_scan_notification(
    scan_info=scan_info,
    statistics=statistics,
    report_url='http://jenkins/reports/scan-123'
)

# Test webhook
if notifier.test_connection():
    print("Slack webhook configured correctly")
```

**Configuration:**
```python
# Via environment variables
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#security-alerts
```

### 3. GitHubNotifier

Integrates with GitHub for issue creation, SARIF uploads, and Check Runs.

**Features:**
- Create issues for vulnerabilities
- Upload SARIF reports to Code Scanning
- Create Check Runs for PR integration
- Automatic issue deduplication
- Severity-based filtering

**Usage:**
```python
from notification_service import GitHubNotifier

notifier = GitHubNotifier(
    token='ghp_your_github_token',
    repo_owner='your-org',
    repo_name='your-repo'
)

# Create issues for vulnerabilities
result = notifier.create_issues_for_vulnerabilities(
    vulnerabilities=vulnerabilities,
    scan_info=scan_info,
    severity_filter=['critical', 'high'],
    labels=['security', 'automated']
)
print(f"Created {result['created']} issues")

# Upload SARIF report
notifier.upload_sarif_report(
    sarif_file_path='report.sarif',
    ref='refs/heads/main'
)

# Create check run
notifier.create_check_run(
    scan_info=scan_info,
    statistics=statistics,
    conclusion='failure' if statistics['critical'] > 0 else 'success',
    report_url='http://jenkins/reports/scan-123'
)
```

**Configuration:**
```python
# Via environment variables
GITHUB_TOKEN=ghp_your_github_token
GITHUB_REPO_OWNER=your-org
GITHUB_REPO_NAME=your-repo
```

### 4. WebhookNotifier

Sends HTTP POST requests to custom webhook endpoints.

**Features:**
- Multiple webhook URLs
- Automatic retry with exponential backoff
- Custom event types
- JSON payload delivery
- Connection pooling

**Usage:**
```python
from notification_service import WebhookNotifier

notifier = WebhookNotifier(
    webhook_urls=[
        'https://webhook1.example.com/amtd',
        'https://webhook2.example.com/security'
    ],
    timeout=30,
    retry_count=3
)

# Send scan notification
results = notifier.send_scan_notification(
    scan_info=scan_info,
    statistics=statistics,
    vulnerabilities=vulnerabilities[:100],  # Limit payload size
    report_url='http://jenkins/reports/scan-123',
    custom_data={'environment': 'production'}
)
print(f"Sent to {results['sent']}/{results['total']} webhooks")

# Send custom event
notifier.send_custom_webhook(
    event_type='custom.event',
    data={'key': 'value'}
)
```

**Configuration:**
```python
# Via environment variables
WEBHOOK_URLS=https://webhook1.com,https://webhook2.com
```

### 5. NotificationManager

Coordinates all notification services with unified interface.

**Features:**
- Unified notification interface
- Channel-specific configuration
- Automatic error handling
- Connection testing
- Channel selection

**Usage:**
```python
from notification_service import NotificationManager

# Configure all channels
config = {
    'email': {
        'enabled': True,
        'recipients': ['security@example.com', 'team@example.com'],
        'attach_pdf': True,
        'attach_json': False
    },
    'slack': {
        'enabled': True,
        'channel': '#security-alerts'
    },
    'github': {
        'enabled': True,
        'create_issues': True,
        'upload_sarif': True,
        'create_check_run': False,
        'issue_severity_filter': ['critical', 'high'],
        'issue_labels': ['security', 'automated']
    },
    'webhook': {
        'enabled': True,
        'urls': ['https://webhook.example.com/amtd']
    }
}

manager = NotificationManager(config)

# Test all connections
test_results = manager.test_all_connections()
print(f"Active channels: {manager.get_active_channels()}")

# Send notifications across all channels
results = manager.send_scan_notification(
    scan_info=scan_info,
    statistics=statistics,
    vulnerabilities=vulnerabilities,
    report_url='http://jenkins/reports/scan-123',
    report_files={
        'pdf': '/path/to/report.pdf',
        'json': '/path/to/report.json',
        'sarif': '/path/to/report.sarif'
    }
)

# Send only to specific channels
results = manager.send_scan_notification(
    scan_info=scan_info,
    statistics=statistics,
    channels=['email', 'slack']  # Only email and Slack
)

# Send failure notification
manager.send_failure_notification(
    scan_info=scan_info,
    error_message='ZAP container failed to start'
)

# Send threshold alert
manager.send_threshold_alert(
    scan_info=scan_info,
    statistics=statistics,
    exceeded_thresholds={
        'critical': {'count': 5, 'threshold': 0},
        'high': {'count': 15, 'threshold': 5}
    }
)
```

## Notification Types

### Scan Completion

Sent when a security scan completes successfully.

**Contains:**
- Vulnerability statistics by severity
- Scan details (application, type, target)
- Link to full report
- Severity-based alerts

**Triggers:**
- Scan completes successfully
- Results are available

### Scan Failure

Sent when a security scan fails to complete.

**Contains:**
- Scan information
- Error message
- Recommended troubleshooting steps

**Triggers:**
- Scanner crashes
- Target unreachable
- Configuration errors

### Threshold Alert

Sent when vulnerability thresholds are exceeded.

**Contains:**
- Exceeded threshold details
- Overall statistics
- Severity breakdown
- Recommended actions

**Triggers:**
- Critical vulnerabilities exceed 0
- High vulnerabilities exceed configured limit
- Custom threshold violations

## Email Templates

### Template Variables

All email templates have access to:

**scan_info:**
- application
- scan_id
- scan_type
- target_url
- started_at
- completed_at

**statistics:**
- critical
- high
- medium
- low
- info
- total

**Additional:**
- severity (overall)
- severity_color (hex code)
- report_url
- error_message (failure only)
- exceeded_thresholds (alert only)

### Custom Templates

Create custom templates in `templates/notifications/`:

```html
<!-- custom_notification.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Custom Notification</title>
</head>
<body>
    <h1>{{ scan_info.application }}</h1>
    <p>Found {{ statistics.total }} issues</p>
</body>
</html>
```

Use in code:
```python
template = email_notifier.env.get_template('custom_notification.html')
html = template.render(scan_info=scan_info, statistics=statistics)
```

## Webhook Payload Format

### Scan Completion Payload

```json
{
  "event": "scan.completed",
  "timestamp": "2025-01-01T12:00:00Z",
  "source": "AMTD",
  "scan_info": {
    "application": "my-app",
    "scan_id": "scan-123",
    "scan_type": "full",
    "target_url": "http://example.com"
  },
  "statistics": {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 15,
    "info": 20,
    "total": 52
  },
  "severity": "critical",
  "report_url": "http://jenkins/reports/scan-123",
  "vulnerabilities": [...],
  "custom": {
    "environment": "production"
  }
}
```

### Scan Failure Payload

```json
{
  "event": "scan.failed",
  "timestamp": "2025-01-01T12:00:00Z",
  "source": "AMTD",
  "scan_info": {...},
  "error": "Target unreachable"
}
```

### Threshold Alert Payload

```json
{
  "event": "threshold.exceeded",
  "timestamp": "2025-01-01T12:00:00Z",
  "source": "AMTD",
  "scan_info": {...},
  "statistics": {...},
  "exceeded_thresholds": {
    "critical": {"count": 5, "threshold": 0}
  }
}
```

## Integration Examples

### With Scan Manager

```python
from scan_manager import ScanExecutor
from report_generator import ReportManager
from notification_service import NotificationManager

# Execute scan
executor = ScanExecutor()
scan_results = executor.execute_scan('my-app')

# Generate reports
report_manager = ReportManager(output_dir='./reports')
reports = report_manager.generate_all(scan_results)

# Send notifications
notification_manager = NotificationManager(config)
notification_manager.send_scan_notification(
    scan_info=scan_results['scan_info'],
    statistics=scan_results['statistics'],
    vulnerabilities=scan_results['vulnerabilities'],
    report_url='http://jenkins/reports',
    report_files=reports
)
```

### With Jenkins

```groovy
stage('Send Notifications') {
    steps {
        script {
            sh """
                python3 -c "
                from notification_service import NotificationManager
                import json

                with open('scan_results.json') as f:
                    results = json.load(f)

                config = {
                    'email': {'enabled': True, 'recipients': ['team@example.com']},
                    'slack': {'enabled': True}
                }

                manager = NotificationManager(config)
                manager.send_scan_notification(
                    scan_info=results['scan_info'],
                    statistics=results['statistics'],
                    report_url='${BUILD_URL}artifact/reports/report.html'
                )
                "
            """
        }
    }
}
```

## Best Practices

1. **Connection Testing**: Always test connections during setup
2. **Error Handling**: Wrap notifications in try-catch blocks
3. **Channel Selection**: Only enable channels you need
4. **Template Customization**: Customize templates for your organization
5. **Severity Filtering**: Filter GitHub issues by severity to avoid spam
6. **Webhook Security**: Use HTTPS webhooks with authentication
7. **Rate Limiting**: Be mindful of API rate limits (especially GitHub)
8. **Attachment Size**: Limit email attachments to avoid delivery issues

## Troubleshooting

### Email Not Sending

**Issue**: SMTP authentication failed

**Solution**:
- Verify SMTP credentials
- Enable "Less secure apps" or use app-specific password
- Check SMTP host and port
- Test with `email_notifier.test_connection()`

### Slack Webhook Failing

**Issue**: Slack returns 400 error

**Solution**:
- Verify webhook URL is correct
- Check message payload format
- Test with `slack_notifier.test_connection()`

### GitHub API Rate Limit

**Issue**: GitHub API returns 403 rate limit exceeded

**Solution**:
- Use authenticated requests (increases limit to 5000/hour)
- Implement caching for repeated operations
- Filter issues by severity to reduce API calls

### Webhook Timeout

**Issue**: Webhook requests timing out

**Solution**:
- Increase timeout value
- Check webhook endpoint is accessible
- Verify network connectivity
- Enable retry logic

## Dependencies

Required Python packages:
- `requests`: HTTP requests for webhooks and APIs
- `jinja2`: Template rendering for emails
- Standard library: `smtplib`, `email`

Install:
```bash
pip install requests jinja2
```

## Security Considerations

1. **Credentials**: Store credentials in environment variables or secrets manager
2. **Email Security**: Use TLS encryption for SMTP
3. **GitHub Tokens**: Use fine-grained tokens with minimal permissions
4. **Webhook Authentication**: Implement signature verification for webhooks
5. **Sensitive Data**: Avoid including sensitive data in notifications
6. **Rate Limiting**: Implement rate limiting to prevent abuse

## Support

For issues or questions:
- Review notification service logs
- Test individual notifiers separately
- Check channel-specific documentation
- Verify credentials and permissions
