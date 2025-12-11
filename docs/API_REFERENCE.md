# AMTD API Reference

**Version:** 1.0  
**Base URL:** `https://api.amtd.example.com/v1`  
**Authentication:** Bearer Token  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Authentication](#authentication)
- [Scan Management](#scan-management)
- [Application Management](#application-management)
- [Vulnerability Management](#vulnerability-management)
- [Report Management](#report-management)
- [Metrics & Analytics](#metrics--analytics)
- [Webhooks](#webhooks)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## Authentication

### Overview

AMTD API uses Bearer Token authentication. All API requests must include a valid API token in the Authorization header.

### Obtaining an API Token

```http
POST /v1/auth/token
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh_token_here"
}
```

### Using the Token

```http
GET /v1/scans
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refreshing Token

```http
POST /v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "refresh_token_here"
}
```

---

## Scan Management

### Trigger a New Scan

Create and trigger a new security scan for an application.

```http
POST /v1/scans
Authorization: Bearer {token}
Content-Type: application/json

{
  "application_id": "uuid",
  "scan_type": "full",
  "configuration": {
    "depth": 5,
    "timeout": 7200,
    "authentication": {
      "type": "form",
      "credentials": {
        "username": "test_user",
        "password": "test_pass"
      }
    }
  }
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `application_id` | UUID | Yes | Target application identifier |
| `scan_type` | string | Yes | `full`, `quick`, or `incremental` |
| `configuration` | object | No | Custom scan configuration |

**Response (202 Accepted):**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Scan queued successfully",
  "estimated_start": "2025-11-26T10:05:00Z"
}
```

---

### Get Scan Status

Retrieve the current status and progress of a scan.

```http
GET /v1/scans/{scan_id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440000",
  "application_id": "app-uuid",
  "application_name": "My Web App",
  "scan_type": "full",
  "status": "running",
  "progress": 45,
  "started_at": "2025-11-26T10:00:00Z",
  "estimated_completion": "2025-11-26T10:30:00Z",
  "statistics": {
    "urls_scanned": 150,
    "requests_sent": 1250,
    "vulnerabilities_found": 12
  }
}
```

**Status Values:**
- `pending` - Scan queued, waiting to start
- `running` - Scan in progress
- `completed` - Scan finished successfully
- `failed` - Scan encountered an error
- `cancelled` - Scan was manually cancelled

---

### List Scans

Retrieve a paginated list of scans with optional filters.

```http
GET /v1/scans?application_id={uuid}&status={status}&limit=20&offset=0
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `application_id` | UUID | Filter by application |
| `status` | string | Filter by status |
| `scan_type` | string | Filter by scan type |
| `start_date` | ISO 8601 | Scans started after this date |
| `end_date` | ISO 8601 | Scans started before this date |
| `limit` | integer | Number of results (max 100) |
| `offset` | integer | Pagination offset |

**Response (200 OK):**
```json
{
  "total": 150,
  "limit": 20,
  "offset": 0,
  "scans": [
    {
      "scan_id": "uuid",
      "application_name": "My Web App",
      "scan_type": "full",
      "status": "completed",
      "started_at": "2025-11-26T10:00:00Z",
      "duration": 1800,
      "vulnerabilities": {
        "critical": 0,
        "high": 3,
        "medium": 8,
        "low": 15
      }
    }
  ]
}
```

---

### Cancel a Scan

Stop a running scan.

```http
POST /v1/scans/{scan_id}/cancel
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "scan_id": "uuid",
  "status": "cancelled",
  "message": "Scan cancelled successfully"
}
```

---

### Delete Scan Results

Delete scan results and associated data.

```http
DELETE /v1/scans/{scan_id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

## Application Management

### Create Application

Register a new application for scanning.

```http
POST /v1/applications
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Web Application",
  "url": "https://app.example.com",
  "owner": "security-team@example.com",
  "team": "Platform Engineering",
  "criticality": "high",
  "scan_schedule": "0 2 * * *",
  "configuration": {
    "authentication": {
      "type": "oauth",
      "config": {
        "client_id": "client_id",
        "client_secret": "client_secret"
      }
    },
    "exclusions": [
      "/admin/.*",
      ".*\\.pdf$"
    ],
    "thresholds": {
      "critical": 0,
      "high": 5,
      "medium": 20
    }
  }
}
```

**Response (201 Created):**
```json
{
  "application_id": "uuid",
  "name": "My Web Application",
  "url": "https://app.example.com",
  "created_at": "2025-11-26T10:00:00Z"
}
```

---

### Get Application

Retrieve application details.

```http
GET /v1/applications/{app_id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "application_id": "uuid",
  "name": "My Web Application",
  "url": "https://app.example.com",
  "owner": "security-team@example.com",
  "team": "Platform Engineering",
  "criticality": "high",
  "scan_schedule": "0 2 * * *",
  "configuration": {...},
  "statistics": {
    "total_scans": 45,
    "last_scan": "2025-11-26T02:00:00Z",
    "open_vulnerabilities": 12
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-11-26T10:00:00Z"
}
```

---

### List Applications

Retrieve all registered applications.

```http
GET /v1/applications?team={team}&criticality={level}&limit=20&offset=0
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total": 50,
  "applications": [
    {
      "application_id": "uuid",
      "name": "My Web App",
      "url": "https://app.example.com",
      "criticality": "high",
      "open_vulnerabilities": 12,
      "last_scan": "2025-11-26T02:00:00Z"
    }
  ]
}
```

---

### Update Application

Update application configuration.

```http
PUT /v1/applications/{app_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "scan_schedule": "0 3 * * *",
  "configuration": {
    "thresholds": {
      "critical": 0,
      "high": 3
    }
  }
}
```

**Response (200 OK):**
```json
{
  "application_id": "uuid",
  "message": "Application updated successfully",
  "updated_at": "2025-11-26T10:00:00Z"
}
```

---

### Delete Application

Remove an application and all associated data.

```http
DELETE /v1/applications/{app_id}
Authorization: Bearer {token}
```

**Response (204 No Content)**

---

## Vulnerability Management

### List Vulnerabilities

Retrieve vulnerabilities with filters.

```http
GET /v1/vulnerabilities?application_id={uuid}&severity={level}&status={status}
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `application_id` | UUID | Filter by application |
| `scan_id` | UUID | Filter by specific scan |
| `severity` | string | `critical`, `high`, `medium`, `low`, `info` |
| `status` | string | `new`, `confirmed`, `false_positive`, `fixed` |
| `type` | string | Vulnerability type (e.g., `SQL Injection`) |
| `limit` | integer | Results per page |
| `offset` | integer | Pagination offset |

**Response (200 OK):**
```json
{
  "total": 45,
  "vulnerabilities": [
    {
      "vulnerability_id": "uuid",
      "scan_id": "uuid",
      "application_name": "My Web App",
      "type": "SQL Injection",
      "severity": "high",
      "cvss_score": 7.5,
      "cwe_id": "CWE-89",
      "url": "https://app.example.com/search",
      "method": "POST",
      "parameter": "query",
      "evidence": "Error message revealed SQL syntax",
      "description": "The application is vulnerable to SQL injection...",
      "solution": "Use parameterized queries...",
      "confidence": "high",
      "status": "new",
      "first_detected": "2025-11-26T10:00:00Z",
      "last_seen": "2025-11-26T10:00:00Z"
    }
  ]
}
```

---

### Get Vulnerability Details

Retrieve detailed information about a specific vulnerability.

```http
GET /v1/vulnerabilities/{vuln_id}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "vulnerability_id": "uuid",
  "scan_id": "uuid",
  "application_id": "uuid",
  "type": "Cross-Site Scripting (XSS)",
  "severity": "high",
  "cvss_score": 7.3,
  "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:L",
  "cwe_id": "CWE-79",
  "owasp_category": "A03:2021 - Injection",
  "url": "https://app.example.com/profile",
  "method": "GET",
  "parameter": "username",
  "evidence": "<script>alert('XSS')</script> reflected in response",
  "description": "The application reflects user input without proper sanitization...",
  "solution": "Implement output encoding using a security library...",
  "references": [
    "https://owasp.org/www-community/attacks/xss/",
    "https://cwe.mitre.org/data/definitions/79.html"
  ],
  "confidence": "high",
  "status": "new",
  "assigned_to": null,
  "first_detected": "2025-11-26T10:00:00Z",
  "last_seen": "2025-11-26T10:00:00Z",
  "occurrences": 1
}
```

---

### Update Vulnerability Status

Change the status of a vulnerability (triage).

```http
PATCH /v1/vulnerabilities/{vuln_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "status": "false_positive",
  "comment": "This is a false positive because the parameter is properly validated on the backend.",
  "assigned_to": "developer@example.com"
}
```

**Valid Status Values:**
- `new` - Newly discovered
- `confirmed` - Verified as valid vulnerability
- `false_positive` - Not a real vulnerability
- `fixed` - Remediated
- `accepted` - Risk accepted (won't fix)

**Response (200 OK):**
```json
{
  "vulnerability_id": "uuid",
  "status": "false_positive",
  "updated_by": "security@example.com",
  "updated_at": "2025-11-26T10:00:00Z"
}
```

---

### Bulk Update Vulnerabilities

Update multiple vulnerabilities at once.

```http
POST /v1/vulnerabilities/bulk-update
Authorization: Bearer {token}
Content-Type: application/json

{
  "vulnerability_ids": ["uuid1", "uuid2", "uuid3"],
  "status": "confirmed",
  "assigned_to": "security-team@example.com"
}
```

**Response (200 OK):**
```json
{
  "updated": 3,
  "failed": 0,
  "message": "Bulk update completed successfully"
}
```

---

## Report Management

### Download Report

Download a scan report in specified format.

```http
GET /v1/reports/{report_id}/download?format={format}
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | `html`, `json`, `pdf` |

**Response (200 OK):**
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="scan_report_20251126.html"

[Report content]
```

---

### List Reports

Get all reports for a scan or application.

```http
GET /v1/reports?scan_id={uuid}&format={format}
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "total": 3,
  "reports": [
    {
      "report_id": "uuid",
      "scan_id": "uuid",
      "format": "html",
      "size": 1048576,
      "generated_at": "2025-11-26T10:30:00Z",
      "download_url": "/v1/reports/uuid/download",
      "summary": {
        "critical": 0,
        "high": 3,
        "medium": 8,
        "low": 15,
        "info": 25
      }
    }
  ]
}
```

---

### Generate Custom Report

Create a custom report based on filters.

```http
POST /v1/reports/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "compliance",
  "format": "pdf",
  "filters": {
    "application_ids": ["uuid1", "uuid2"],
    "start_date": "2025-11-01T00:00:00Z",
    "end_date": "2025-11-30T23:59:59Z",
    "severity": ["critical", "high"]
  },
  "options": {
    "include_executive_summary": true,
    "include_details": false
  }
}
```

**Response (202 Accepted):**
```json
{
  "report_id": "uuid",
  "status": "generating",
  "estimated_completion": "2025-11-26T10:35:00Z"
}
```

---

## Metrics & Analytics

### Get Dashboard Metrics

Retrieve high-level metrics for dashboard.

```http
GET /v1/metrics/dashboard?timerange=30d
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timerange` | string | `7d`, `30d`, `90d`, `1y` |

**Response (200 OK):**
```json
{
  "timerange": "30d",
  "total_scans": 245,
  "successful_scans": 238,
  "failed_scans": 7,
  "total_vulnerabilities": 1847,
  "severity_breakdown": {
    "critical": 12,
    "high": 145,
    "medium": 678,
    "low": 890,
    "info": 122
  },
  "scan_success_rate": 97.1,
  "average_scan_duration": 1650,
  "applications_monitored": 52,
  "trend_data": {
    "vulnerabilities": [
      {"date": "2025-11-01", "count": 1820},
      {"date": "2025-11-08", "count": 1835},
      {"date": "2025-11-15", "count": 1842},
      {"date": "2025-11-22", "count": 1847}
    ]
  }
}
```

---

### Get Application Risk Score

Calculate risk score for an application.

```http
GET /v1/metrics/applications/{app_id}/risk-score
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "application_id": "uuid",
  "application_name": "My Web App",
  "risk_score": 7.5,
  "risk_level": "high",
  "factors": {
    "vulnerability_severity": 8.0,
    "vulnerability_count": 7.0,
    "time_since_last_scan": 5.0,
    "open_critical_vulns": 9.0
  },
  "calculation_date": "2025-11-26T10:00:00Z"
}
```

---

### Get Vulnerability Trends

Analyze vulnerability trends over time.

```http
GET /v1/metrics/trends/vulnerabilities?application_id={uuid}&timerange=90d
Authorization: Bearer {token}
```

**Response (200 OK):**
```json
{
  "application_id": "uuid",
  "timerange": "90d",
  "data_points": [
    {
      "date": "2025-09-01",
      "critical": 2,
      "high": 15,
      "medium": 45,
      "low": 80,
      "total": 142
    },
    {
      "date": "2025-10-01",
      "critical": 1,
      "high": 12,
      "medium": 42,
      "low": 78,
      "total": 133
    },
    {
      "date": "2025-11-01",
      "critical": 0,
      "high": 10,
      "medium": 38,
      "low": 75,
      "total": 123
    }
  ],
  "trend": "improving",
  "change_percentage": -13.4
}
```

---

## Webhooks

### Register Webhook

Subscribe to events via webhook.

```http
POST /v1/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": [
    "scan.completed",
    "scan.failed",
    "vulnerability.critical"
  ],
  "secret": "webhook_secret_for_signature",
  "active": true
}
```

**Response (201 Created):**
```json
{
  "webhook_id": "uuid",
  "url": "https://your-server.com/webhook",
  "events": ["scan.completed", "scan.failed", "vulnerability.critical"],
  "created_at": "2025-11-26T10:00:00Z"
}
```

---

### Webhook Event: Scan Completed

```json
{
  "event": "scan.completed",
  "timestamp": "2025-11-26T10:30:00Z",
  "data": {
    "scan_id": "uuid",
    "application_id": "uuid",
    "application_name": "My Web App",
    "scan_type": "full",
    "status": "completed",
    "duration": 1800,
    "vulnerabilities": {
      "critical": 0,
      "high": 3,
      "medium": 8,
      "low": 15,
      "info": 25
    },
    "report_url": "https://api.amtd.example.com/v1/reports/uuid/download"
  }
}
```

---

### Webhook Event: Critical Vulnerability

```json
{
  "event": "vulnerability.critical",
  "timestamp": "2025-11-26T10:15:00Z",
  "data": {
    "vulnerability_id": "uuid",
    "scan_id": "uuid",
    "application_name": "My Web App",
    "type": "SQL Injection",
    "severity": "critical",
    "cvss_score": 9.8,
    "url": "https://app.example.com/api/users",
    "description": "Critical SQL injection vulnerability detected..."
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "scan_type",
        "message": "Must be one of: full, quick, incremental"
      }
    ]
  },
  "request_id": "req_uuid",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation) |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication required |
| `INVALID_TOKEN` | Token is invalid or expired |
| `INSUFFICIENT_PERMISSIONS` | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `VALIDATION_ERROR` | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `SCAN_IN_PROGRESS` | Scan already running for this application |
| `INTERNAL_ERROR` | Server error |

---

## Rate Limiting

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1637942400
```

### Rate Limits

| Endpoint | Limit |
|----------|-------|
| **Authentication** | 10 requests/minute |
| **Scan Operations** | 100 requests/hour |
| **Read Operations** | 1000 requests/hour |
| **Webhook Operations** | 50 requests/hour |

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "retry_after": 60
  }
}
```

---

## Examples

### Complete Workflow Example

```python
import requests
import time

BASE_URL = "https://api.amtd.example.com/v1"
TOKEN = "your_api_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Create an application
app_data = {
    "name": "Test Application",
    "url": "https://test.example.com",
    "owner": "security@example.com"
}
response = requests.post(f"{BASE_URL}/applications", 
                        json=app_data, headers=headers)
app_id = response.json()["application_id"]

# 2. Trigger a scan
scan_data = {
    "application_id": app_id,
    "scan_type": "full"
}
response = requests.post(f"{BASE_URL}/scans", 
                        json=scan_data, headers=headers)
scan_id = response.json()["scan_id"]

# 3. Poll for scan completion
while True:
    response = requests.get(f"{BASE_URL}/scans/{scan_id}", 
                           headers=headers)
    status = response.json()["status"]
    
    if status == "completed":
        break
    elif status == "failed":
        print("Scan failed!")
        break
    
    time.sleep(30)  # Wait 30 seconds

# 4. Get vulnerabilities
response = requests.get(
    f"{BASE_URL}/vulnerabilities?scan_id={scan_id}&severity=critical,high",
    headers=headers
)
vulnerabilities = response.json()["vulnerabilities"]

# 5. Download report
response = requests.get(
    f"{BASE_URL}/reports/{scan_id}/download?format=pdf",
    headers=headers
)
with open("scan_report.pdf", "wb") as f:
    f.write(response.content)
```

---

**API Version:** 1.0  
**Documentation Updated:** November 26, 2025  
**Support:** api-support@example.com
