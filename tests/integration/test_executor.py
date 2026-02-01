"""Integration tests for executor.py module."""

import os
import tempfile

import yaml

from tools.executor import (
    ActionResult,
    ExecutionReport,
    execute_action_script,
    execute_actions_from_file,
)


def test_execute_action_script_success():
    """Should execute script and return success result."""
    script_path = "tests/fixtures/mock-success.py"
    action_data = {"action": "test-action", "version": "1.0", "inputs": {"test": "value"}}

    result = execute_action_script(script_path, action_data, timeout=10)

    assert result["status"] == "success"
    assert "result" in result["outputs"]
    assert result["error"] is None


def test_execute_action_script_failure():
    """Should execute script and return error result."""
    script_path = "tests/fixtures/mock-failure.py"
    action_data = {"action": "test-action", "version": "1.0", "inputs": {"test": "value"}}

    result = execute_action_script(script_path, action_data, timeout=10)

    assert result["status"] == "error"
    assert result["outputs"] == {}
    assert result["error"] is not None
    assert "simulated error" in result["error"]


def test_execute_action_script_timeout():
    """Should handle script timeout."""
    # Create a script that sleeps longer than timeout
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("#!/usr/bin/env python3\nimport time\ntime.sleep(10)\n")
        temp_script = f.name

    os.chmod(temp_script, 0o755)

    try:
        action_data = {"action": "test", "version": "1.0", "inputs": {}}
        result = execute_action_script(temp_script, action_data, timeout=1)

        assert result["status"] == "error"
        assert "Timeout" in result["error"]
    finally:
        os.unlink(temp_script)


def test_execute_action_script_not_found():
    """Should handle script not found."""
    result = execute_action_script("nonexistent.py", {}, timeout=10)

    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


def test_execute_action_script_invalid_json_output():
    """Should handle invalid JSON output from script."""
    # Create a script that outputs invalid JSON
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("#!/usr/bin/env python3\nprint('not json')\n")
        temp_script = f.name

    os.chmod(temp_script, 0o755)

    try:
        action_data = {"action": "test", "version": "1.0", "inputs": {}}
        result = execute_action_script(temp_script, action_data, timeout=10)

        assert result["status"] == "error"
        assert "Invalid JSON" in result["error"]
    finally:
        os.unlink(temp_script)


def test_execute_action_script_nonzero_exit_with_json_error():
    """Should parse JSON error from stdout even when script exits with non-zero code."""
    # Create a script that outputs JSON error to stdout AND exits with code 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""#!/usr/bin/env python3
import sys
import json

# Output JSON error to stdout
output = {"status": "error", "outputs": {}, "error": "Detailed error from script"}
json.dump(output, sys.stdout)
sys.stdout.flush()

# Exit with non-zero code
sys.exit(1)
""")
        temp_script = f.name
    
    os.chmod(temp_script, 0o755)
    
    try:
        action_data = {"action": "test", "version": "1.0", "inputs": {}}
        result = execute_action_script(temp_script, action_data, timeout=10)
        
        # Should capture the detailed error from JSON, not generic "Script exited with code 1"
        assert result["status"] == "error"
        assert result["error"] == "Detailed error from script"
        assert "Script exited with code" not in result["error"]
    finally:
        os.unlink(temp_script)


def test_execute_action_script_nonzero_exit_without_json_uses_stderr():
    """Should fall back to stderr when script exits non-zero without valid JSON."""
    # Create a script that outputs to stderr and exits with code 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""#!/usr/bin/env python3
import sys

# Write error to stderr, nothing to stdout
sys.stderr.write("Error from stderr")
sys.stderr.flush()

# Exit with non-zero code
sys.exit(1)
""")
        temp_script = f.name
    
    os.chmod(temp_script, 0o755)
    
    try:
        action_data = {"action": "test", "version": "1.0", "inputs": {}}
        result = execute_action_script(temp_script, action_data, timeout=10)
        
        # Should capture error from stderr
        assert result["status"] == "error"
        assert "Error from stderr" in result["error"]
    finally:
        os.unlink(temp_script)


