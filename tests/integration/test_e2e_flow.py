"""End-to-end integration tests for the complete workflow.

This module tests the full flow of the actions-as-markdown framework:
1. Define an action (script + schema + allowlist)
2. Create tasks/actions in a markdown file
3. Validate actions (like PR validation)
4. Execute actions (like execution on merge)
5. Verify complete workflow works E2E
"""

import pytest
import os
import tempfile
import json
import yaml
from pathlib import Path

from tools.parser import parse_daily_file
from tools.validator import validate_daily_file
from tools.executor import execute_actions_from_file


def test_e2e_complete_workflow():
    """Test complete E2E workflow: define action, validate, execute.
    
    This test simulates the complete lifecycle:
    1. Define a custom action with script and schema
    2. Create a daily file with multiple tasks/actions
    3. Validate actions (PR validation phase)
    4. Execute actions (merge-to-main phase)
    5. Verify results are written back correctly
    """
    # Create temporary directory for our test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # 1. Define action script
        script_path = tmpdir / "deploy-app.py"
        script_content = """#!/usr/bin/env python3
import sys
import json

def main():
    input_data = json.load(sys.stdin)
    inputs = input_data.get("inputs", {})
    
    # Simulate successful deployment
    output = {
        "status": "success",
        "outputs": {
            "deploymentUrl": f"https://deploy.example.com/{inputs['environment']}/{inputs['version']}",
            "deploymentId": "deploy-12345",
            "environment": inputs['environment']
        }
    }
    
    json.dump(output, sys.stdout)
    sys.stdout.flush()
    return 0

if __name__ == "__main__":
    sys.exit(main())
"""
        script_path.write_text(script_content)
        os.chmod(script_path, 0o755)
        
        # 2. Define action schema
        schema_path = tmpdir / "deploy-schema.json"
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["environment", "version"],
            "properties": {
                "environment": {
                    "type": "string",
                    "enum": ["dev", "staging", "prod"]
                },
                "version": {
                    "type": "string",
                    "pattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+$"
                }
            },
            "additionalProperties": False
        }
        schema_path.write_text(json.dumps(schema, indent=2))
        
        # 3. Create allowlist
        allowlist_path = tmpdir / "allowlist.yaml"
        allowlist = {
            "deploy-app": {
                "script": str(script_path),
                "version": "1.0",
                "schema": str(schema_path),
                "timeout": 10,
                "environment": "any"
            }
        }
        allowlist_path.write_text(yaml.dump(allowlist))
        
        # 4. Create daily file with multiple tasks/actions
        daily_file = tmpdir / "2026-01-15.md"
        daily_content = """# Daily Actions - 2026-01-15

## Deployment Tasks

- [ ] `d1` — *deploy-app* v1.0
```yaml
inputs:
  environment: dev
  version: v1.2.3
outputs: {}
meta: {}
```

- [ ] `d2` — *deploy-app* v1.0
```yaml
inputs:
  environment: staging
  version: v1.2.3
outputs: {}
meta: {}
```

- [ ] `d3` — *deploy-app* v1.0
```yaml
inputs:
  environment: prod
  version: v1.2.4
outputs: {}
meta: {}
```
"""
        daily_file.write_text(daily_content)
        
        # 5. VALIDATE phase (simulates PR validation)
        validation_result = validate_daily_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            schemas_dir=str(tmpdir),
            mode="pr"
        )
        
        # Verify validation passes
        assert validation_result.is_valid, f"Validation failed: {validation_result.errors}"
        
        # Parse and verify actions were parsed correctly
        with open(daily_file, 'r') as f:
            actions = parse_daily_file(f.read())
        
        assert len(actions) == 3
        assert all(not action.is_checked for action in actions)
        assert actions[0].id == "d1"
        assert actions[1].id == "d2"
        assert actions[2].id == "d3"
        assert actions[0].inputs["environment"] == "dev"
        assert actions[1].inputs["environment"] == "staging"
        assert actions[2].inputs["environment"] == "prod"
        
        # 6. EXECUTE phase (simulates execution on merge to main)
        report = execute_actions_from_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            commit=False  # Don't git commit in test
        )
        
        # Verify execution report
        assert report.total_actions == 3
        assert report.pending_actions == 3
        assert report.executed_actions == 3
        assert report.successful_actions == 3
        assert report.failed_actions == 0
        assert report.skipped_actions == 0
        
        # Verify results
        assert len(report.results) == 3
        for result in report.results:
            assert result.status == "success"
            assert "deploymentUrl" in result.outputs
            assert "deploymentId" in result.outputs
        
        # 7. Verify file was updated with results
        with open(daily_file, 'r') as f:
            updated_content = f.read()
            updated_actions = parse_daily_file(updated_content)
        
        # All actions should be checked now
        assert all(action.is_checked for action in updated_actions)
        
        # Verify outputs were written
        for action in updated_actions:
            assert "deploymentUrl" in action.outputs
            assert "deploymentId" in action.outputs
            assert action.outputs["environment"] in ["dev", "staging", "prod"]
        
        # Verify metadata was written
        for action in updated_actions:
            assert "executedAt" in action.meta
            assert "runId" in action.meta


