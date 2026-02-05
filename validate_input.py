"""
Input validation utilities for the flaky test detector.
Validates configuration against the JSON schema.
"""

import json
import os
from typing import Any

try:
    from jsonschema import Draft7Validator, ValidationError

    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # Fallback type
    Draft7Validator = None  # type: ignore[misc,assignment]


def load_schema() -> dict[str, Any]:
    """Load the input JSON schema."""
    schema_path = os.path.join(os.path.dirname(__file__), "input_schema.json")
    with open(schema_path) as f:
        return json.load(f)


def validate_input(
    config: dict[str, Any], schema_path: str | None = None
) -> tuple[bool, list[str]]:
    """
    Validate input configuration against the schema.

    Args:
        config: The configuration dictionary to validate
        schema_path: Optional path to schema file (uses default if not provided)

    Returns:
        Tuple of (is_valid, errors) where errors is a list of error messages
    """
    if not JSONSCHEMA_AVAILABLE:
        # If jsonschema is not installed, do basic validation
        return _basic_validation(config)

    try:
        if schema_path:
            with open(schema_path) as f:
                schema = json.load(f)
        else:
            schema = load_schema()

        validator = Draft7Validator(schema)
        errors = []

        for error in validator.iter_errors(config):
            # Format error messages to be user-friendly
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        return (len(errors) == 0, errors)

    except FileNotFoundError as e:
        return (False, [f"Schema file not found: {e}"])
    except json.JSONDecodeError as e:
        return (False, [f"Invalid JSON in schema: {e}"])
    except Exception as e:
        return (False, [f"Validation error: {e}"])


def _basic_validation(config: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Basic validation when jsonschema is not available.
    Checks required fields and basic constraints.
    """
    errors = []

    # Check required fields
    if "repo" not in config:
        errors.append("Missing required field: repo")
    elif not isinstance(config["repo"], str) or not config["repo"]:
        errors.append("repo must be a non-empty string")

    if "test_command" not in config:
        errors.append("Missing required field: test_command")
    elif not isinstance(config["test_command"], str) or not config["test_command"]:
        errors.append("test_command must be a non-empty string")

    # Check optional fields if present
    if "runs" in config:
        if not isinstance(config["runs"], int):
            errors.append("runs must be an integer")
        elif config["runs"] < 1 or config["runs"] > 1000:
            errors.append("runs must be between 1 and 1000")

    if "parallelism" in config:
        if not isinstance(config["parallelism"], int):
            errors.append("parallelism must be an integer")
        elif config["parallelism"] < 1 or config["parallelism"] > 50:
            errors.append("parallelism must be between 1 and 50")

    if "framework" in config:
        valid_frameworks = [
            "python",
            "go",
            "typescript-jest",
            "typescript-vitest",
            "javascript-mocha",
        ]
        if not isinstance(config["framework"], str):
            errors.append("framework must be a string")
        elif config["framework"] not in valid_frameworks:
            errors.append(f"framework must be one of: {', '.join(valid_frameworks)}")

    return (len(errors) == 0, errors)


def validate_and_report(config: dict[str, Any], config_file: str = "config") -> bool:
    """
    Validate configuration and print user-friendly error messages.

    Args:
        config: Configuration to validate
        config_file: Name of config file for error messages

    Returns:
        True if valid, False otherwise
    """
    is_valid, errors = validate_input(config)

    if not is_valid:
        print(f"❌ Invalid configuration in {config_file}:")
        print()
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")
        print()
        print("💡 See input_schema.json for the complete configuration specification")
        return False

    return True
