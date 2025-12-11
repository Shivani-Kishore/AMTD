#!/usr/bin/env python3
"""
Enhanced Configuration Validator
Validates AMTD configuration files
"""

import sys
import logging
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config_manager import ConfigManager, ConfigValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_configuration(config_type: str, config_file: str, verbose: bool = False) -> bool:
    """
    Validate configuration file

    Args:
        config_type: Type of configuration (application, policy, global)
        config_file: Path to configuration file
        verbose: Verbose output

    Returns:
        True if valid
    """
    try:
        validator = ConfigValidator()

        logger.info(f"Validating {config_type} configuration: {config_file}")

        if config_type == 'application':
            # Validate application configuration
            errors, warnings = validator.validate_application_config(config_file)

        elif config_type == 'policy':
            # Load and basic validate scan policy
            import yaml
            with open(config_file, 'r') as f:
                policy_config = yaml.safe_load(f)

            errors = []
            warnings = []

            # Basic validation
            required_fields = ['spider', 'active_scan']
            for field in required_fields:
                if field not in policy_config:
                    errors.append(f"Missing required section: {field}")

            logger.info(f"Policy configuration validated (basic check)")

        elif config_type == 'global':
            # Load and validate global configuration
            import yaml
            with open(config_file, 'r') as f:
                global_config = yaml.safe_load(f)

            errors = []
            warnings = []

            # Basic validation
            required_sections = ['logging', 'database', 'scanning']
            for section in required_sections:
                if section not in global_config:
                    errors.append(f"Missing required section: {section}")

            logger.info(f"Global configuration validated (basic check)")

        else:
            logger.error(f"Unknown configuration type: {config_type}")
            return False

        # Report results
        if errors:
            logger.error(f"Validation FAILED with {len(errors)} errors:")
            for error in errors:
                logger.error(f"  ERROR: {error}")

        if warnings:
            logger.warning(f"Found {len(warnings)} warnings:")
            for warning in warnings:
                logger.warning(f"  WARNING: {warning}")

        if not errors and not warnings:
            logger.info("Configuration is VALID - no errors or warnings")

        if verbose:
            # Show full configuration
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            logger.info("Configuration content:")
            logger.info(yaml.dump(config, default_flow_style=False))

        return len(errors) == 0

    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        return False
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


def validate_all_applications(config_dir: str) -> bool:
    """
    Validate all application configurations

    Args:
        config_dir: Configuration directory

    Returns:
        True if all valid
    """
    try:
        config_path = Path(config_dir) / 'applications'

        if not config_path.exists():
            logger.error(f"Applications directory not found: {config_path}")
            return False

        # Get all YAML files
        yaml_files = list(config_path.glob('*.yaml')) + list(config_path.glob('*.yml'))

        logger.info(f"Found {len(yaml_files)} application configuration files")

        all_valid = True
        for yaml_file in yaml_files:
            if yaml_file.name == 'template.yaml':
                continue  # Skip template

            logger.info(f"\n{'='*60}")
            logger.info(f"Validating: {yaml_file.name}")
            logger.info(f"{'='*60}")

            valid = validate_configuration('application', str(yaml_file))
            if not valid:
                all_valid = False

        logger.info(f"\n{'='*60}")
        if all_valid:
            logger.info("ALL configurations are VALID")
        else:
            logger.error("Some configurations have ERRORS")
        logger.info(f"{'='*60}")

        return all_valid

    except Exception as e:
        logger.error(f"Failed to validate all applications: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Validate AMTD configuration files')
    parser.add_argument(
        '--type',
        '-t',
        choices=['application', 'policy', 'global'],
        help='Configuration type'
    )
    parser.add_argument('--file', '-f', help='Configuration file to validate')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all applications')
    parser.add_argument('--config-dir', '-d', default='config', help='Configuration directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.all:
        # Validate all applications
        success = validate_all_applications(args.config_dir)
    elif args.type and args.file:
        # Validate specific file
        success = validate_configuration(args.type, args.file, args.verbose)
    else:
        parser.error("Either --all or both --type and --file are required")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
