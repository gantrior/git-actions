# Quickstart: AI Action Hooks

**Feature**: 002-ai-action-hooks  
**Date**: 2026-01-19  
**For**: Developers integrating with external task management systems

## Overview

This guide shows you how to add custom hooks to your Actions-as-Markdown Framework repository. Hooks allow you to execute custom logic when AI actions complete, such as updating task status in Jira, sending Slack notifications, or triggering other workflows.

## Prerequisites

- Actions-as-Markdown Framework already set up in your repository
- Python 3.9+ installed
- Basic understanding of action execution workflow

## Quick Start (5 minutes)

### 1. Create Hook Configuration

Create or edit `actions/hooks.yaml` in your repository:

```yaml
hooks:
  - id: update_task_status
    lifecycle_event: after_success
    task_type_filter: []  # Empty = applies to all action types
    execution_mode: async
    execution_order: 1
    enabled: true
    script_path: scripts/hooks/update_task.py
    timeout_seconds: 30
    retry_count: 3
    retry_backoff_seconds: 2
    config:
      task_api_url: https://api.example.com/tasks
      api_key: "${TASK_API_KEY}"  # Use environment variable
```

### 2. Write Hook Script

Create `scripts/hooks/update_task.py`:

```python
#!/usr/bin/env python3
"""Update task status when action completes."""

import json
import sys
import os
import requests

def main():
    # Read context from stdin
    context = json.load(sys.stdin)

    # Get configuration (from hooks.yaml config section)
    config = context.get('hook_config', {})
    api_url = config['task_api_url']
    api_key = os.getenv('TASK_API_KEY')

    # Extract task information
    task_id = context['task_id']
    action_status = context['action_status']

    # Update task via API
    try:
        response = requests.post(
            f"{api_url}/{task_id}/status",
            headers={'Authorization': f'Bearer {api_key}'},
            json={'status': 'completed' if action_status == 'success' else 'failed'},
            timeout=10
        )
        response.raise_for_status()

        # Return success result to stdout
        result = {
            'success': True,
            'message': f'Updated task {task_id} status',
            'details': {
                'task_id': task_id,
                'new_status': response.json().get('status')
            }
        }
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # Return failure result
        result = {
            'success': False,
            'message': f'Failed to update task: {str(e)}'
        }
        print(json.dumps(result))
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### 3. Make Script Executable

```bash
chmod +x scripts/hooks/update_task.py
```

### 4. Test Your Hook

Create a test action in `actions/test-hook.md`:

```markdown
# Test Hook

- [ ] test_action
  - task_id: TEST-123
  - message: Testing hook execution
```

Commit and push to trigger the action workflow. After the action executes successfully, your hook will run and update the task status.

### 5. Check Hook Logs

View hook execution history:

```bash
cat logs/hook-executions.log | grep "update_task_status"
```

Example log entry:
```json
{"timestamp": "2026-01-19T11:07:24Z", "hook_id": "update_task_status", "lifecycle_event": "after_success", "task_id": "TEST-123", "status": "success", "duration_ms": 342}
```

## Common Use Cases

### Use Case 1: Update Jira Status on Success

```yaml
hooks:
  - id: jira_update_on_success
    lifecycle_event: after_success
    task_type_filter: ["jira_comment", "jira_update"]
    execution_mode: async
    execution_order: 1
    enabled: true
    script_path: scripts/hooks/jira_update.py
    config:
      jira_url: https://jira.example.com
      status_transition: "Done"
```

### Use Case 2: Send Slack Notification on Failure

```yaml
hooks:
  - id: slack_notify_on_failure
    lifecycle_event: after_failure
    task_type_filter: []  # All action types
    execution_mode: async
    execution_order: 1
    enabled: true
    script_path: scripts/hooks/slack_notify.sh
    config:
      webhook_url: "${SLACK_WEBHOOK_URL}"
      channel: "#alerts"
```

### Use Case 3: Log All Action Starts

```yaml
hooks:
  - id: audit_log_action_start
    lifecycle_event: before_execute
    task_type_filter: []
    execution_mode: sync  # Block until logging completes
    execution_order: 1
    enabled: true
    script_path: scripts/hooks/audit_log.py
    timeout_seconds: 5
    config:
      log_file: /var/log/actions-audit.log
