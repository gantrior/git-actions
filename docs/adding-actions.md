# Adding New Action Types

This guide explains how to add new action types to the Actions-as-Markdown framework.

## Overview

Adding a new action type involves three steps:
1. Create a JSON schema for input validation
2. Create an executable action script
3. Register the action in the allowlist

## Step 1: Create a JSON Schema

Create a JSON Schema file in `schemas/` that defines the required and optional inputs for your action.

**Example: `schemas/slack-message.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["channel", "message"],
  "properties": {
    "channel": {
      "type": "string",
      "pattern": "^#[a-z0-9-]+$",
      "description": "Slack channel name (e.g., #general)"
    },
    "message": {
      "type": "string",
      "minLength": 1,
      "description": "Message text to post"
    },
    "threadTs": {
      "type": "string",
      "description": "Optional: Thread timestamp for replies"
    }
  },
  "additionalProperties": false
}
```

**Schema Guidelines:**
- Use JSON Schema Draft 7 format
- Define all required fields in the `required` array
- Use `pattern` for string validation (e.g., email, ID formats)
- Add clear `description` fields for documentation
- Set `additionalProperties: false` to prevent unknown fields

## Step 2: Create an Action Script

Create an executable script in `scripts/` that implements your action. The script must:
- Read JSON input from stdin
- Write JSON output to stdout
- Exit with code 0 on success, non-zero on error

**Example: `scripts/slack-message.py`**

```python
#!/usr/bin/env python3
"""Slack message action script."""

import sys
import json
import os
import requests

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        inputs = input_data.get("inputs", {})

        # Extract inputs
        channel = inputs.get("channel")
        message = inputs.get("message")
        thread_ts = inputs.get("threadTs")

        # Get Slack token from environment
        slack_token = os.environ.get("SLACK_BOT_TOKEN")
        if not slack_token:
            output = {
                "status": "error",
                "outputs": {},
                "error": "SLACK_BOT_TOKEN environment variable not set"
            }
            json.dump(output, sys.stdout)
            return 1

        # Call Slack API
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {slack_token}"},
            json={
                "channel": channel,
                "text": message,
                "thread_ts": thread_ts
            }
        )

        data = response.json()

        if not data.get("ok"):
            output = {
                "status": "error",
                "outputs": {},
                "error": f"Slack API error: {data.get('error', 'Unknown error')}"
            }
            json.dump(output, sys.stdout)
            return 1

        # Return success
        output = {
            "status": "success",
            "outputs": {
                "messageTs": data["ts"],
                "messageUrl": f"https://yourworkspace.slack.com/archives/{channel}/p{data['ts'].replace('.', '')}"
            }
        }
        json.dump(output, sys.stdout)
        return 0

    except Exception as e:
        output = {
            "status": "error",
            "outputs": {},
            "error": f"Unexpected error: {str(e)}"
        }
        json.dump(output, sys.stdout)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Script Requirements:**
- Must be executable (`chmod +x scripts/your-action.py`)
- Must read JSON from stdin with format: `{"action": "name", "version": "1.0", "inputs": {...}}`
- Must write JSON to stdout with format: `{"status": "success|error", "outputs": {...}, "error": "..."}`
- Should get secrets from environment variables (never hardcode)
- Should handle errors gracefully and return meaningful error messages

## Step 3: Register in Allowlist

Add your action to `actions/allowlist.yaml`:

```yaml
slack-message:
  script: "scripts/slack-message.py"
  version: "1.0"
  schema: "schemas/slack-message.json"
  timeout: 30  # seconds, default 300, max 3600
  environment: "any"  # any, ci-only, or local-only
```

**Allowlist Fields:**
- `script`: Path to your executable script
- `version`: Semantic version (e.g., "1.0", "2.1")
- `schema`: Path to your JSON schema
- `timeout`: Max execution time in seconds (default 300, max 3600)
- `environment`: Execution constraint:
  - `any`: Can run anywhere
  - `ci-only`: Only runs in CI/CD environments
  - `local-only`: Only runs on developer machines

## Step 4: Test Your Action

Create a test action file to verify your action works:

**`actions/2026-01-16.md`**

```markdown
- [ ] `slack-1` — *slack-message* v1.0
\```yaml
inputs:
  channel: "#general"
  message: "Deployment to production completed successfully!"
outputs: {}
meta: {}
\```
```

Test locally:

```bash
# Validate the action format
PYTHONPATH=. python tools/pr_validator.py --file actions/2026-01-16.md

# Execute the action (without committing)
export SLACK_BOT_TOKEN="your-token-here"
PYTHONPATH=. python tools/action_executor.py --file actions/2026-01-16.md --no-commit
```

## Environment Variables

Configure secrets in your CI/CD environment:

**GitHub Actions:**
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets (e.g., `SLACK_BOT_TOKEN`)
3. Reference in `.github/workflows/execute-actions.yml`:

```yaml
- name: Execute actions
  env:
    SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
  run: |
    PYTHONPATH=. python tools/action_executor.py --file "actions/*.md" --commit
```

## Best Practices

1. **Keep scripts simple** - One action, one responsibility
2. **Use environment variables for secrets** - Never hardcode credentials
3. **Return meaningful errors** - Help users debug issues
4. **Set appropriate timeouts** - Quick actions: 30s, API calls: 60s, long operations: 300s+
5. **Test thoroughly** - Validate both success and error paths
6. **Document inputs** - Clear descriptions in JSON schema
7. **Version carefully** - Increment version when changing inputs/outputs
8. **Handle rate limits** - Add retry logic for API calls if needed

## Example Actions

Here are some ideas for custom actions:

- **jira-comment** - Post comments to Jira tickets
- **github-pr-comment** - Add comments to GitHub PRs
- **slack-message** - Send Slack messages
- **email-notification** - Send email notifications
- **deploy-service** - Trigger deployments
- **run-tests** - Execute test suites
- **backup-database** - Create database backups
- **update-docs** - Update documentation sites

## Troubleshooting

**Action fails validation:**
- Check JSON schema syntax
- Verify inputs match schema requirements
- Ensure action name in allowlist matches action entry

**Action fails execution:**
- Check script has execute permissions (`chmod +x`)
- Verify script outputs valid JSON
- Check environment variables are set
- Review error messages in execution logs
- Test script manually: `echo '{"action":"...","inputs":{...}}' | ./scripts/your-action.py`

**Timeout errors:**
- Increase timeout in allowlist
- Optimize script performance
- Consider splitting into smaller actions

## Next Steps

- Read the [Quickstart Guide](quickstart.md) for usage examples
- See [Implementation Plan](../specs/001-actions-markdown-framework/plan.md) for technical details
- Check [Specification](../specs/001-actions-markdown-framework/spec.md) for requirements
