# Quickstart Guide: Actions-as-Markdown Framework

**Feature**: 001-actions-markdown-framework  
**Audience**: Developers and AI assistants proposing actions

> **New to the framework?** See the [Installation Guide](installation.md) first to set up the framework in your repository.

---

## What is this?

The Actions-as-Markdown Framework lets you propose automated actions (like posting Jira comments, updating docs, etc.) as reviewable PRs by editing markdown files. No action executes until the PR is merged to `main`. After execution, results are committed back inline for a complete audit trail.

**Key benefits**:
- ✅ Actions are human-readable markdown (not JSON or YAML config)
- ✅ Safe: PR validation catches errors before execution
- ✅ Auditable: All actions and results in git history
- ✅ Simple: No external database or complex infrastructure

---

## Quick Example

### 1. Propose an action (Create PR)

Create or edit `actions/2026-01-15.md`:

```markdown
# Actions for 2026-01-15

- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: |
    Fixed the authentication bug.
    Root cause was incorrect session timeout.
outputs: {}
meta: {}
```
```

**What this does**: When merged, posts a comment to Jira ticket `PROJ-123`.

### 2. PR validation runs

The PR workflow:
- ✅ Checks action format is correct
- ✅ Verifies `jira-comment` exists in allowlist
- ✅ Validates inputs match schema (ticket ID pattern, comment not empty)
- ❌ Does NOT execute the action (safe for review)

### 3. Human reviews PR

Reviewer sees:
- Exactly what action will execute
- Clear inputs (ticket ID, comment text)
- Action type and version

### 4. Merge to main

Action executes automatically:
- Script `scripts/jira-comment.py` runs with inputs
- Result captured and committed back:

```markdown
- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: |
    Fixed the authentication bug.
    Root cause was incorrect session timeout.
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
  commentId: "456"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```
```

---

## File Structure

```text
actions/
  2026-01-15.md        # Today's actions
  2026-01-16.md        # Tomorrow's actions
  allowlist.yaml       # Registry of allowed action types

scripts/
  jira-comment.py      # Action implementation
  confluence-comment.py

schemas/
  jira-comment.json    # Input validation schema
  confluence-comment.json

tools/
  parser.py            # Framework internals (you don't edit these)
  editor.py
  validator.py
  executor.py
```

---

## Action Entry Format

Every action follows this structure:

```markdown
- [ ] `{action-id}` — *{action-name}* v{version}
```yaml
inputs:
  {key}: {value}
outputs: {}
meta: {}
```
```

**Field explanations**:
- `action-id`: Unique within the daily file (e.g., `a1`, `jira-001`)
- `action-name`: Type of action (must be in allowlist)
- `version`: Action script version (must match allowlist)
- `inputs`: Parameters for the action (validated by schema)
- `outputs`: Empty until executed, then populated with results
- `meta`: Empty until executed, then populated with timestamp and run ID

---

## How to Propose an Action

### Step 1: Choose the right daily file

**Rule**: Actions go in `actions/YYYY-MM-DD.md` where date is the day you propose them.

**Examples**:
- Today is 2026-01-15 → Use `actions/2026-01-15.md`
- Planning for tomorrow → Use `actions/2026-01-16.md`

**File doesn't exist?** Create it:

```markdown
# Actions for 2026-01-15

Daily actions log. Actions are executed when merged to main.

(actions go below)
```

### Step 2: Pick an action type

Check `actions/allowlist.yaml` for available actions:

```yaml
jira-comment:
  script: "scripts/jira-comment.py"
  version: "1.0"
  schema: "schemas/jira-comment.json"
  timeout: 60
  environment: "any"

confluence-comment:
  script: "scripts/confluence-comment.py"
  version: "1.0"
  schema: "schemas/confluence-comment.json"
  timeout: 60
  environment: "any"
```

**Action not in allowlist?** See "Adding New Action Types" below.

### Step 3: Find the schema

Look at `schemas/{action-name}.json` to see required inputs.

**Example**: `schemas/jira-comment.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["ticket", "comment"],
  "properties": {
    "ticket": {
      "type": "string",
      "pattern": "^[A-Z]+-[0-9]+$",
      "description": "Jira ticket ID (e.g., PROJ-123)"
    },
    "comment": {
      "type": "string",
      "minLength": 1,
      "description": "Comment text to post"
    }
  }
}
```

**Required fields**: `ticket`, `comment`  
**Validation**: `ticket` must match pattern `PROJ-123`, `comment` must be non-empty

### Step 4: Write the action entry

