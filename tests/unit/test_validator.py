"""Unit tests for validator.py module."""

import pytest
import os
import tempfile
import json
import yaml

from tools.validator import (
    validate_daily_file, load_allowlist, validate_inputs,
    ValidationResult, ValidationError, Allowlist, AllowlistEntry,
    get_current_environment
)


def test_load_allowlist():
    """Load allowlist from YAML file."""
    allowlist = load_allowlist("tests/fixtures/test-allowlist.yaml")
    
    assert isinstance(allowlist, Allowlist)
    assert allowlist.is_allowed("test-action")
    assert not allowlist.is_allowed("nonexistent-action")


def test_load_allowlist_file_not_found():
    """Should raise FileNotFoundError for missing allowlist."""
    with pytest.raises(FileNotFoundError):
        load_allowlist("nonexistent.yaml")


def test_allowlist_entry_properties():
    """AllowlistEntry should have all required properties."""
    allowlist = load_allowlist("tests/fixtures/test-allowlist.yaml")
    entry = allowlist.get_entry("test-action")
    
    assert entry is not None
    assert entry.script == "tests/fixtures/mock-success.py"
    assert entry.version == "1.0"
    assert entry.schema == "tests/fixtures/test-schema.json"
    assert entry.timeout == 10
    assert entry.environment == "any"


def test_allowlist_validate_version():
    """Should validate version matches allowlist."""
    allowlist = load_allowlist("tests/fixtures/test-allowlist.yaml")
    
    assert allowlist.validate_version("test-action", "1.0") is True
    assert allowlist.validate_version("test-action", "2.0") is False
    assert allowlist.validate_version("nonexistent", "1.0") is False


def test_allowlist_entry_can_run_in_environment():
    """AllowlistEntry should check environment constraints."""
    entry_any = AllowlistEntry(
        script="test.py",
        version="1.0",
        schema="test.json",
        environment="any"
    )
    entry_ci = AllowlistEntry(
        script="test.py",
        version="1.0",
        schema="test.json",
        environment="ci-only"
    )
    entry_local = AllowlistEntry(
        script="test.py",
        version="1.0",
        schema="test.json",
        environment="local-only"
    )
    
    # "any" can run in both environments
    assert entry_any.can_run_in_environment("ci") is True
    assert entry_any.can_run_in_environment("local") is True
    
    # "ci-only" can only run in CI
    assert entry_ci.can_run_in_environment("ci") is True
    assert entry_ci.can_run_in_environment("local") is False
    
    # "local-only" can only run locally
    assert entry_local.can_run_in_environment("ci") is False
    assert entry_local.can_run_in_environment("local") is True


def test_validate_inputs_valid():
    """Should validate valid inputs against schema."""
    inputs = {
        "ticket": "PROJ-123",
        "comment": "Test comment"
    }
    errors = validate_inputs(inputs, "tests/fixtures/test-schema.json")
    assert errors == []


def test_validate_inputs_missing_required_field():
    """Should detect missing required field."""
    inputs = {
        "comment": "Test comment"
        # Missing "ticket" field
    }
    errors = validate_inputs(inputs, "tests/fixtures/test-schema.json")
    assert len(errors) > 0
    assert "ticket" in errors[0] or "'ticket' is a required property" in errors[0]


def test_validate_inputs_invalid_pattern():
    """Should detect invalid field pattern."""
    inputs = {
        "ticket": "invalid-format",  # Should be PROJ-123 format
        "comment": "Test comment"
    }
    errors = validate_inputs(inputs, "tests/fixtures/test-schema.json")
    assert len(errors) > 0


def test_validate_inputs_additional_properties():
    """Should detect additional properties when not allowed."""
    inputs = {
        "ticket": "PROJ-123",
        "comment": "Test comment",
        "extra_field": "not allowed"
    }
    errors = validate_inputs(inputs, "tests/fixtures/test-schema.json")
    assert len(errors) > 0
    assert "additional" in errors[0].lower() or "extra_field" in errors[0]


def test_validate_inputs_schema_not_found():
    """Should raise FileNotFoundError for missing schema."""
    inputs = {"ticket": "PROJ-123"}
    with pytest.raises(FileNotFoundError):
        validate_inputs(inputs, "schemas/nonexistent.json")


