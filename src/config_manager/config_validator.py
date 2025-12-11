"""
Configuration Validator
Validates configuration against JSON schemas and business rules
"""

import logging
from typing import Dict, Any, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates configuration files"""

    def __init__(self):
        """Initialize the ConfigValidator"""
        self.errors = []
        self.warnings = []

    def validate_application_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate application configuration

        Args:
            config: Configuration dictionary to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        if 'application' not in config:
            self.errors.append("Missing 'application' section in configuration")
            return False, self.errors, self.warnings

        app_config = config['application']

        # Required fields
        self._validate_required_field(app_config, 'name', str)
        self._validate_required_field(app_config, 'url', str)
        self._validate_required_field(app_config, 'owner', str)

        # Validate URL
        if 'url' in app_config:
            self._validate_url(app_config['url'])

        # Validate email
        if 'owner' in app_config:
            self._validate_email(app_config['owner'])

        # Validate criticality
        if 'criticality' in app_config:
            self._validate_enum(app_config['criticality'], ['critical', 'high', 'medium', 'low'])

        # Validate scan configuration
        if 'scan' in app_config:
            self._validate_scan_config(app_config['scan'])

        # Validate notifications
        if 'notifications' in app_config:
            self._validate_notifications_config(app_config['notifications'])

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings

    def _validate_required_field(self, config: Dict, field: str, expected_type: type) -> bool:
        """Validate that a required field exists and has the correct type"""
        if field not in config:
            self.errors.append(f"Required field '{field}' is missing")
            return False

        if not isinstance(config[field], expected_type):
            self.errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
            return False

        return True

    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                self.errors.append(f"Invalid URL format: {url}")
                return False

            if result.scheme not in ['http', 'https']:
                self.errors.append(f"URL scheme must be http or https: {url}")
                return False

            return True
        except Exception as e:
            self.errors.append(f"Invalid URL: {url} - {str(e)}")
            return False

    def _validate_email(self, email: str) -> bool:
        """Basic email validation"""
        if '@' not in email or '.' not in email.split('@')[1]:
            self.errors.append(f"Invalid email format: {email}")
            return False
        return True

    def _validate_enum(self, value: str, allowed_values: List[str]) -> bool:
        """Validate that value is in allowed list"""
        if value not in allowed_values:
            self.errors.append(f"Value '{value}' must be one of: {', '.join(allowed_values)}")
            return False
        return True

    def _validate_scan_config(self, scan_config: Dict[str, Any]) -> bool:
        """Validate scan configuration"""
        # Validate scan type
        if 'type' in scan_config:
            self._validate_enum(scan_config['type'], ['full', 'quick', 'incremental'])

        # Validate timeout
        if 'timeout' in scan_config:
            if not isinstance(scan_config['timeout'], int) or scan_config['timeout'] <= 0:
                self.errors.append("Scan timeout must be a positive integer")

        # Validate schedule (cron format)
        if 'schedule' in scan_config:
            self._validate_cron_schedule(scan_config['schedule'])

        # Validate thresholds
        if 'thresholds' in scan_config:
            self._validate_thresholds(scan_config['thresholds'])

        # Validate authentication
        if 'authentication' in scan_config:
            auth_config = scan_config['authentication']
            if auth_config.get('enabled'):
                if 'type' in auth_config:
                    self._validate_enum(
                        auth_config['type'],
                        ['form', 'oauth', 'api_key', 'basic', 'session']
                    )

        return len(self.errors) == 0

    def _validate_cron_schedule(self, schedule: str) -> bool:
        """Validate cron schedule format"""
        parts = schedule.split()
        if len(parts) != 5:
            self.errors.append(f"Invalid cron schedule format: {schedule}. Expected 5 fields.")
            return False

        # Basic validation (could be more thorough)
        for i, part in enumerate(parts):
            if part not in ['*', '*/']:
                # Check if it's a number or range
                if not any(c in part for c in [',', '-', '/']) and not part.isdigit():
                    self.warnings.append(f"Potentially invalid cron schedule: {schedule}")
                    break

        return True

    def _validate_thresholds(self, thresholds: Dict[str, Any]) -> bool:
        """Validate vulnerability thresholds"""
        valid_severities = ['critical', 'high', 'medium', 'low', 'info']

        for severity, value in thresholds.items():
            if severity not in valid_severities:
                self.warnings.append(f"Unknown severity level in thresholds: {severity}")

            if value is not None and (not isinstance(value, int) or value < 0):
                self.errors.append(f"Threshold for '{severity}' must be null or a non-negative integer")

        return len(self.errors) == 0

    def _validate_notifications_config(self, notifications_config: Dict[str, Any]) -> bool:
        """Validate notifications configuration"""
        # Validate email
        if 'email' in notifications_config:
            email_config = notifications_config['email']
            if isinstance(email_config, dict) and 'recipients' in email_config:
                recipients = email_config['recipients']
                if not isinstance(recipients, list):
                    self.errors.append("Email recipients must be a list")
                else:
                    for recipient in recipients:
                        self._validate_email(recipient)

        # Validate Slack
        if 'slack' in notifications_config:
            slack_config = notifications_config['slack']
            if isinstance(slack_config, dict) and slack_config.get('enabled'):
                if 'channel' not in slack_config:
                    self.warnings.append("Slack enabled but no channel specified")

        # Validate GitHub
        if 'github' in notifications_config:
            github_config = notifications_config['github']
            if isinstance(github_config, dict) and github_config.get('enabled'):
                if 'issue_severity' in github_config:
                    for severity in github_config['issue_severity']:
                        self._validate_enum(
                            severity,
                            ['critical', 'high', 'medium', 'low', 'info']
                        )

        return len(self.errors) == 0

    def validate_scan_policy(self, policy: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate scan policy configuration

        Args:
            policy: Policy dictionary to validate

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []

        if 'policy' not in policy:
            self.errors.append("Missing 'policy' section in scan policy")
            return False, self.errors, self.warnings

        policy_config = policy['policy']

        # Validate required fields
        self._validate_required_field(policy_config, 'name', str)

        # Validate spider config
        if 'spider' in policy_config:
            spider = policy_config['spider']
            if not isinstance(spider.get('enabled'), bool):
                self.errors.append("spider.enabled must be a boolean")

        # Validate active scan config
        if 'active_scan' in policy_config:
            active_scan = policy_config['active_scan']
            if not isinstance(active_scan.get('enabled'), bool):
                self.errors.append("active_scan.enabled must be a boolean")

            if 'intensity' in active_scan:
                self._validate_enum(active_scan['intensity'], ['low', 'medium', 'high'])

        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
