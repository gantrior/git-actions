"""Validator for action entries against allowlist and JSON schemas.

This module provides functionality to validate action entries in daily files
against the allowlist configuration and JSON schemas for input validation.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml
from jsonschema import ValidationError as SchemaValidationError
from jsonschema import validate as json_validate

from tools.parser import ParseError, parse_daily_file


@dataclass
class AllowlistEntry:
    """Configuration for a single action type in the allowlist.

    Attributes:
        script: Path to action script
        version: Expected version
        schema: Path to JSON schema for input validation
        timeout: Timeout in seconds (default 300)
        environment: Environment constraint (any, ci-only, local-only)
    """

    script: str
    version: str
    schema: str
    timeout: int = 300
    environment: str = "any"

    def can_run_in_environment(self, current_env: str) -> bool:
        """Check if action can run in the current environment.

        Args:
            current_env: Current environment ("ci" or "local")

        Returns:
            True if action can run, False otherwise
        """
        if self.environment == "any":
            return True
        elif self.environment == "ci-only":
            return current_env == "ci"
        elif self.environment == "local-only":
            return current_env == "local"
        return False


@dataclass
class Allowlist:
    """Parsed allowlist configuration.

    Attributes:
        entries: Map of action name to allowlist entry
    """

    entries: Dict[str, AllowlistEntry] = field(default_factory=dict)

    def get_entry(self, action_name: str) -> Optional[AllowlistEntry]:
        """Get allowlist entry for action type.

        Args:
            action_name: Name of action type

        Returns:
            AllowlistEntry if found, None otherwise
        """
        return self.entries.get(action_name)

    def is_allowed(self, action_name: str) -> bool:
        """Check if action type is in allowlist.

        Args:
            action_name: Name of action type

        Returns:
            True if action is allowed, False otherwise
        """
        return action_name in self.entries

    def validate_version(self, action_name: str, version: str) -> bool:
        """Check if version matches allowlist version.

        Args:
            action_name: Name of action type
            version: Version from action entry

        Returns:
            True if version matches, False otherwise
        """
        entry = self.get_entry(action_name)
        if entry is None:
            return False
        return entry.version == version


@dataclass
class ValidationError:
    """Represents a single validation failure.

    Attributes:
        action_id: ID of action that failed validation
        error_type: Category of error
        message: Human-readable error description
        line_number: Line number in file where error occurred
    """

    action_id: str
    error_type: str
    message: str
    line_number: Optional[int] = None

    def __str__(self) -> str:
        """Format error as human-readable string."""
        location = f" (line {self.line_number})" if self.line_number else ""
        return f"  Action '{self.action_id}'{location}\n    [{self.error_type}] {self.message}"


@dataclass
class ValidationResult:
    """Result of validating a daily file.

    Attributes:
        is_valid: True if all validations passed
        errors: List of validation errors
        warnings: Non-critical warnings
        file_path: Path to file that was validated
    """

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    file_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize validation result to dictionary.

        Returns:
            Dictionary representation of validation result
        """
        return {
            "is_valid": self.is_valid,
            "file_path": self.file_path,
            "errors": [
                {
                    "action_id": err.action_id,
                    "error_type": err.error_type,
                    "message": err.message,
                    "line_number": err.line_number,
                }
                for err in self.errors
            ],
            "warnings": self.warnings,
        }

    def print_report(self) -> None:
        """Print human-readable validation report."""
        if self.is_valid:
            print("✅ All actions are valid")
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    print(f"  ⚠️  {warning}")
        else:
            print("❌ Validation failed:")
            if self.file_path:
                print(f"\n{self.file_path}:")
            for error in self.errors:
                print(str(error))
            if self.warnings:
                print("\nWarnings:")
                for warning in self.warnings:
                    print(f"  ⚠️  {warning}")


def load_allowlist(allowlist_path: str) -> Allowlist:
    """Load and parse allowlist YAML file.

    Args:
        allowlist_path: Path to allowlist.yaml

    Returns:
        Allowlist object with parsed configuration

    Raises:
        FileNotFoundError: Allowlist file not found
        yaml.YAMLError: Malformed YAML
    """
    if not os.path.exists(allowlist_path):
        raise FileNotFoundError(f"Allowlist file not found: {allowlist_path}")

    with open(allowlist_path) as f:
        data = yaml.safe_load(f)

    # Handle empty allowlist
    if data is None:
        return Allowlist(entries={})

    if not isinstance(data, dict):
        raise ValueError(f"Allowlist must be a dictionary, got {type(data)}")

    # Parse each allowlist entry
    entries = {}
    for action_name, config in data.items():
        if not isinstance(config, dict):
            raise ValueError(f"Allowlist entry for '{action_name}' must be a dictionary")

        entry = AllowlistEntry(
            script=config.get("script", ""),
            version=config.get("version", ""),
            schema=config.get("schema", ""),
            timeout=config.get("timeout", 300),
            environment=config.get("environment", "any"),
        )
        entries[action_name] = entry

    return Allowlist(entries=entries)


