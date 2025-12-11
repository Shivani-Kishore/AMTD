# AMTD Architecture Documentation

**Version:** 1.0  
**Last Updated:** November 26, 2025  
**Status:** Production

---

## Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [High-Level Architecture](#high-level-architecture)
- [Component Architecture](#component-architecture)
- [Data Architecture](#data-architecture)
- [Integration Architecture](#integration-architecture)
- [Deployment Architecture](#deployment-architecture)
- [Security Architecture](#security-architecture)
- [Scalability & Performance](#scalability--performance)
- [Technology Stack](#technology-stack)

---

## Overview

AMTD follows a **modular, layered architecture** designed for scalability, maintainability, and extensibility. The system is built around a CI/CD-centric approach with Docker-based containerization for isolation and portability.

### Architecture Goals

1. **Modularity:** Independent components with clear boundaries
2. **Scalability:** Horizontal scaling for concurrent scans
3. **Reliability:** Fault tolerance and graceful degradation
4. **Security:** Defense in depth with multiple security layers
5. **Maintainability:** Clean code, documentation, and monitoring
6. **Extensibility:** Easy to add new scanners, integrations, and features

### Key Characteristics

- **Event-Driven:** Pipeline stages trigger events
- **Stateless Scanning:** Each scan runs in isolated container
- **Persistent Storage:** Reports and data stored in databases
- **API-First:** REST API for all operations
- **Infrastructure as Code:** Declarative configurations

---

## Design Principles

### 1. Separation of Concerns
Each component has a single, well-defined responsibility

### 2. Loose Coupling
Components communicate through well-defined interfaces

### 3. High Cohesion
Related functionality grouped together

### 4. Fail-Safe Defaults
System defaults to secure, conservative settings

### 5. Defense in Depth
Multiple layers of security

### 6. Observability
Built-in monitoring and debugging

---

## High-Level Architecture

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

---

## Component Architecture

### 1. Pipeline Orchestrator
- Manages end-to-end scan workflow
- Coordinates between components  
- Handles failures and retries
- Enforces security policies

### 2. Scan Manager
- Launches ZAP Docker containers
- Configures scan policies
- Monitors scan progress
- Enforces resource limits

### 3. Report Generator
- Parses ZAP output
- Generates HTML/JSON/PDF reports
- Archives reports
- Calculates metrics

### 4. Notification Service  
- Email notifications
- Slack/Teams integration
- GitHub issues
- Webhooks

### 5. Configuration Manager
- Loads and validates configs
- Manages secrets
- Environment-specific configs
- Configuration versioning

### 6. Analytics Engine
- Aggregates scan data
- Calculates trends
- Tracks vulnerability lifecycle
- Compliance reporting

---

## Data Architecture

### Core Data Models

**Application:**
- id, name, url, owner, team
- criticality, scan_schedule
- configuration

**Scan:**
- id, application_id, scan_type
- status, trigger, triggered_by
- started_at, completed_at, duration
- statistics, report_path

**Vulnerability:**
- id, scan_id, application_id
- type, severity, cvss_score
- url, method, parameter
- evidence, description, solution
- status, assigned_to

**Report:**
- id, scan_id, format
- path, size, generated_at
- summary

### Database Schema Highlights

```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    configuration JSONB,
    created_at TIMESTAMP
);

CREATE TABLE scans (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    status VARCHAR(20),
    statistics JSONB,
    created_at TIMESTAMP
);

CREATE TABLE vulnerabilities (
    id UUID PRIMARY KEY,
    scan_id UUID REFERENCES scans(id),
    severity VARCHAR(20),
    status VARCHAR(30),
    first_detected TIMESTAMP
);
```

---

## Integration Architecture

### GitHub Integration
- Webhook handlers for push/PR events
- Automatic issue creation
- PR status comments
- Commit status checks

### Slack Integration
- Real-time scan notifications
- Interactive message buttons
- Daily/weekly summaries

### Email Integration
- SMTP-based delivery
- HTML email templates
- Attachment support

---

## Deployment Architecture

### Docker Compose (Dev/Test)
```
Jenkins + PostgreSQL + MinIO + Monitoring
```

### Kubernetes (Production)
```
- Jenkins StatefulSet (master) + Deployment (agents)
- PostgreSQL StatefulSet (replicated)
- MinIO StatefulSet (distributed)
- Prometheus + Grafana
```

---

## Security Architecture

### Security Layers

1. **Application Security**
   - Input validation
   - Output encoding

2. **Authentication/Authorization**
   - SSO/SAML
   - RBAC

3. **Data Security**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)

4. **Network Security**
   - Container isolation
   - Network policies

5. **Infrastructure Security**
   - OS hardening
   - Least privilege

6. **Monitoring & Logging**
   - Audit logs
   - Security alerts

---

## Scalability & Performance

### Horizontal Scaling
- Multiple Jenkins agents
- Concurrent scan execution
- Load balanced API

### Performance Optimizations
- Incremental scanning
- Parallel execution
- Database indexing
- Report caching

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| CI/CD | Jenkins 2.400+ |
| Scanner | OWASP ZAP |
| Container | Docker 20.10+ |
| Database | PostgreSQL 15+ |
| Storage | MinIO/S3 |
| Monitoring | Prometheus + Grafana |
| Logging | ELK Stack |

---

**Document Version:** 1.0  
**Last Updated:** November 26, 2025
