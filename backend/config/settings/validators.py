"""
Environment Variable Validators for Production Settings

Validates that all required environment variables are properly configured
before the Django application starts. Fail-fast approach prevents silent
failures in production.
"""

import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing or invalid."""
    pass


def validate_required_env_vars() -> Tuple[bool, List[str]]:
    """
    Validates that all required environment variables are set.

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Core Django settings
    required_vars = {
        'SECRET_KEY': 'Django secret key for cryptographic signing',
        'ALLOWED_HOSTS': 'Comma-separated list of allowed hosts',
    }

    # Database settings (PostgreSQL required in production)
    db_vars = {
        'DB_NAME': 'PostgreSQL database name',
        'DB_USER': 'PostgreSQL database user',
        'DB_PASSWORD': 'PostgreSQL database password',
        'DB_HOST': 'PostgreSQL database host',
    }

    # GCP-specific settings (if using Cloud Run)
    gcp_vars = {
        'GCP_PROJECT_ID': 'Google Cloud Project ID',
    }

    # Optional but recommended
    recommended_vars = {
        'SENTRY_DSN': 'Sentry error tracking DSN',
        'GEMINI_API_KEY': 'Google Gemini API key for agent enhancement',
    }

    # Check required variables
    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if not value:
            errors.append(f"Missing required variable: {var_name} ({description})")
        elif var_name == 'SECRET_KEY' and (value == 'insecure-dev-key' or len(value) < 50):
            errors.append(f"Insecure SECRET_KEY detected - must be 50+ characters")

    # Check database variables
    for var_name, description in db_vars.items():
        value = os.getenv(var_name)
        if not value:
            errors.append(f"Missing database variable: {var_name} ({description})")

    # Check GCP variables (warning only)
    for var_name, description in gcp_vars.items():
        value = os.getenv(var_name)
        if not value:
            logger.warning(f"Missing GCP variable: {var_name} ({description})")

    # Check recommended variables (info only)
    for var_name, description in recommended_vars.items():
        value = os.getenv(var_name)
        if not value:
            logger.info(f"Optional variable not set: {var_name} ({description})")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_settings_security() -> Tuple[bool, List[str]]:
    """
    Validates security-related settings.

    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []

    # Check DEBUG mode
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    if debug_mode:
        warnings.append("WARNING: DEBUG=True in production is a security risk")

    # Check ALLOWED_HOSTS
    allowed_hosts = os.getenv('ALLOWED_HOSTS', '')
    if not allowed_hosts or allowed_hosts == '*':
        warnings.append("WARNING: ALLOWED_HOSTS not properly configured")

    # Check database connection
    db_host = os.getenv('DB_HOST', '')
    if db_host == 'localhost' or db_host == '127.0.0.1':
        warnings.append("INFO: Using localhost database (OK for development)")

    return len(warnings) == 0, warnings


def validate_production_environment():
    """
    Main validation function - runs all checks and fails fast if critical issues found.

    Raises:
        EnvironmentValidationError: If validation fails
    """
    logger.info("🔍 Validating production environment variables...")

    # Check required variables
    is_valid, errors = validate_required_env_vars()
    if not is_valid:
        error_message = "\n❌ Environment Validation FAILED:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(error_message)
        raise EnvironmentValidationError(error_message)

    # Check security settings
    is_secure, warnings = validate_settings_security()
    if warnings:
        warning_message = "\n⚠️  Security Warnings:\n" + "\n".join(f"  - {warning}" for warning in warnings)
        logger.warning(warning_message)

    logger.info("✅ Environment validation passed!")


if __name__ == '__main__':
    """Allow running validator standalone for testing."""
    try:
        validate_production_environment()
        print("✅ All validation checks passed!")
    except EnvironmentValidationError as e:
        print(f"❌ Validation failed:\n{e}")
        exit(1)
