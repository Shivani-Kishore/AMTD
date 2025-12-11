"""
Configuration Loader
Loads and merges YAML configuration files with environment variable substitution
"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and processes YAML configuration files"""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the ConfigLoader

        Args:
            config_dir: Base directory for configuration files
        """
        self.config_dir = Path(config_dir)
        self.env_var_pattern = re.compile(r'\$\{([^}^{]+)\}')

    def load_yaml(self, file_path: str) -> Dict[str, Any]:
        """
        Load a YAML file

        Args:
            file_path: Path to the YAML file

        Returns:
            Dictionary containing the parsed YAML

        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Substitute environment variables
                content = self._substitute_env_vars(content)
                config = yaml.safe_load(content)
                logger.info(f"Loaded configuration from {file_path}")
                return config or {}
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {file_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            raise

    def _substitute_env_vars(self, content: str) -> str:
        """
        Substitute environment variables in the format ${VAR_NAME} or ${VAR_NAME:-default}

        Args:
            content: String content with environment variable placeholders

        Returns:
            Content with environment variables substituted
        """
        def replacer(match):
            var_spec = match.group(1)

            # Check for default value syntax: ${VAR:-default}
            if ':-' in var_spec:
                var_name, default_value = var_spec.split(':-', 1)
                return os.getenv(var_name.strip(), default_value.strip())
            else:
                var_name = var_spec.strip()
                value = os.getenv(var_name)
                if value is None:
                    logger.warning(f"Environment variable '{var_name}' not set, keeping placeholder")
                    return match.group(0)
                return value

        return self.env_var_pattern.sub(replacer, content)

    def load_global_config(self) -> Dict[str, Any]:
        """
        Load global configuration

        Returns:
            Global configuration dictionary
        """
        global_config_path = self.config_dir / "global.yaml"
        if global_config_path.exists():
            return self.load_yaml(str(global_config_path))
        else:
            logger.warning("Global configuration file not found, using empty config")
            return {}

    def load_environment_config(self, environment: str) -> Dict[str, Any]:
        """
        Load environment-specific configuration

        Args:
            environment: Environment name (development, staging, production)

        Returns:
            Environment-specific configuration dictionary
        """
        env_config_path = self.config_dir / "environments" / f"{environment}.yaml"
        if env_config_path.exists():
            return self.load_yaml(str(env_config_path))
        else:
            logger.info(f"No environment-specific config found for '{environment}'")
            return {}

    def load_application_config(self, app_name: str) -> Dict[str, Any]:
        """
        Load application-specific configuration

        Args:
            app_name: Application name or config file name (without .yaml)

        Returns:
            Application configuration dictionary

        Raises:
            FileNotFoundError: If application config doesn't exist
        """
        app_config_path = self.config_dir / "applications" / f"{app_name}.yaml"
        if not app_config_path.exists():
            raise FileNotFoundError(f"Application configuration not found: {app_config_path}")

        return self.load_yaml(str(app_config_path))

    def load_scan_policy(self, policy_name: str) -> Dict[str, Any]:
        """
        Load scan policy configuration

        Args:
            policy_name: Policy name (default, quick, passive-only, etc.)

        Returns:
            Scan policy configuration dictionary
        """
        policy_path = self.config_dir / "scan-policies" / f"{policy_name}.yaml"
        if not policy_path.exists():
            logger.warning(f"Scan policy '{policy_name}' not found, using default")
            policy_path = self.config_dir / "scan-policies" / "default.yaml"

        return self.load_yaml(str(policy_path))

    def merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge multiple configuration dictionaries
        Later configs override earlier ones

        Args:
            *configs: Variable number of configuration dictionaries

        Returns:
            Merged configuration dictionary
        """
        def deep_merge(base: Dict, override: Dict) -> Dict:
            """Recursively merge two dictionaries"""
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = {}
        for config in configs:
            if config:
                merged = deep_merge(merged, config)

        return merged

    def load_complete_config(self, app_name: str, environment: Optional[str] = None) -> Dict[str, Any]:
        """
        Load complete configuration by merging global, environment, and application configs

        Args:
            app_name: Application name
            environment: Environment name (defaults to ENVIRONMENT env var or 'development')

        Returns:
            Complete merged configuration
        """
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')

        logger.info(f"Loading complete configuration for app '{app_name}' in environment '{environment}'")

        # Load configurations in order of precedence (lowest to highest)
        global_config = self.load_global_config()
        env_config = self.load_environment_config(environment)
        app_config = self.load_application_config(app_name)

        # Merge configurations
        merged_config = self.merge_configs(global_config, env_config, app_config)

        # Load and merge scan policy if specified
        if 'scan' in merged_config.get('application', {}) and 'policy' in merged_config['application']['scan']:
            policy_name = merged_config['application']['scan']['policy']
            scan_policy = self.load_scan_policy(policy_name)
            # Merge scan policy into the scan configuration
            if 'application' in merged_config and 'scan' in merged_config['application']:
                merged_config['application']['scan']['policy_config'] = scan_policy.get('policy', {})

        logger.info(f"Configuration loaded successfully for '{app_name}'")
        return merged_config

    def list_applications(self) -> list:
        """
        List all available application configurations

        Returns:
            List of application names
        """
        app_dir = self.config_dir / "applications"
        if not app_dir.exists():
            return []

        apps = []
        for file_path in app_dir.glob("*.yaml"):
            if file_path.name != "template.yaml":
                apps.append(file_path.stem)

        return sorted(apps)

    def list_policies(self) -> list:
        """
        List all available scan policies

        Returns:
            List of policy names
        """
        policy_dir = self.config_dir / "scan-policies"
        if not policy_dir.exists():
            return []

        policies = []
        for file_path in policy_dir.glob("*.yaml"):
            policies.append(file_path.stem)

        return sorted(policies)