def test_e2e_workflow_with_mixed_results():
    """Test E2E workflow with both successful and failed actions.
    
    This verifies that:
    1. Failed actions don't stop execution of subsequent actions
    2. Both successes and failures are properly recorded
    3. The workflow is resilient to partial failures
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create success script
        success_script = tmpdir / "success.py"
        success_script.write_text("""#!/usr/bin/env python3
import sys
import json
input_data = json.load(sys.stdin)
output = {"status": "success", "outputs": {"result": "ok"}}
json.dump(output, sys.stdout)
""")
        os.chmod(success_script, 0o755)
        
        # Create failure script
        failure_script = tmpdir / "failure.py"
        failure_script.write_text("""#!/usr/bin/env python3
import sys
import json
input_data = json.load(sys.stdin)
output = {"status": "error", "error": "Simulated failure"}
json.dump(output, sys.stdout)
sys.exit(1)
""")
        os.chmod(failure_script, 0o755)
        
        # Create simple schema
        schema_path = tmpdir / "schema.json"
        schema_path.write_text('{"type": "object", "properties": {}, "additionalProperties": true}')
        
        # Create allowlist with both action types
        allowlist_path = tmpdir / "allowlist.yaml"
        allowlist = {
            "success-action": {
                "script": str(success_script),
                "version": "1.0",
                "schema": str(schema_path),
                "timeout": 10,
                "environment": "any"
            },
            "failure-action": {
                "script": str(failure_script),
                "version": "1.0",
                "schema": str(schema_path),
                "timeout": 10,
                "environment": "any"
            }
        }
        allowlist_path.write_text(yaml.dump(allowlist))
        
        # Create daily file with mixed actions
        daily_file = tmpdir / "tasks.md"
        daily_content = """# Test Tasks

- [ ] `t1` — *success-action* v1.0
```yaml
inputs: {}
outputs: {}
meta: {}
```

- [ ] `t2` — *failure-action* v1.0
```yaml
inputs: {}
outputs: {}
meta: {}
```

