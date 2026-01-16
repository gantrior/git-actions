# Installation Guide: Actions-as-Markdown Framework

This guide explains how to install and configure the Actions-as-Markdown Framework in your repository.

---

## Overview

The Actions-as-Markdown Framework is designed to be installed in your repository as a git submodule. This allows you to easily update to new framework versions by updating the submodule reference. Once installed, you can define custom actions specific to your needs and propose/execute them through pull requests.

**Benefits of submodule installation:**
- Easy updates: Pull new framework versions with a simple `git submodule update`
- Version control: Pin to specific framework versions or tags
- Separation: Framework code stays separate from your custom actions
- No duplication: Share the same framework code across multiple repositories

---

## Prerequisites

- A GitHub repository with admin access
- Python 3.9 or higher
- Git command line tools

---

## Installation Steps

### Step 1: Add Framework as Git Submodule (Recommended)

Adding the framework as a git submodule allows you to easily update to new versions by updating the submodule reference.

```bash
# Navigate to your repository
cd /path/to/your-repo

# Add the framework as a submodule
git submodule add https://github.com/gantrior/git-actions.git .github/actions-framework

# Initialize and update the submodule
git submodule update --init --recursive

# Commit the submodule addition
git add .gitmodules .github/actions-framework
git commit -m "Add actions-as-markdown framework as submodule"
```

**To update the framework to the latest version later:**

```bash
# Update the submodule to the latest version
cd .github/actions-framework
git pull origin main
cd ../..

# Commit the updated submodule reference
git add .github/actions-framework
git commit -m "Update actions-framework to latest version"
```

**To update to a specific version/tag:**

```bash
cd .github/actions-framework
git checkout v0.0.3  # or any specific tag/version
cd ../..
git add .github/actions-framework
git commit -m "Update actions-framework to v0.0.3"
```

**Alternative: Copy Framework Files (Not Recommended)**

If you prefer not to use submodules, you can copy the framework files directly:

```bash
# Clone the framework repository
git clone https://github.com/gantrior/git-actions.git /tmp/actions-framework

# Copy framework files to your repository
cp -r /tmp/actions-framework/tools/ /path/to/your-repo/
cp /tmp/actions-framework/requirements.txt /path/to/your-repo/

# Clean up
rm -rf /tmp/actions-framework
```

**Note**: With this approach, you'll need to manually update files when new framework versions are released.

**After installation, your repository structure will be:**

```text
your-repo/
├── .github/
│   ├── actions-framework/          # Git submodule (framework code)
│   │   ├── tools/
│   │   │   ├── parser.py
│   │   │   ├── editor.py
│   │   │   ├── validator.py
│   │   │   └── executor.py
│   │   └── requirements.txt
│   └── workflows/
│       ├── pr-validation.yml
│       └── execute-actions.yml
├── actions/
│   └── allowlist.yaml              # Your custom action definitions
├── schemas/
│   └── (your custom schemas here)
└── scripts/
    └── (your custom action scripts here)
```

### Step 2: Set Up GitHub Actions Workflows

Create two workflow files in your repository's `.github/workflows/` directory. These workflows reference the framework tools from the submodule.

#### PR Validation Workflow

Create `.github/workflows/pr-validation.yml`:

```yaml
name: PR Validation

on:
  pull_request:
    branches:
      - main
    paths:
      - 'actions/*.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    name: Validate Action Files
    
    permissions:
      contents: read
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive  # Important: checkout submodules
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r .github/actions-framework/requirements.txt
      
      - name: Validate action files
        id: validation
        run: |
          PYTHONPATH=.github/actions-framework python .github/actions-framework/tools/pr_validator.py --file "actions/*.md"
      
      - name: Validation summary
        if: always()
        run: |
          if [ "${{ steps.validation.outcome }}" == "success" ]; then
            echo "✅ All action files are valid"
          else
            echo "❌ Validation failed - see errors above"
            exit 1
          fi
```

#### Action Execution Workflow

Create `.github/workflows/execute-actions.yml`:

```yaml
name: Execute Actions

on:
  push:
    branches:
      - main
    paths:
      - 'actions/*.md'

# Ensure only one execution runs at a time to avoid conflicts
concurrency:
  group: execute-actions
  cancel-in-progress: false

jobs:
  execute:
    runs-on: ubuntu-latest
    name: Execute Pending Actions
    
    permissions:
      contents: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          submodules: recursive  # Important: checkout submodules
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r .github/actions-framework/requirements.txt
      
      - name: Execute actions
        id: execution
        env:
          CI: "true"
          GITHUB_RUN_ID: ${{ github.run_id }}
          # Add your custom secrets here as needed
          # JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
          # SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        run: |
          PYTHONPATH=.github/actions-framework python .github/actions-framework/tools/action_executor.py --file "actions/*.md" --commit
      
      - name: Execution summary
        if: always()
        run: |
          if [ "${{ steps.execution.outcome }}" == "success" ]; then
            echo "✅ All actions executed successfully"
          else
            echo "❌ Some actions failed - see logs above"
            exit 1
          fi
```

