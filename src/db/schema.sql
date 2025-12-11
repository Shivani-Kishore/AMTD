-- AMTD Database Schema
-- Complete database schema for the AMTD system

-- ============================================
-- Applications Table
-- ============================================
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    url TEXT NOT NULL,
    owner VARCHAR(255) NOT NULL,
    team VARCHAR(255),
    criticality VARCHAR(20) CHECK (criticality IN ('critical', 'high', 'medium', 'low')),
    tags JSONB DEFAULT '[]'::jsonb,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

CREATE INDEX idx_applications_name ON applications(name);
CREATE INDEX idx_applications_owner ON applications(owner);
CREATE INDEX idx_applications_criticality ON applications(criticality);
CREATE INDEX idx_applications_is_active ON applications(is_active);
CREATE INDEX idx_applications_tags ON applications USING gin(tags);

-- ============================================
-- Scans Table
-- ============================================
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    scan_type VARCHAR(20) NOT NULL CHECK (scan_type IN ('full', 'quick', 'incremental')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    trigger VARCHAR(50) CHECK (trigger IN ('manual', 'scheduled', 'git_commit', 'api', 'webhook')),
    triggered_by VARCHAR(255),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration INTEGER, -- seconds
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),

    -- Statistics
    statistics JSONB DEFAULT '{}'::jsonb,

    -- URLs scanned, requests sent, etc.
    urls_scanned INTEGER DEFAULT 0,
    requests_sent INTEGER DEFAULT 0,

    -- Vulnerability counts
    critical_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    medium_count INTEGER DEFAULT 0,
    low_count INTEGER DEFAULT 0,
    info_count INTEGER DEFAULT 0,
    total_vulnerabilities INTEGER DEFAULT 0,

    -- Build information (if from CI/CD)
    build_number INTEGER,
    build_url TEXT,
    git_commit VARCHAR(40),
    git_branch VARCHAR(255),

    -- Report paths
    report_html_path TEXT,
    report_json_path TEXT,
    report_pdf_path TEXT,

    -- ZAP session data
    zap_session_path TEXT,
    zap_log_path TEXT,

    -- Error information
    error_message TEXT,
    error_details JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_scans_application_id ON scans(application_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_scan_type ON scans(scan_type);
CREATE INDEX idx_scans_started_at ON scans(started_at DESC);
CREATE INDEX idx_scans_completed_at ON scans(completed_at DESC);
CREATE INDEX idx_scans_trigger ON scans(trigger);

-- ============================================
-- Vulnerabilities Table
-- ============================================
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,

    -- Vulnerability details
    name VARCHAR(500) NOT NULL,
    type VARCHAR(255),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    confidence VARCHAR(20) CHECK (confidence IN ('high', 'medium', 'low')),

    -- CVSS scoring
    cvss_score DECIMAL(3, 1),
    cvss_vector VARCHAR(255),

    -- CWE/OWASP mapping
    cwe_id VARCHAR(20),
    owasp_category VARCHAR(100),

    -- Location
    url TEXT NOT NULL,
    method VARCHAR(10),
    parameter VARCHAR(500),
    attack VARCHAR(1000),

    -- Evidence
    evidence TEXT,
    other_info TEXT,

    -- Description and solution
    description TEXT,
    solution TEXT,
    reference TEXT,

    -- Status and assignment
    status VARCHAR(30) DEFAULT 'new' CHECK (status IN ('new', 'confirmed', 'false_positive', 'fixed', 'accepted', 'wont_fix')),
    assigned_to VARCHAR(255),

    -- GitHub issue tracking
    github_issue_number INTEGER,
    github_issue_url TEXT,

    -- Timestamps
    first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fixed_at TIMESTAMP,

    -- Comments
    comments JSONB DEFAULT '[]'::jsonb,

    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vulnerabilities_scan_id ON vulnerabilities(scan_id);
CREATE INDEX idx_vulnerabilities_application_id ON vulnerabilities(application_id);
CREATE INDEX idx_vulnerabilities_severity ON vulnerabilities(severity);
CREATE INDEX idx_vulnerabilities_status ON vulnerabilities(status);
CREATE INDEX idx_vulnerabilities_type ON vulnerabilities(type);
CREATE INDEX idx_vulnerabilities_cwe_id ON vulnerabilities(cwe_id);
CREATE INDEX idx_vulnerabilities_first_detected ON vulnerabilities(first_detected DESC);

-- ============================================
-- Reports Table
-- ============================================
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,

    format VARCHAR(20) NOT NULL CHECK (format IN ('html', 'json', 'pdf', 'xml', 'markdown')),
    file_path TEXT NOT NULL,
    file_size BIGINT, -- bytes
    storage_location VARCHAR(50) DEFAULT 'local' CHECK (storage_location IN ('local', 's3', 'minio')),
    storage_bucket VARCHAR(255),
    storage_key TEXT,

    -- Report summary
    summary JSONB DEFAULT '{}'::jsonb,

    -- Executive summary
    executive_summary TEXT,

    -- Report metadata
    generated_by VARCHAR(255),
    report_template VARCHAR(100),

    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,

    -- Access tracking
    download_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_reports_scan_id ON reports(scan_id);
CREATE INDEX idx_reports_application_id ON reports(application_id);
CREATE INDEX idx_reports_format ON reports(format);
CREATE INDEX idx_reports_generated_at ON reports(generated_at DESC);

-- ============================================
-- Notifications Table
-- ============================================
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,

    type VARCHAR(50) NOT NULL CHECK (type IN ('email', 'slack', 'github', 'webhook', 'teams')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed', 'skipped')),

    -- Recipients
    recipients JSONB,

    -- Message details
    subject VARCHAR(500),
    message TEXT,

    -- Delivery details
    sent_at TIMESTAMP,
    delivery_attempts INTEGER DEFAULT 0,

    -- Error information
    error_message TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_scan_id ON notifications(scan_id);
CREATE INDEX idx_notifications_application_id ON notifications(application_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- ============================================
-- Users Table (for RBAC)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),

    -- Authentication
    password_hash VARCHAR(255), -- For local auth

    -- SSO integration
    sso_provider VARCHAR(50),
    sso_id VARCHAR(255),

    -- Role
    role VARCHAR(50) NOT NULL DEFAULT 'viewer' CHECK (role IN ('admin', 'security_engineer', 'developer', 'viewer')),

    -- Permissions
    permissions JSONB DEFAULT '[]'::jsonb,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,

    -- API access
    api_key_hash VARCHAR(255),
    api_key_created_at TIMESTAMP,

    -- Last activity
    last_login_at TIMESTAMP,
    last_active_at TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);

-- ============================================
-- Audit Log Table
-- ============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    username VARCHAR(100),

    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,

    -- Details
    details JSONB DEFAULT '{}'::jsonb,

    -- Request information
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,

    -- Result
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_username ON audit_log(username);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- ============================================
-- Metrics Table (for dashboard and analytics)
-- ============================================
CREATE TABLE IF NOT EXISTS metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- counter, gauge, histogram
    metric_value DECIMAL,

    -- Labels/dimensions
    labels JSONB DEFAULT '{}'::jsonb,

    -- Timestamp
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_recorded_at ON metrics(recorded_at DESC);
CREATE INDEX idx_metrics_labels ON metrics USING gin(labels);

-- ============================================
-- Functions and Triggers
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update_updated_at trigger to relevant tables
CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scans_updated_at BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vulnerabilities_updated_at BEFORE UPDATE ON vulnerabilities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notifications_updated_at BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate scan duration
CREATE OR REPLACE FUNCTION calculate_scan_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.completed_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at))::INTEGER;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER calculate_scans_duration BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION calculate_scan_duration();