- [ ] `t3` — *success-action* v1.0
```yaml
inputs: {}
outputs: {}
meta: {}
```
"""
        daily_file.write_text(daily_content)
        
        # Validate
        validation_result = validate_daily_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            schemas_dir=str(tmpdir),
            mode="pr"
        )
        assert validation_result.is_valid
        
        # Execute
        report = execute_actions_from_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            commit=False
        )
        
        # Verify mixed results
        assert report.total_actions == 3
        assert report.executed_actions == 3
        assert report.successful_actions == 2  # t1 and t3
        assert report.failed_actions == 1  # t2
        
        # Verify all actions were attempted
        assert report.results[0].status == "success"
        assert report.results[1].status == "error"
        assert report.results[2].status == "success"
        
        # Verify file was updated even with failures
        with open(daily_file, 'r') as f:
            updated_actions = parse_daily_file(f.read())
        
        # All actions should be checked
        assert all(action.is_checked for action in updated_actions)
        
        # Verify error was recorded
        assert "error" in updated_actions[1].meta
        # Error could be either the script's error message or exit code message
        assert updated_actions[1].meta["error"] is not None
        assert len(updated_actions[1].meta["error"]) > 0


def test_e2e_workflow_skips_already_executed():
    """Test that E2E workflow skips already executed actions.
    
    This simulates a workflow re-run or a file with both pending
    and completed actions.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create simple action script
        script_path = tmpdir / "action.py"
        script_path.write_text("""#!/usr/bin/env python3
import sys
import json
input_data = json.load(sys.stdin)
output = {"status": "success", "outputs": {"executed": True}}
json.dump(output, sys.stdout)
""")
        os.chmod(script_path, 0o755)
        
        schema_path = tmpdir / "schema.json"
        schema_path.write_text('{"type": "object"}')
        
        allowlist_path = tmpdir / "allowlist.yaml"
        allowlist = {
            "test-action": {
                "script": str(script_path),
                "version": "1.0",
                "schema": str(schema_path),
                "timeout": 10,
                "environment": "any"
            }
        }
        allowlist_path.write_text(yaml.dump(allowlist))
        
        # Create file with one completed and one pending action
        daily_file = tmpdir / "actions.md"
        daily_content = """# Actions

- [x] `a1` — *test-action* v1.0
```yaml
inputs: {}
outputs:
  executed: true
meta:
  executedAt: "2026-01-14T10:00:00Z"
  runId: "12345"
```

- [ ] `a2` — *test-action* v1.0
```yaml
inputs: {}
outputs: {}
meta: {}
```
"""
        daily_file.write_text(daily_content)
        
        # Execute
        report = execute_actions_from_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            commit=False
        )
        
        # Verify only pending action was executed
        assert report.total_actions == 2
        assert report.pending_actions == 1
        assert report.executed_actions == 1
        assert report.successful_actions == 1
        
        # Verify the correct action was executed
        assert report.results[0].action_id == "a2"
        
        # Verify both actions are now checked
        with open(daily_file, 'r') as f:
            updated_actions = parse_daily_file(f.read())
        
        assert all(action.is_checked for action in updated_actions)
        
        # Verify first action's metadata wasn't changed
        assert updated_actions[0].meta["runId"] == "12345"
        assert updated_actions[0].meta["executedAt"] == "2026-01-14T10:00:00Z"


def test_e2e_validation_fails_for_invalid_action():
    """Test that validation phase catches invalid actions.
    
    This ensures the PR validation step works correctly to prevent
    invalid actions from being merged.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        script_path = tmpdir / "action.py"
        script_path.write_text("#!/usr/bin/env python3\nprint('ok')")
        os.chmod(script_path, 0o755)
        
        # Create schema with required fields
        schema_path = tmpdir / "schema.json"
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["required_field"],
            "properties": {
                "required_field": {"type": "string"}
            }
        }
        schema_path.write_text(json.dumps(schema))
        
        allowlist_path = tmpdir / "allowlist.yaml"
        allowlist = {
            "test-action": {
                "script": str(script_path),
                "version": "1.0",
                "schema": str(schema_path),
                "timeout": 10,
                "environment": "any"
            }
        }
        allowlist_path.write_text(yaml.dump(allowlist))
        
        # Create file with action missing required field
        daily_file = tmpdir / "invalid.md"
        daily_content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  wrong_field: "value"
outputs: {}
meta: {}
```
"""
        daily_file.write_text(daily_content)
        
        # Validate - should fail
        validation_result = validate_daily_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            schemas_dir=str(tmpdir),
            mode="pr"
        )
        
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        assert any("required_field" in str(err).lower() for err in validation_result.errors)


def test_e2e_validation_fails_for_non_allowlisted_action():
    """Test that validation rejects actions not in allowlist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create empty allowlist
        allowlist_path = tmpdir / "allowlist.yaml"
        allowlist_path.write_text(yaml.dump({}))
        
        # Create file with non-allowlisted action
        daily_file = tmpdir / "invalid.md"
        daily_content = """- [ ] `a1` — *unknown-action* v1.0
```yaml
inputs: {}
outputs: {}
meta: {}
```
"""
        daily_file.write_text(daily_content)
        
        # Validate - should fail
        validation_result = validate_daily_file(
            file_path=str(daily_file),
            allowlist_path=str(allowlist_path),
            schemas_dir=str(tmpdir),
            mode="pr"
        )
        
        assert not validation_result.is_valid
        assert len(validation_result.errors) > 0
        assert any("unknown-action" in str(err).lower() for err in validation_result.errors)