```markdown
- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Fixed the bug"
outputs: {}
meta: {}
```
```

**Tips**:
- Use unique `action-id` (check file for existing IDs)
- Match `version` exactly from allowlist
- For multiline text, use YAML literal block:
  ```yaml
  inputs:
    comment: |
      First line
      Second line
      Third line
  ```

### Step 5: Create PR

```bash
git checkout -b add-jira-comment-action
git add actions/2026-01-15.md
git commit -m "Add Jira comment action for PROJ-123"
git push origin add-jira-comment-action
```

Create PR on GitHub. The validation workflow will run automatically.

### Step 6: Fix validation errors (if any)

**Common errors**:

❌ **Action not in allowlist**:
```
ERROR: Action 'jira-coment' not found in allowlist (typo?)
```
**Fix**: Check spelling of action name

❌ **Version mismatch**:
```
ERROR: Action 'jira-comment' version mismatch: action has v2.0, allowlist expects v1.0
```
**Fix**: Change `v2.0` to `v1.0` in action entry

❌ **Missing required field**:
```
ERROR: Action 'jira-comment' inputs invalid: 'ticket' is a required property
```
**Fix**: Add `ticket` field to inputs

❌ **Invalid field value**:
```
ERROR: Action 'jira-comment' inputs invalid: 'PROJ_123' does not match pattern '^[A-Z]+-[0-9]+$'
```
**Fix**: Use hyphen instead of underscore: `PROJ-123`

### Step 7: Merge PR

Once validation passes and reviewer approves, merge to `main`. The execution workflow runs automatically and commits results back.

---

## How to Check Action Results

### Option 1: View in Git History

```bash
git log --oneline actions/2026-01-15.md
```

You'll see commits like:
```
abc123d Execute action a1 [skip ci]
```

View the commit:
```bash
git show abc123d
```

### Option 2: View the File Directly

Open `actions/2026-01-15.md` and look for `[x]` checkboxes:

```markdown
- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Fixed the bug"
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
  commentId: "456"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```
```

**Success indicators**:
- `[x]` checkbox is checked
- `outputs` field populated
- `meta.executedAt` timestamp present
- No `meta.error` field

**Failure indicators**:
- `[x]` checkbox is checked (action was attempted)
- `outputs` is empty: `{}`
- `meta.error` field present:
  ```yaml
  meta:
    executedAt: "2026-01-15T14:32:45Z"
    runId: "1234567890"
    error: "API rate limit exceeded: 429 Too Many Requests"
  ```

---

## Troubleshooting

### Action didn't execute after merge

**Check**:
1. Is checkbox still unchecked `[ ]`?
   - View GitHub Actions workflow runs
   - Look for "Execute Actions" workflow
   - Check logs for errors

2. Was action skipped due to environment?
   - Check `meta.skipped` field:
     ```yaml
     meta:
       skipped: true
       reason: "Environment mismatch: action requires local, running in ci"
     ```

### PR validation failed but I can't see why

**Check**:
1. View GitHub Actions workflow run for PR
2. Look at "Validate Action Proposals" job
3. Read error output (includes line numbers)

**Common causes**:
- Malformed YAML (indentation, missing colon)
- Action ID has spaces or special characters
- Version format wrong (needs `v1.0` not `1.0`)

### I need to re-run a failed action

**Option 1: Re-propose** (recommended)
- Create new action entry with different ID:
  ```markdown
  - [ ] `a1-retry` — *jira-comment* v1.0
  ```

**Option 2: Manual edit** (advanced)
- Manually uncheck the failed action (change `[x]` to `[ ]`)
- Remove `outputs` and `meta` (reset to `{}`)
- Create PR with changes
- **Warning**: Validation will reject this in PR mode due to immutability check

---

## Adding New Action Types

**Action not in allowlist?** See the [Installation Guide](installation.md#step-4-create-your-first-custom-action) for a complete example, or the [Adding Actions Guide](adding-actions.md) for detailed instructions on creating custom action types.

---

## Best Practices

### ✅ DO

- Use descriptive action IDs (`jira-proj123`, not just `a1`)
- Write clear, detailed input values (helps reviewers)
- Check allowlist before proposing (avoid typos)
- Review your own PR before requesting review
- Add actions to the current day's file (not past dates)
- Use multiline YAML for long text:
  ```yaml
  comment: |
    Line 1
    Line 2
  ```

### ❌ DON'T

- Don't modify checked actions (`[x]`) - they're immutable
- Don't put secrets in markdown files (they go in environment variables)
- Don't reuse action IDs within same daily file
- Don't skip `outputs: {}` and `meta: {}` fields (required even when empty)
- Don't use version `1.0` when allowlist says `v1.0` (include the `v`)

---

## Common Action Types

### Jira Comment

```markdown
- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Status update"
outputs: {}
meta: {}
```
```

### Confluence Comment

```markdown
- [ ] `a2` — *confluence-comment* v1.0
```yaml
inputs:
  pageId: "98765"
  comment: "Updated documentation"
outputs: {}
meta: {}
```
```

---

## Next Steps

1. **Explore existing actions**: Check `actions/allowlist.yaml`
2. **Review past actions**: Browse `actions/` directory
3. **Propose your first action**: Follow the quickstart above
4. **Add new action types**: See "Adding New Action Types" section

---

## Getting Help

- **Schema validation errors**: Check `schemas/{action-name}.json` for requirements
- **Execution failures**: Check `meta.error` field in action entry
- **Workflow issues**: View GitHub Actions logs in repository
- **Questions**: Ask in repository discussions or create an issue

---

**Happy automating! 🚀**