-- Function to update total vulnerabilities count
CREATE OR REPLACE FUNCTION update_vulnerability_counts()
RETURNS TRIGGER AS $$
BEGIN
    NEW.total_vulnerabilities = COALESCE(NEW.critical_count, 0) +
                                COALESCE(NEW.high_count, 0) +
                                COALESCE(NEW.medium_count, 0) +
                                COALESCE(NEW.low_count, 0) +
                                COALESCE(NEW.info_count, 0);
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scans_vulnerability_counts BEFORE INSERT OR UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_vulnerability_counts();

-- ============================================
-- Views for Common Queries
-- ============================================

-- View: Application Portfolio Overview
CREATE OR REPLACE VIEW vw_application_portfolio AS
SELECT
    a.id,
    a.name,
    a.url,
    a.owner,
    a.team,
    a.criticality,
    a.is_active,
    COUNT(DISTINCT s.id) as total_scans,
    MAX(s.started_at) as last_scan_date,
    SUM(CASE WHEN v.severity = 'critical' THEN 1 ELSE 0 END) as open_critical,
    SUM(CASE WHEN v.severity = 'high' THEN 1 ELSE 0 END) as open_high,
    SUM(CASE WHEN v.severity = 'medium' THEN 1 ELSE 0 END) as open_medium,
    SUM(CASE WHEN v.status = 'new' THEN 1 ELSE 0 END) as new_vulnerabilities
FROM applications a
LEFT JOIN scans s ON a.id = s.application_id AND s.status = 'completed'
LEFT JOIN vulnerabilities v ON a.id = v.application_id AND v.status NOT IN ('fixed', 'false_positive')
GROUP BY a.id, a.name, a.url, a.owner, a.team, a.criticality, a.is_active;

-- View: Recent Scans
CREATE OR REPLACE VIEW vw_recent_scans AS
SELECT
    s.id,
    s.application_id,
    a.name as application_name,
    s.scan_type,
    s.status,
    s.started_at,
    s.completed_at,
    s.duration,
    s.critical_count,
    s.high_count,
    s.medium_count,
    s.low_count,
    s.total_vulnerabilities
FROM scans s
JOIN applications a ON s.application_id = a.id
ORDER BY s.started_at DESC;

-- View: Vulnerability Summary
CREATE OR REPLACE VIEW vw_vulnerability_summary AS
SELECT
    v.id,
    v.scan_id,
    v.application_id,
    a.name as application_name,
    v.name as vulnerability_name,
    v.severity,
    v.status,
    v.url,
    v.cwe_id,
    v.first_detected,
    v.last_seen,
    v.assigned_to
FROM vulnerabilities v
JOIN applications a ON v.application_id = a.id
WHERE v.status NOT IN ('fixed', 'false_positive')
ORDER BY
    CASE v.severity
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        WHEN 'medium' THEN 3
        WHEN 'low' THEN 4
        ELSE 5
    END,
    v.first_detected DESC;

-- ============================================
-- Initial Data
-- ============================================

-- Insert default admin user (password should be changed immediately)
INSERT INTO users (username, email, full_name, role, is_active, is_verified)
VALUES ('admin', 'admin@example.com', 'Administrator', 'admin', TRUE, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO amtd;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO amtd;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO amtd;