def validate_inputs(inputs: Dict[str, Any], schema_path: str) -> List[str]:
    """Validate action inputs against JSON schema.

    Args:
        inputs: Dictionary of input parameters
        schema_path: Path to JSON Schema file

    Returns:
        List of error messages (empty if valid)

    Raises:
        FileNotFoundError: Schema file not found
        json.JSONDecodeError: Malformed JSON schema
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path) as f:
        schema = json.load(f)

    errors = []
    try:
        json_validate(instance=inputs, schema=schema)
    except SchemaValidationError as e:
        # Convert jsonschema errors to human-readable messages
        path_str = ".".join(str(p) for p in e.path) if e.path else "root"
        errors.append(f"{e.message} at {path_str}")

    return errors


def get_current_environment() -> str:
    """Detect if running in CI or locally.

    Returns:
        "ci" if running in CI environment, "local" otherwise
    """
    if os.environ.get("CI") == "true":
        return "ci"
    else:
        return "local"


def validate_daily_file(
    file_path: str,
    allowlist_path: str,
    schemas_dir: str,
    mode: str = "pr",
    file_changed: bool = True,
    modified_checked_actions: Optional[set] = None,
) -> ValidationResult:
    """Validate all actions in a daily file.

    Args:
        file_path: Path to daily markdown file to validate
        allowlist_path: Path to allowlist YAML file
        schemas_dir: Directory containing JSON schemas
        mode: Validation mode - "pr" (strict) or "execution" (lenient)
        file_changed: Whether the file was modified in the PR. If False,
            immutability checks are skipped for checked actions since
            unchanged files should not trigger immutability errors.
        modified_checked_actions: Set of action IDs that are checked and
            were modified compared to the base branch. If provided, only
            these actions will trigger immutability errors. If None,
            falls back to file_changed behavior for backward compatibility.

    Returns:
        ValidationResult object with validation status and errors

    Raises:
        FileNotFoundError: File or allowlist not found
        ParseError: Malformed daily file
    """
    # Parse daily file
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Daily file not found: {file_path}")

    with open(file_path) as f:
        content = f.read()

    try:
        actions = parse_daily_file(content, filename=file_path)
    except ParseError as e:
        # Treat parse errors as validation errors
        return ValidationResult(
            is_valid=False,
            errors=[
                ValidationError(
                    action_id="(parse error)",
                    error_type="format",
                    message=str(e),
                    line_number=e.line_number,
                )
            ],
            file_path=file_path,
        )

    # Load allowlist
    allowlist = load_allowlist(allowlist_path)

    # Get current environment for constraint checking
    current_env = get_current_environment()

    # Validate each action
    errors = []
    warnings = []

    for action in actions:
        # Check if action name is in allowlist
        if not allowlist.is_allowed(action.name):
            errors.append(
                ValidationError(
                    action_id=action.id,
                    error_type="allowlist",
                    message=f"Action type '{action.name}' is not in the allowlist",
                    line_number=action.line_number,
                )
            )
            continue  # Can't validate further without allowlist entry

        # Get allowlist entry
        entry = allowlist.get_entry(action.name)

        # Check version match
        if not allowlist.validate_version(action.name, action.version):
            errors.append(
                ValidationError(
                    action_id=action.id,
                    error_type="version",
                    message=f"Version mismatch: action has v{action.version}, allowlist expects v{entry.version}",
                    line_number=action.line_number,
                )
            )

        # Check environment constraints
        if not entry.can_run_in_environment(current_env):
            # In execution mode, this is just a warning (action will be skipped)
            # In PR mode, we still validate the action format
            warnings.append(
                f"Action '{action.id}' has environment constraint '{entry.environment}' "
                f"and will be skipped in {current_env} environment"
            )

        # Validate inputs against schema
        # Try schema path as-is first (relative from project root)
        schema_path = entry.schema
        if not os.path.exists(schema_path):
            # Fallback: try in schemas_dir if it's just a filename
            schema_path = os.path.join(schemas_dir, os.path.basename(entry.schema))

        try:
            input_errors = validate_inputs(action.inputs, schema_path)
            for error_msg in input_errors:
                errors.append(
                    ValidationError(
                        action_id=action.id,
                        error_type="schema",
                        message=error_msg,
                        line_number=action.line_number,
                    )
                )
        except FileNotFoundError:
            errors.append(
                ValidationError(
                    action_id=action.id,
                    error_type="schema",
                    message=f"Schema file not found: {entry.schema}",
                    line_number=action.line_number,
                )
            )
        except json.JSONDecodeError as e:
            errors.append(
                ValidationError(
                    action_id=action.id,
                    error_type="schema",
                    message=f"Invalid JSON schema: {str(e)}",
                    line_number=action.line_number,
                )
            )

        # Check immutability in PR mode
        # If modified_checked_actions is provided, only flag actions in that set
        # Otherwise, fall back to file_changed behavior for backward compatibility
        if mode == "pr" and action.is_checked:
            should_flag = False
            if modified_checked_actions is not None:
                # New behavior: only flag if this action was actually modified
                should_flag = action.id in modified_checked_actions
            elif file_changed:
                # Legacy behavior: flag all checked actions in changed files
                should_flag = True

            if should_flag:
                errors.append(
                    ValidationError(
                        action_id=action.id,
                        error_type="immutability",
                        message="Cannot modify checked actions in PR. Checked actions are immutable.",
                        line_number=action.line_number,
                    )
                )

    # Build result
    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid, errors=errors, warnings=warnings, file_path=file_path
    )
