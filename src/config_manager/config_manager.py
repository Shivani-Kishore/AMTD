"""
Configuration Manager
Main class for configuration management
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from .config_loader import ConfigLoader
from .config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Main configuration manager class
    Provides high-level interface for configuration operations
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the ConfigManager

        Args:
            config_dir: Base directory for configuration files
        """
        self.loader = ConfigLoader(config_dir)
        self.validator = ConfigValidator()
        self._config_cache = {}

    def get_application_config(
        self,
        app_name: str,
        environment: Optional[str] = None,
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Get complete configuration for an application

        Args:
            app_name: Application name
            environment: Environment name (optional)
            validate: Whether to validate the configuration

        Returns:
            Complete merged and validated configuration

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If configuration file doesn't exist
        """
        # Check cache
        cache_key = f"{app_name}_{environment or 'default'}"
        if cache_key in self._config_cache:
            logger.debug(f"Using cached configuration for {cache_key}")
            return self._config_cache[cache_key]

        # Load configuration
        config = self.loader.load_complete_config(app_name, environment)

        # Validate if requested
        if validate:
            is_valid, errors, warnings = self.validator.validate_application_config(config)

            # Log warnings
            for warning in warnings:
                logger.warning(f"Configuration warning for '{app_name}': {warning}")

            # Raise error if invalid
            if not is_valid:
                error_msg = f"Invalid configuration for '{app_name}':\n" + "\n".join(errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

        # Cache the configuration
        self._config_cache[cache_key] = config

        return config

    def get_scan_policy(self, policy_name: str, validate: bool = True) -> Dict[str, Any]:
        """
        Get scan policy configuration

        Args:
            policy_name: Policy name
            validate: Whether to validate the policy

        Returns:
            Scan policy configuration

        Raises:
            ValueError: If policy is invalid
        """
        policy = self.loader.load_scan_policy(policy_name)

        if validate:
            is_valid, errors, warnings = self.validator.validate_scan_policy(policy)

            for warning in warnings:
                logger.warning(f"Policy warning for '{policy_name}': {warning}")

            if not is_valid:
                error_msg = f"Invalid scan policy '{policy_name}':\n" + "\n".join(errors)
                logger.error(error_msg)
                raise ValueError(error_msg)

        return policy

    def list_applications(self) -> List[str]:
        """
        List all available application configurations

        Returns:
            List of application names
        """
        return self.loader.list_applications()

    def list_policies(self) -> List[str]:
        """
        List all available scan policies

        Returns:
            List of policy names
        """
        return self.loader.list_policies()

    def validate_application(self, app_name: str, environment: Optional[str] = None) -> Tuple[bool, List[str], List[str]]:
        """
        Validate an application configuration

        Args:
            app_name: Application name
            environment: Environment name (optional)

        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        try:
            config = self.loader.load_complete_config(app_name, environment)
            return self.validator.validate_application_config(config)
        except Exception as e:
            logger.error(f"Error validating application '{app_name}': {e}")
            return False, [str(e)], []

    def validate_all_applications(self) -> Dict[str, Tuple[bool, List[str], List[str]]]:
        """
        Validate all application configurations

        Returns:
            Dictionary mapping application names to validation results
        """
        results = {}
        applications = self.list_applications()

        for app_name in applications:
            logger.info(f"Validating configuration for '{app_name}'")
            results[app_name] = self.validate_application(app_name)

        return results

    def clear_cache(self):
        """Clear the configuration cache"""
        self._config_cache = {}
        logger.info("Configuration cache cleared")

    def get_scan_config(self, app_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get scan-specific configuration for an application

        Args:
            app_name: Application name
            environment: Environment name (optional)

        Returns:
            Scan configuration dictionary
        """
        config = self.get_application_config(app_name, environment)
        return config.get('application', {}).get('scan', {})

    def get_notification_config(self, app_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Get notification configuration for an application

        Args:
            app_name: Application name
            environment: Environment name (optional)

        Returns:
            Notification configuration dictionary
        """
        config = self.get_application_config(app_name, environment)
        return config.get('application', {}).get('notifications', {})

    def get_target_url(self, app_name: str, environment: Optional[str] = None) -> str:
        """
        Get target URL for an application

        Args:
            app_name: Application name
            environment: Environment name (optional)

        Returns:
            Target URL string
        """
        config = self.get_application_config(app_name, environment)
        return config.get('application', {}).get('url', '')

    def get_thresholds(self, app_name: str, environment: Optional[str] = None) -> Dict[str, Optional[int]]:
        """
        Get vulnerability thresholds for an application

        Args:
            app_name: Application name
            environment: Environment name (optional)

        Returns:
            Dictionary of severity thresholds
        """
        scan_config = self.get_scan_config(app_name, environment)
        return scan_config.get('thresholds', {
            'critical': 0,
            'high': 5,
            'medium': 20,
            'low': None,
            'info': None
        })