def test_validate_daily_file_valid():
    """Should validate a valid daily file."""
    result = validate_daily_file(
        file_path="tests/fixtures/sample-day-pending.md",
        allowlist_path="tests/fixtures/test-allowlist.yaml",
        schemas_dir="tests/fixtures/",
        mode="pr"
    )
    
    assert result.is_valid is True
    assert len(result.errors) == 0
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_daily_file_action_not_in_allowlist():
    """Should detect action not in allowlist."""
    # Create a temporary daily file with invalid action
    content = """- [ ] `a1` — *invalid-action* v1.0
```yaml
inputs:
  test: "value"
outputs: {}
meta: {}
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="pr"
        )
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any(e.error_type == "allowlist" for e in result.errors)
        assert any("invalid-action" in e.message for e in result.errors)
    finally:
        os.unlink(temp_file)


def test_validate_daily_file_version_mismatch():
    """Should detect version mismatch."""
    content = """- [ ] `a1` — *test-action* v2.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test"
outputs: {}
meta: {}
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="pr"
        )
        
        assert result.is_valid is False
        assert any(e.error_type == "version" for e in result.errors)
    finally:
        os.unlink(temp_file)


def test_validate_daily_file_schema_validation_fails():
    """Should detect schema validation errors."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: "invalid"
  comment: "Test"
outputs: {}
meta: {}
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="pr"
        )
        
        assert result.is_valid is False
        assert any(e.error_type == "schema" for e in result.errors)
    finally:
        os.unlink(temp_file)


def test_validate_daily_file_checked_action_in_pr_mode():
    """Should reject checked actions in PR mode (immutability)."""
    content = """- [x] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Already executed"
outputs:
  commentUrl: "https://example.com"
meta:
  executedAt: "2026-01-15T14:32:11Z"
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="pr"
        )
        
        assert result.is_valid is False
        assert any(e.error_type == "immutability" for e in result.errors)
    finally:
        os.unlink(temp_file)


def test_validate_daily_file_checked_action_in_execution_mode():
    """Should allow checked actions in execution mode."""
    content = """- [x] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Already executed"
outputs:
  commentUrl: "https://example.com"
meta:
  executedAt: "2026-01-15T14:32:11Z"
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="execution"
        )
        
        assert result.is_valid is True
        assert not any(e.error_type == "immutability" for e in result.errors)
    finally:
        os.unlink(temp_file)


def test_validate_daily_file_multiple_errors():
    """Should collect all errors, not stop at first one."""
    content = """- [ ] `a1` — *invalid-action* v1.0
```yaml
inputs:
  test: "value"
outputs: {}
meta: {}
```

- [ ] `a2` — *test-action* v2.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test"
outputs: {}
meta: {}
```
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        result = validate_daily_file(
            file_path=temp_file,
            allowlist_path="tests/fixtures/test-allowlist.yaml",
            schemas_dir="tests/fixtures/",
            mode="pr"
        )
        
        assert result.is_valid is False
        # Should have at least 2 errors (allowlist + version)
        assert len(result.errors) >= 2
    finally:
        os.unlink(temp_file)


def test_validation_result_to_dict():
    """ValidationResult should serialize to dictionary."""
    result = ValidationResult(
        is_valid=False,
        errors=[
            ValidationError(
                action_id="a1",
                error_type="schema",
                message="Test error",
                line_number=42
            )
        ],
        warnings=["Test warning"],
        file_path="test.md"
    )
    
    data = result.to_dict()
    assert data["is_valid"] is False
    assert data["file_path"] == "test.md"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["action_id"] == "a1"
    assert data["errors"][0]["error_type"] == "schema"
    assert len(data["warnings"]) == 1


def test_validation_result_print_report(capsys):
    """ValidationResult should print readable report."""
    result = ValidationResult(
        is_valid=True,
        file_path="test.md"
    )
    
    result.print_report()
    captured = capsys.readouterr()
    assert "✅" in captured.out or "valid" in captured.out.lower()


def test_get_current_environment_ci():
    """Should detect CI environment."""
    os.environ["CI"] = "true"
    env = get_current_environment()
    assert env == "ci"


def test_get_current_environment_local():
    """Should detect local environment."""
    if "CI" in os.environ:
        del os.environ["CI"]
    env = get_current_environment()
    assert env == "local"