### Step 3: Configure Branch Protection (Important!)

The framework commits action results back to the `main` branch. You need to configure branch protection to allow the GitHub Actions bot to push commits while still protecting your branch.

#### Option 1: Allow GitHub Actions to bypass protection (Recommended)

1. Go to your repository **Settings** → **Branches**
2. Click **Add rule** (or edit existing rule for `main`)
3. Configure the following settings:
   - **Branch name pattern**: `main`
   - ✅ **Require a pull request before merging**
   - ✅ **Require approvals** (set to 1 or more)
   - ✅ **Require status checks to pass before merging**
     - Add `Validate Action Files` as required check
   - ✅ **Allow specified actors to bypass required pull requests**
     - Add `github-actions[bot]` to the list
4. Click **Create** or **Save changes**

**Why this works**: This allows the execution workflow to commit results directly to `main` after actions execute, while still requiring PRs for all human-initiated changes.

#### Option 2: Use a Personal Access Token (PAT)

If you prefer not to bypass protection rules, use a PAT with appropriate permissions:

1. Create a Personal Access Token (classic) with `repo` scope
2. Add it as a repository secret: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `PAT_TOKEN`
   - Value: Your PAT
3. Update `.github/workflows/execute-actions.yml`:
   ```yaml
   - name: Checkout code
     uses: actions/checkout@v4
     with:
       token: ${{ secrets.PAT_TOKEN }}  # Changed from GITHUB_TOKEN
   ```

#### Option 3: Create a separate results branch

If you want to keep `main` fully protected:

1. Create a `results` branch for execution outputs
2. Update `.github/workflows/execute-actions.yml` to commit to `results` branch
3. Periodically merge `results` back to `main` via PR

**Note**: Option 1 is recommended for most use cases.

### Step 4: Create Your First Custom Action

Create a custom action type specific to your needs. Here's an example for posting Slack messages:

#### 4.1 Create the JSON Schema

Create `schemas/slack-message.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["message"],
  "properties": {
    "message": {
      "type": "string",
      "minLength": 1,
      "description": "Message text to post to Slack"
    },
    "channel": {
      "type": "string",
      "pattern": "^#[a-z0-9-]+$",
      "description": "Slack channel (default: #general)"
    }
  },
  "additionalProperties": false
}
```

#### 4.2 Create the Action Script