def test_execute_actions_from_file():
    """Should execute pending actions from file."""
    # Create a temporary allowlist with mock script
    allowlist_content = {
        "test-action": {
            "script": "tests/fixtures/mock-success.py",
            "version": "1.0",
            "schema": "tests/fixtures/test-schema.json",
            "timeout": 10,
            "environment": "any",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(allowlist_content, f)
        temp_allowlist = f.name

    # Create a temporary daily file with pending action
    daily_content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test"
outputs: {}
meta: {}
```
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(daily_content)
        temp_daily = f.name

    try:
        # Execute actions (without committing)
        report = execute_actions_from_file(
            file_path=temp_daily, allowlist_path=temp_allowlist, commit=False
        )

        # Check report
        assert report.total_actions == 1
        assert report.pending_actions == 1
        assert report.executed_actions == 1
        assert report.successful_actions == 1
        assert report.failed_actions == 0
        assert report.skipped_actions == 0

        # Check that file was updated
        with open(temp_daily) as f:
            updated_content = f.read()

        assert "- [x] `a1`" in updated_content
        assert "executedAt:" in updated_content
        assert "runId:" in updated_content

    finally:
        os.unlink(temp_allowlist)
        os.unlink(temp_daily)


def test_execute_actions_from_file_with_failure():
    """Should handle action execution failure."""
    # Create allowlist with failing script
    allowlist_content = {
        "test-action": {
            "script": "tests/fixtures/mock-failure.py",
            "version": "1.0",
            "schema": "tests/fixtures/test-schema.json",
            "timeout": 10,
            "environment": "any",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(allowlist_content, f)
        temp_allowlist = f.name

    daily_content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test"
outputs: {}
meta: {}
```
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(daily_content)
        temp_daily = f.name

    try:
        report = execute_actions_from_file(
            file_path=temp_daily, allowlist_path=temp_allowlist, commit=False
        )

        assert report.executed_actions == 1
        assert report.successful_actions == 0
        assert report.failed_actions == 1

        # Check that file was updated with error
        with open(temp_daily) as f:
            updated_content = f.read()

        assert "- [x] `a1`" in updated_content
        assert "error:" in updated_content

    finally:
        os.unlink(temp_allowlist)
        os.unlink(temp_daily)


def test_execute_actions_skips_checked_actions():
    """Should skip already checked actions."""
    allowlist_content = {
        "test-action": {
            "script": "tests/fixtures/mock-success.py",
            "version": "1.0",
            "schema": "tests/fixtures/test-schema.json",
            "timeout": 10,
            "environment": "any",
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(allowlist_content, f)
        temp_allowlist = f.name

    # File with checked action
    daily_content = """- [x] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs:
  result: "Already done"
meta:
  executedAt: "2026-01-15T10:00:00Z"
```
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(daily_content)
        temp_daily = f.name

    try:
        report = execute_actions_from_file(
            file_path=temp_daily, allowlist_path=temp_allowlist, commit=False
        )

        # Should not execute any actions
        assert report.total_actions == 1
        assert report.pending_actions == 0
        assert report.executed_actions == 0

    finally:
        os.unlink(temp_allowlist)
        os.unlink(temp_daily)


def test_execution_report_to_dict():
    """ExecutionReport should serialize to dictionary."""
    result = ActionResult(
        action_id="a1",
        action_name="test-action",
        status="success",
        outputs={"result": "done"},
        executed_at="2026-01-15T10:00:00Z",
        run_id="123456",
        duration_seconds=1.5,
    )

    report = ExecutionReport(
        total_actions=2,
        pending_actions=1,
        executed_actions=1,
        successful_actions=1,
        failed_actions=0,
        skipped_actions=0,
        results=[result],
    )

    data = report.to_dict()

    assert data["total_actions"] == 2
    assert data["executed_actions"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["action_id"] == "a1"


def test_execution_report_print_summary(capsys):
    """ExecutionReport should print readable summary."""
    report = ExecutionReport(
        total_actions=5,
        pending_actions=3,
        executed_actions=3,
        successful_actions=2,
        failed_actions=1,
        skipped_actions=0,
    )

    report.print_summary()
    captured = capsys.readouterr()

    assert "Execution complete" in captured.out
    assert "Total actions: 5" in captured.out
    assert "Successful: 2" in captured.out
    assert "Failed: 1" in captured.out