```

## Hook Lifecycle Events

Choose the right event for your use case:

- **before_execute**: Runs before the action starts
  - Use for: Pre-flight checks, resource allocation, audit logging

- **after_success**: Runs after action completes successfully
  - Use for: Task status updates, success notifications

- **after_failure**: Runs after action fails
  - Use for: Error notifications, rollback, incident creation

- **after_timeout**: Runs if action times out
  - Use for: Timeout notifications, cleanup

## Execution Modes

### Async (Fire-and-Forget)

```yaml
execution_mode: async
```

- Hook runs in background, doesn't block action completion
- Best for: Notifications, non-critical updates
- Failures are logged but don't affect action

### Sync (Blocking)

```yaml
execution_mode: sync
timeout_seconds: 30
```

- Action waits for hook to complete (or timeout)
- Best for: Critical updates, validation, pre-flight checks
- Hook failure is logged but action still succeeds

## Hook Script Contract

### Input (via stdin)

Your script receives JSON via stdin with this structure:

```json
{
  "task_id": "TASK-123",
  "task_type": "jira_comment",
  "action_type": "jira_comment",
  "action_status": "success",
  "start_time": "2026-01-19T11:07:24Z",
  "end_time": "2026-01-19T11:07:26Z",
  "input_parameters": {
    "issue_key": "PROJ-456",
    "comment_text": "Automated comment"
  },
  "output_data": {
    "comment_id": "12345"
  },
  "metadata": {
    "pr_number": 42,
    "commit_sha": "abc123"
  },
  "hook_config": {
    // Your config from hooks.yaml
  }
}
```

### Output (via stdout)

Your script must output JSON to stdout:

```json
{
  "success": true,
  "message": "Updated task status",
  "details": {
    "old_status": "In Progress",
    "new_status": "Done"
  }
}
```

### Exit Codes

- `0`: Success (hook completed successfully)
- `1-255`: Failure (hook failed, will retry if configured)

## Error Handling & Retries

Configure automatic retries for transient failures:

```yaml
retry_count: 3
retry_backoff_seconds: 2  # Exponential: 2s, 4s, 8s
```

Hook will retry on:
- Non-zero exit code
- Timeout
- Script not found or not executable

Hook will NOT retry on:
- Invalid JSON output
- Schema validation failure

## Testing Hooks

### Unit Test Your Hook Script

```python
import subprocess
import json

def test_hook():
    context = {
        "task_id": "TEST-123",
        "action_status": "success",
        # ... other fields
    }

    result = subprocess.run(
        ['python3', 'scripts/hooks/update_task.py'],
        input=json.dumps(context),
        capture_output=True,
        text=True,
        timeout=5
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output['success'] == True
```

### Integration Test with Mock Action

1. Create test action in `actions/test/`
2. Configure hook to point to test script
3. Run action executor with test action
4. Verify hook execution in logs

## Troubleshooting

### Hook Not Executing

Check:
- [ ] `enabled: true` in hooks.yaml
- [ ] Script exists at `script_path`
- [ ] Script is executable (`chmod +x`)
- [ ] `task_type_filter` matches your action type (or is empty)
- [ ] Hook validation passed (check workflow logs)

### Hook Timing Out

- Increase `timeout_seconds`
- Check if external API is slow
- Consider using `async` mode instead of `sync`

### Hook Failing

Check logs:
```bash
cat logs/hook-executions.log | jq 'select(.status == "failure")'
```

Common issues:
- API credentials not set in environment
- Network connectivity issues
- Invalid JSON output from script
- Script runtime errors (check stderr in logs)

### Hook Not Filtering Correctly

Verify `task_type_filter`:
```yaml
task_type_filter: ["jira_comment"]  # Only jira_comment actions
task_type_filter: []                # All action types
```

## Best Practices

1. **Keep hooks simple**: Each hook should do one thing well
2. **Use async by default**: Unless you need to block action completion
3. **Set reasonable timeouts**: 30s for API calls, 5s for logging
4. **Log errors clearly**: Include context in error messages
5. **Use environment variables**: For API keys and sensitive config
6. **Test hooks independently**: Unit test before integration
7. **Monitor hook performance**: Check logs for slow hooks
8. **Handle failures gracefully**: Don't assume external APIs are always available

## Next Steps

- Review [data-model.md](data-model.md) for complete entity definitions
- See [contracts/](contracts/) for JSON schemas
- Check [research.md](research.md) for design decisions
- Read main [spec.md](spec.md) for complete requirements

## Support

For issues or questions:
- Check hook execution logs: `logs/hook-executions.log`
- Validate hooks.yaml schema: Use JSON Schema validator
- Review action workflow logs in GitHub Actions
