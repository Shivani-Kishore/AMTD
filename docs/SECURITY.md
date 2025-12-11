# AMTD Security Documentation

**Version:** 1.0  
**Last Updated:** November 26, 2025

---

## Table of Contents

- [Security Policy](#security-policy)
- [Reporting Vulnerabilities](#reporting-vulnerabilities)
- [Security Architecture](#security-architecture)
- [Authentication & Authorization](#authentication--authorization)
- [Data Security](#data-security)
- [Network Security](#network-security)
- [Secure Configuration](#secure-configuration)
- [Security Best Practices](#security-best-practices)
- [Compliance](#compliance)
- [Security Checklist](#security-checklist)

---

## Security Policy

### Supported Versions

| Version | Supported | Security Updates |
|---------|-----------|------------------|
| 1.x.x   | ✅ Yes    | Active          |
| 0.x.x   | ❌ No     | End of Life     |

### Security Update Schedule

- **Critical:** Patch within 24 hours
- **High:** Patch within 7 days
- **Medium:** Patch within 30 days
- **Low:** Patch in next release

---

## Reporting Vulnerabilities

### How to Report

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead:

1. **Email:** security@example.com
2. **Subject:** "SECURITY: [Brief Description]"
3. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

1. **Acknowledgment:** Within 24 hours
2. **Initial Assessment:** Within 72 hours
3. **Status Updates:** Weekly
4. **Resolution:** Based on severity
5. **Disclosure:** Coordinated with reporter

### Responsible Disclosure

We follow a 90-day disclosure timeline:

1. **Day 0:** Vulnerability reported
2. **Day 1-7:** Assessment and validation
3. **Day 7-30:** Patch development
4. **Day 30-60:** Testing and QA
5. **Day 60-90:** Coordinated disclosure
6. **Day 90:** Public disclosure

### Bug Bounty

We currently do not have a bug bounty program, but we:
- Acknowledge security researchers in release notes
- Provide recognition on our security hall of fame

---

## Security Architecture

### Defense in Depth

AMTD implements multiple security layers:

```
┌─────────────────────────────────────────────────┐
│ Layer 7: Application Security                  │
│ - Input validation                              │
│ - Output encoding                               │
│ - CSRF protection                               │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│ Layer 6: Authentication & Authorization         │
│ - SSO/SAML integration                         │
│ - RBAC enforcement                              │
│ - API key management                            │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│ Layer 5: Data Security                          │
│ - Encryption at rest (AES-256)                 │
│ - Encryption in transit (TLS 1.3)              │
│ - Secure secret management                      │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│ Layer 4: Network Security                       │
│ - Container isolation                           │
│ - Network segmentation                          │
│ - Firewall rules                                │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│ Layer 3: Infrastructure Security                │
│ - OS hardening                                  │
│ - Least privilege                               │
│ - Regular updates                               │
└─────────────────────────────────────────────────┘
                     │
┌─────────────────────────────────────────────────┐
│ Layer 2: Monitoring & Detection                 │
│ - Audit logging                                 │
│ - Intrusion detection                           │
│ - Security alerts                               │
└─────────────────────────────────────────────────┘
```

### Threat Model

#### Assets
- Vulnerability scan data
- Application credentials
- User credentials
- API tokens
- Scan reports
- System configurations

#### Threats
- **T1:** Unauthorized access to scan results
- **T2:** Credential theft/exposure
- **T3:** Scan data tampering
- **T4:** Denial of service attacks
- **T5:** Privilege escalation
- **T6:** Container escape
- **T7:** Man-in-the-middle attacks

#### Mitigations
- **M1:** RBAC + encryption (T1)
- **M2:** Secrets management + rotation (T2)
- **M3:** Digital signatures + checksums (T3)
- **M4:** Rate limiting + resource quotas (T4)
- **M5:** Least privilege + audit logs (T5)
- **M6:** Container hardening + SELinux (T6)
- **M7:** TLS 1.3 + certificate pinning (T7)

---

## Authentication & Authorization

### Authentication Methods

#### 1. Local Authentication

```yaml
# Not recommended for production
auth:
  type: local
  users:
    - username: admin
      password_hash: $2b$12$...
      roles: [admin]
```

#### 2. LDAP/Active Directory

```yaml
auth:
  type: ldap
  server: ldap://ldap.example.com
  base_dn: "dc=example,dc=com"
  user_dn_pattern: "uid={0},ou=users,dc=example,dc=com"
  group_search:
    base: "ou=groups,dc=example,dc=com"
    filter: "(member={0})"
```

#### 3. SAML 2.0

```yaml
auth:
  type: saml
  idp:
    entity_id: "https://idp.example.com"
    sso_url: "https://idp.example.com/sso"
    x509_cert: "MII..."
  sp:
    entity_id: "https://amtd.example.com"
    acs_url: "https://amtd.example.com/saml/acs"
```

#### 4. OAuth 2.0 / OpenID Connect

```yaml
auth:
  type: oauth2
  provider: okta  # okta, auth0, google, etc.
  client_id: "${OAUTH_CLIENT_ID}"
  client_secret: "${OAUTH_CLIENT_SECRET}"
  authorization_url: "https://example.okta.com/oauth2/v1/authorize"
  token_url: "https://example.okta.com/oauth2/v1/token"
  user_info_url: "https://example.okta.com/oauth2/v1/userinfo"
```

### Role-Based Access Control (RBAC)

#### Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full system access |
| **Security Engineer** | Manage scans, view all reports, triage vulnerabilities |
| **Developer** | View scans for own applications, view reports |
| **Viewer** | Read-only access to reports |

#### Permission Matrix

| Action | Admin | Security Engineer | Developer | Viewer |
|--------|-------|-------------------|-----------|--------|
| Create/Edit Apps | ✅ | ✅ | ❌ | ❌ |
| Trigger Scans | ✅ | ✅ | ✅* | ❌ |
| View Scans | ✅ | ✅ | ✅* | ✅* |
| Triage Vulns | ✅ | ✅ | ❌ | ❌ |
| View Reports | ✅ | ✅ | ✅* | ✅* |
| Manage Users | ✅ | ❌ | ❌ | ❌ |
| System Config | ✅ | ❌ | ❌ | ❌ |

*Only for assigned applications

### API Authentication

#### API Key Authentication

```bash
# Generate API key
curl -X POST https://amtd.example.com/api/v1/auth/keys \
  -u username:password \
  -d '{"name": "CI/CD Pipeline", "expires_in": 2592000}'

# Use API key
curl -H "X-API-Key: your_api_key" \
  https://amtd.example.com/api/v1/scans
```

#### JWT Token Authentication

```bash
# Obtain token
curl -X POST https://amtd.example.com/api/v1/auth/token \
  -d '{"username": "user", "password": "pass"}'

# Use token
curl -H "Authorization: Bearer eyJhbGc..." \
  https://amtd.example.com/api/v1/scans
```

---

## Data Security

### Encryption at Rest

#### Database Encryption

```yaml
# PostgreSQL encryption
database:
  ssl_mode: require
  ssl_cert: /path/to/client-cert.pem
  ssl_key: /path/to/client-key.pem
  ssl_root_cert: /path/to/ca-cert.pem
  
  # Transparent Data Encryption
  encryption:
    enabled: true
    algorithm: AES-256-GCM
```

#### Object Storage Encryption

```yaml
# MinIO/S3 server-side encryption
storage:
  encryption:
    type: SSE-S3  # or SSE-KMS
    algorithm: AES256
    kms_key_id: "arn:aws:kms:..."  # For SSE-KMS
```

### Encryption in Transit

#### TLS Configuration

```yaml
# Enforce TLS 1.3
tls:
  min_version: "1.3"
  cipher_suites:
    - TLS_AES_128_GCM_SHA256
    - TLS_AES_256_GCM_SHA384
    - TLS_CHACHA20_POLY1305_SHA256
  
  certificates:
    cert_file: /path/to/cert.pem
    key_file: /path/to/key.pem
    ca_file: /path/to/ca.pem
```

### Secret Management

#### Using Environment Variables

```bash
# Never commit secrets to Git
# Use environment variables
export DB_PASSWORD="secure_password"
export API_KEY="secure_api_key"
```

#### Using HashiCorp Vault

```yaml
secrets:
  backend: vault
  vault:
    address: https://vault.example.com
    token: "${VAULT_TOKEN}"
    path: secret/amtd
```

#### Using Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: amtd-secrets
type: Opaque
stringData:
  db-password: secure_password
  api-key: secure_api_key
```

### Data Retention

```yaml
retention:
  # Scan results
  scans:
    duration: 365  # days
    archive_after: 90
  
  # Reports
  reports:
    duration: 365
    compress_after: 30
  
  # Logs
  logs:
    duration: 90
    archive_after: 30
  
  # Audit logs (longer retention for compliance)
  audit_logs:
    duration: 2555  # 7 years
```

---

## Network Security

### Container Isolation

```yaml
# docker-compose.yml
services:
  jenkins:
    networks:
      - management
    # No direct access to scan network
  
  zap-scanner:
    networks:
      - scan
    # Isolated scan network
    
networks:
  management:
    driver: bridge
  scan:
    driver: bridge
    internal: true  # No external access
```

### Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8080/tcp   # Jenkins (use reverse proxy)
sudo ufw enable

# Or using iptables
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j DROP
```

### Network Segmentation

```
┌─────────────────────────────────────────────┐
│         DMZ (Public Network)                │
│  - Reverse Proxy (nginx)                    │
│  - Load Balancer                            │
└─────────────────┬───────────────────────────┘
                  │ TLS
┌─────────────────▼───────────────────────────┐
│    Application Network (Private)            │
│  - Jenkins                                  │
│  - API Server                               │
│  - Dashboard                                │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│      Data Network (Private)                 │
│  - PostgreSQL                               │
│  - MinIO                                    │
│  - Redis                                    │
└─────────────────────────────────────────────┘
```

---

## Secure Configuration

### Jenkins Security

```groovy
// Jenkins configuration as code
jenkins:
  securityRealm:
    saml:
      idpMetadataConfiguration:
        url: "https://idp.example.com/metadata"
  
  authorizationStrategy:
    roleBased:
      roles:
        global:
          - name: "admin"
            permissions:
              - "Overall/Administer"
          - name: "user"
            permissions:
              - "Overall/Read"
              - "Job/Build"
              - "Job/Read"
  
  security:
    csrf:
      defaultCrumbIssuer:
        excludeClientIPFromCrumb: false
    
    apiToken:
      creationOfLegacyTokenEnabled: false
```

### PostgreSQL Security

```sql
-- Create restricted user
CREATE USER amtd_app WITH PASSWORD 'secure_password';

-- Grant minimal permissions
GRANT CONNECT ON DATABASE amtd TO amtd_app;
GRANT USAGE ON SCHEMA public TO amtd_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO amtd_app;

-- Revoke dangerous permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON pg_catalog FROM PUBLIC;
```

### Docker Security

```yaml
# docker-compose.yml security settings
services:
  jenkins:
    # Run as non-root user
    user: "1000:1000"
    
    # Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp
      - /var/jenkins_home/workspace
    
    # Security options
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          memory: 2G
```

---

## Security Best Practices

### Secure Coding Guidelines

#### Input Validation

```python
# Always validate user input
def validate_url(url: str) -> bool:
    """Validate URL format and protocol."""
    from urllib.parse import urlparse
    
    try:
        result = urlparse(url)
        # Only allow HTTP/HTTPS
        if result.scheme not in ['http', 'https']:
            raise ValueError(f"Invalid protocol: {result.scheme}")
        # Validate domain
        if not result.netloc:
            raise ValueError("Invalid URL: No domain")
        return True
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")

# Use it
url = request.args.get('target_url')
if not validate_url(url):
    return {"error": "Invalid URL"}, 400
```

#### Output Encoding

```python
# Prevent XSS by encoding output
from markupsafe import escape

def render_vulnerability(vuln):
    """Render vulnerability safely."""
    return f"""
    <div class="vulnerability">
        <h3>{escape(vuln['type'])}</h3>
        <p>{escape(vuln['description'])}</p>
        <code>{escape(vuln['evidence'])}</code>
    </div>
    """
```

#### SQL Injection Prevention

```python
# Use parameterized queries
def get_scan(scan_id: str):
    """Fetch scan by ID."""
    # Good - parameterized
    query = "SELECT * FROM scans WHERE id = %s"
    result = db.execute(query, (scan_id,))
    
    # Bad - string concatenation
    # query = f"SELECT * FROM scans WHERE id = '{scan_id}'"
    # DO NOT DO THIS!
    
    return result
```

### Secure Dependencies

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Or using pip-audit
pip install pip-audit
pip-audit

# Update dependencies regularly
pip list --outdated
pip install --upgrade package_name
```

### Logging & Monitoring

```python
import logging
import json

# Structured logging for security events
security_logger = logging.getLogger('security')

def log_security_event(event_type, user, details):
    """Log security-relevant events."""
    event = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user': user,
        'ip_address': request.remote_addr,
        'user_agent': request.user_agent.string,
        'details': details
    }
    security_logger.info(json.dumps(event))

# Usage
log_security_event('authentication_failed', username, {
    'reason': 'invalid_password',
    'attempt_count': 3
})
```

---

## Compliance

### SOC 2

- ✅ Access controls (RBAC)
- ✅ Encryption at rest and in transit
- ✅ Audit logging
- ✅ Incident response plan
- ✅ Regular security assessments

### PCI-DSS

- ✅ Network segmentation
- ✅ Strong authentication
- ✅ Encrypted communications
- ✅ Regular vulnerability scanning
- ✅ Access logging and monitoring

### GDPR

- ✅ Data minimization
- ✅ Encryption of personal data
- ✅ Access controls
- ✅ Data retention policies
- ✅ Right to deletion

### HIPAA

- ✅ Access controls
- ✅ Audit trails
- ✅ Encryption
- ✅ Data backup and recovery
- ✅ Breach notification procedures

---

## Security Checklist

### Production Deployment

- [ ] All default passwords changed
- [ ] HTTPS/TLS enabled and enforced
- [ ] Strong password policy configured
- [ ] Multi-factor authentication enabled
- [ ] RBAC configured
- [ ] Secrets in secure storage (Vault/K8s secrets)
- [ ] Database encryption enabled
- [ ] Regular backup schedule configured
- [ ] Firewall rules configured
- [ ] Intrusion detection enabled
- [ ] Audit logging enabled
- [ ] Security monitoring configured
- [ ] Incident response plan documented
- [ ] Security contacts documented
- [ ] Regular security updates scheduled

### Application Security

- [ ] Input validation on all user input
- [ ] Output encoding to prevent XSS
- [ ] Parameterized queries (no SQL injection)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured
- [ ] Session management secure
- [ ] Secure headers configured
- [ ] Error messages don't leak information
- [ ] Security dependencies updated
- [ ] Code reviewed for security issues

### Infrastructure Security

- [ ] OS patches up to date
- [ ] Unnecessary services disabled
- [ ] Least privilege principles applied
- [ ] Container images scanned
- [ ] Network segmentation implemented
- [ ] Security groups/firewall configured
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery tested
- [ ] Disaster recovery plan documented
- [ ] Regular security audits scheduled

---

## Security Contacts

**Security Team:**
- Email: security@example.com
- PGP Key: [Link to public key]
- Response Time: 24 hours

**Emergency Contact:**
- Phone: +1-XXX-XXX-XXXX (24/7)
- For critical security incidents only

---

**Document Version:** 1.0  
**Last Updated:** November 26, 2025  
**Next Review:** March 2026