Create `scripts/slack-message.py`:

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
        message = inputs.get("message")
        channel = inputs.get("channel", "#general")
        
        # Get Slack webhook URL from environment
        webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        if not webhook_url:
            output = {
                "status": "error",
                "outputs": {},
                "error": "SLACK_WEBHOOK_URL environment variable not set"
            }
            json.dump(output, sys.stdout)
            return 1
        
        # Post to Slack
        response = requests.post(
            webhook_url,
            json={"text": message, "channel": channel},
            timeout=30
        )
        response.raise_for_status()
        
        # Return success
        output = {
            "status": "success",
            "outputs": {
                "posted": True,
                "channel": channel
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

Make the script executable:

```bash
chmod +x scripts/slack-message.py
```

#### 4.3 Register in Allowlist

Edit `actions/allowlist.yaml`:

```yaml
slack-message:
  script: "scripts/slack-message.py"
  version: "1.0"
  schema: "schemas/slack-message.json"
  timeout: 30
  environment: "any"
```

#### 4.4 Configure Secrets

Add your Slack webhook URL as a repository secret:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `SLACK_WEBHOOK_URL`
4. Value: Your Slack webhook URL
5. Click **Add secret**

Update `.github/workflows/execute-actions.yml` to include the secret:

```yaml
- name: Execute actions
  env:
    CI: "true"
    GITHUB_RUN_ID: ${{ github.run_id }}
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}  # Add this line
  run: |
    PYTHONPATH=.github/actions-framework python .github/actions-framework/tools/action_executor.py --file "actions/*.md" --commit
```

### Step 5: Test Your Installation

Create a test action file to verify everything works:

#### 5.1 Create Test Action

Create `actions/2026-01-16.md`:

```markdown
# Actions for 2026-01-16

Daily actions log. Actions are executed when merged to main.

- [ ] `test-1` — *slack-message* v1.0
```yaml
inputs:
  message: "Hello from Actions-as-Markdown Framework!"
  channel: "#general"
outputs: {}
meta: {}
```
```

#### 5.2 Test Validation Locally

```bash
# Install dependencies
pip install -r .github/actions-framework/requirements.txt

# Validate the action file
PYTHONPATH=.github/actions-framework python .github/actions-framework/tools/pr_validator.py --file actions/2026-01-16.md
```

You should see output like:
```
✅ All action files are valid
```

#### 5.3 Create PR and Test Workflow

```bash
git checkout -b test-slack-action
git add actions/2026-01-16.md
git commit -m "Add test Slack message action"
git push origin test-slack-action
```

Create a PR on GitHub. The PR validation workflow should run automatically and pass.

#### 5.4 Merge and Verify Execution

Merge the PR to `main`. The execution workflow should:
1. Execute the action
2. Post the message to Slack
3. Commit the results back to the action file

Check the updated file to see the execution results:

```markdown
- [x] `test-1` — *slack-message* v1.0
```yaml
inputs:
  message: "Hello from Actions-as-Markdown Framework!"
  channel: "#general"
outputs:
  posted: true
  channel: "#general"
meta:
  executedAt: "2026-01-16T14:32:11Z"
  runId: "1234567890"
```
```

---

## Troubleshooting

### Workflow doesn't trigger

**Problem**: PR validation or execution workflow doesn't run.

**Solutions**:
- Verify workflow files are in `.github/workflows/` directory
- Check that action files are in `actions/` directory with `.md` extension
- Ensure branch protection rules don't block the workflows
- Check GitHub Actions is enabled: **Settings** → **Actions** → **General**

### Execution workflow can't push commits

**Problem**: Execution workflow fails with permission error when trying to commit results.

**Solutions**:
- Follow Step 3 to configure branch protection correctly
- Verify the workflow has `contents: write` permission
- Check that `github-actions[bot]` is allowed to bypass PR requirements
- Consider using a PAT if issues persist (Option 2 in Step 3)

### Action script fails to execute

**Problem**: Action executes but script returns an error.

**Solutions**:
- Verify script has execute permissions: `chmod +x scripts/your-script.py`
- Check environment variables are configured as secrets
- Review script logs in GitHub Actions workflow run
- Test script locally: `echo '{"inputs":{...}}' | ./scripts/your-script.py`
- Ensure all required Python packages are in `requirements.txt`

### Schema validation fails

**Problem**: PR validation fails with schema errors.

**Solutions**:
- Verify JSON schema syntax is correct
- Check that inputs match schema requirements
- Ensure action name in allowlist matches action entry exactly
- Validate schema file path is correct in allowlist

### Submodule not found or checkout fails

**Problem**: Workflow fails with "submodule not found" or similar errors.

**Solutions**:
- Verify submodule was added correctly: `git submodule status`
- Ensure workflow has `submodules: recursive` in checkout step
- Try initializing submodule manually: `git submodule update --init --recursive`
- Check `.gitmodules` file exists and has correct URL

---

## Directory Structure Reference

After installation with submodule, your repository should have this structure:

```text
your-repo/
├── .github/
│   ├── actions-framework/          # Git submodule (framework code)
│   │   ├── tools/
│   │   │   ├── parser.py           # Framework core - parses action files
│   │   │   ├── editor.py           # Framework core - edits action files
│   │   │   ├── validator.py        # Framework core - validates actions
│   │   │   ├── executor.py         # Framework core - executes actions
│   │   │   ├── pr_validator.py     # CLI tool for PR validation
│   │   │   └── action_executor.py  # CLI tool for action execution
│   │   └── requirements.txt        # Python dependencies for framework
│   └── workflows/
│       ├── pr-validation.yml       # Validates PRs with action changes
│       └── execute-actions.yml     # Executes actions on merge to main
├── actions/
│   ├── allowlist.yaml              # Registry of allowed action types
│   └── YYYY-MM-DD.md               # Daily action files (created as needed)
├── schemas/
│   └── your-action.json            # JSON schemas for your custom actions
├── scripts/
│   └── your-action.py              # Your custom action scripts
├── .gitmodules                     # Git submodule configuration
└── README.md                       # Your repository documentation
```

**Note**: The `tools/` directory and `requirements.txt` are in the submodule, not your main repository.

---

## Next Steps

1. **Read the [Quickstart Guide](quickstart.md)** to learn how to use the framework
2. **Create custom actions** for your specific needs (see [Adding Actions](adding-actions.md))
3. **Configure additional secrets** for your action scripts
4. **Customize workflows** if you need different behavior
5. **Review past actions** by browsing the `actions/` directory
6. **Update the framework** periodically by updating the submodule to get new features and fixes

---

## Getting Help

- **Installation issues**: Check the Troubleshooting section above
- **Usage questions**: See the [Quickstart Guide](quickstart.md)
- **Adding custom actions**: See [Adding Actions Guide](adding-actions.md)
- **Technical details**: See the [Implementation Plan](../specs/001-actions-markdown-framework/plan.md)

---

**Happy automating! 🚀**
