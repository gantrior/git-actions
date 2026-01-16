# Feature Specification: Actions-as-Markdown Framework

**Feature Branch**: `001-actions-markdown-framework`  
**Created**: 2026-01-16  
**Status**: Draft  
**Input**: User description: "Design a **max-compact** "actions-as-markdown" framework: Actions are **defined in repository** (scripts are the source of truth). AI creates **proposals as PRs** by editing markdown files. **No action is executed** until the PR is merged to `main`. After execution, the system **autocommits back to `main`** by **checking off** the action in the same markdown location and appending execution outputs inline (no separate audit file). Actions are grouped in **one Markdown file per day**."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Proposes Action via PR (Priority: P1)

An AI assistant (or human developer) wants to propose a new action (e.g., posting a Jira comment) to be executed later. They create a PR that adds an unchecked action entry to today's daily markdown file. The PR validation workflow checks the action format and allowlist but does not execute it.

**Why this priority**: This is the core value proposition - enabling safe, reviewable action proposals without immediate execution. Without this, the entire framework has no purpose.

**Independent Test**: Can be fully tested by creating a PR with a new action entry, verifying it passes validation, and confirming no external API calls are made during PR checks.

**Acceptance Scenarios**:

1. **Given** it's 2026-01-15 and `actions/2026-01-15.md` doesn't exist, **When** AI creates a PR adding an unchecked Jira comment action, **Then** the PR validation passes and the file is created with the action entry
2. **Given** `actions/2026-01-15.md` exists with one action, **When** AI adds a second action to the same file in a PR, **Then** validation passes and both actions are preserved
3. **Given** a PR with an invalid action (misspelled field), **When** validation runs, **Then** it fails with a clear error message identifying the specific problem
4. **Given** a PR with a non-allowlisted action type, **When** validation runs, **Then** it fails indicating the action is not allowed

---

### User Story 2 - Execute Actions on Merge (Priority: P1)

When a PR containing new actions is merged to main, the execution workflow runs, identifies all pending (unchecked) actions in the changed files, executes each one sequentially, and commits back the results (checked checkbox, outputs, metadata) to main.

**Why this priority**: Execution is equally critical as proposal - it delivers the actual value. The system is useless if actions are never executed.

**Independent Test**: Can be fully tested by merging a PR with pending actions, verifying the workflow executes them, and confirming the markdown file is updated with results and committed back to main.

**Acceptance Scenarios**:

1. **Given** `actions/2026-01-15.md` has two unchecked actions, **When** the file is merged to main, **Then** both actions execute, checkboxes are marked, outputs are written inline, and changes are auto-committed
2. **Given** an action that succeeds, **When** it executes, **Then** the checkbox is checked, outputs are captured, executedAt timestamp is recorded, and runId is stored
3. **Given** an action that fails, **When** it executes, **Then** the checkbox is checked, error message is captured, executedAt timestamp is recorded, and subsequent actions still execute
4. **Given** the same commit is processed twice (workflow re-run), **When** execution runs, **Then** already-checked actions are skipped and not re-executed

---

### User Story 3 - Human Reviews Action Proposal (Priority: P2)

A human reviewer examines a PR containing proposed actions. They can see exactly what will be executed (action type, inputs, version) in a compact, readable format. They approve or request changes based on the action's appropriateness.

**Why this priority**: Human review is the safety gate that makes this framework secure. While the framework can work without rich preview features, basic readability is essential.

**Independent Test**: Can be tested by creating a PR with actions and verifying a human can understand what will happen by reading the markdown diff.

**Acceptance Scenarios**:

1. **Given** a PR with a Jira comment action, **When** a reviewer reads the diff, **Then** they can clearly see the action type, Jira ticket ID, and comment text
2. **Given** a PR with multiple actions, **When** a reviewer reads the file, **Then** they can distinguish between actions and understand the order of execution
3. **Given** a PR that modifies an existing checked action, **When** validation runs, **Then** it fails because checked actions are immutable

---

### User Story 4 - Add New Action Type (Priority: P3)

A developer wants to add support for a new action type (e.g., Confluence comment, GitHub PR review). They create a new script in the actions directory, add it to the allowlist mapping, and define its input/output schema.

**Why this priority**: Extensibility is important for long-term value, but the framework can deliver value with just one action type initially.

**Independent Test**: Can be tested by adding a new action script, using it in a daily file, and verifying it executes correctly.

**Acceptance Scenarios**:

1. **Given** a new action script at `actions/confluence-comment.py`, **When** the allowlist is updated and an action uses it, **Then** the action executes successfully
2. **Given** a new action type with required input fields, **When** a proposal omits a required field, **Then** PR validation fails with a clear schema error

---

### User Story 5 - Audit Action History (Priority: P3)

A user wants to review what actions have been executed. They browse the daily markdown files in the `actions/` directory, where each file serves as an append-only audit log showing when actions were proposed, when they executed, and their results.

**Why this priority**: Audit capability adds transparency and debugging value, but it's a natural byproduct of the inline execution results rather than a primary feature to build.

**Independent Test**: Can be tested by reviewing a daily markdown file after actions have executed and verifying all historical information is present and human-readable.

**Acceptance Scenarios**:

1. **Given** multiple actions executed over several days, **When** a user browses the `actions/` directory, **Then** they can see one file per day with all actions and their execution results
2. **Given** an action that failed, **When** a user reads the markdown, **Then** they can see the error message inline with the action entry

---

### Edge Cases

- What happens when an action entry is malformed during parsing? (System should fail PR validation with specific line/column error)
- What happens when two PRs concurrently add actions to the same daily file? (Git merge conflict requires manual resolution)
- What happens when an action script times out or hangs? (Action runner should enforce timeout and record error)
- What happens when a daily file is manually edited while the execution workflow is running? (Concurrency lock should prevent simultaneous execution runs)
- What happens when an action outputs extremely large data (e.g., 10MB JSON)? (Output should be truncated with a warning)
- What happens when a user tries to modify a checked action in a PR? (Validation should reject as immutable)
- What happens when the repository has no `actions/` directory yet? (First action creates the directory automatically)
- What happens when an action script is deleted but old daily files reference it? (Execution should fail with clear "action not found" error)

## Requirements *(mandatory)*

### Functional Requirements

#### A) File Format Specification (Max Compact)

- **FR-001**: System MUST store actions in daily markdown files named `actions/YYYY-MM-DD.md`
- **FR-002**: Each action entry MUST use a single-line header (checkbox + identifier) followed by a fenced YAML block
- **FR-003**: Action entry format MUST be:
  ```
  - [ ] `action-id` — *action-name* v*version*
  ```yaml
  inputs:
    key: value
  outputs: {}
  meta: {}
  ```
  ```
- **FR-004**: The `action-id` MUST be a unique identifier within the daily file (e.g., `a1`, `a2`, `jira-001`)
- **FR-005**: The `action-name` MUST match an entry in the allowlist (e.g., `jira-comment`, `confluence-comment`)
- **FR-006**: The `version` field MUST specify action script version (e.g., `1.0`, `2.1`)
- **FR-007**: The `inputs` field MUST contain action-specific parameters (e.g., `ticket: PROJ-123`, `comment: "Fixed bug"`)
- **FR-008**: The `outputs` field MUST start as empty object `{}` and be populated after execution (e.g., `commentUrl: "https://jira.example.com/..."`)
- **FR-009**: The `meta` field MUST start as empty object `{}` and be populated after execution with `executedAt` (ISO timestamp), `runId` (workflow run ID), and optionally `error` (error message)
- **FR-010**: Checkbox state MUST indicate execution status: `[ ]` for pending, `[x]` for completed
- **FR-011**: Multiline text inputs MUST use YAML literal block scalar syntax (`|` or `>`) to avoid bloating the file
- **FR-012**: Daily files MUST be append-only during normal operation (new actions added at end)
- **FR-013**: Checked actions MUST be immutable (validation must reject PRs that modify checked actions)

#### B) Parsing and Editing Rules

- **FR-014**: Parser MUST identify actions by matching the pattern: `- [ ] \`[a-zA-Z0-9-]+\` — \*[a-z-]+\* v[0-9.]+` followed by YAML block
- **FR-015**: Parser MUST extract action ID, name, version, checkbox state, and YAML content for each action
- **FR-016**: Parser MUST preserve all non-action content (comments, headings, whitespace) unchanged
- **FR-017**: Editor MUST update actions in-place by matching action ID and replacing only the checkbox and YAML block
- **FR-018**: Editor MUST maintain stable diffs (no whitespace changes, no reordering of unrelated content)
- **FR-019**: Parser MUST fail with specific line/column error if action entry is malformed
- **FR-020**: Parser MUST handle edge case of action ID appearing in regular markdown text (only treat as action if format exactly matches)

#### C) Action Runner Contract

- **FR-021**: Action scripts MUST accept input as JSON on stdin
- **FR-022**: Input JSON MUST contain: `{"action": "action-name", "version": "1.0", "inputs": {...}}`
- **FR-023**: Action scripts MUST output JSON on stdout with format: `{"status": "success|error", "outputs": {...}, "error": "error message if status=error"}`
- **FR-024**: Action scripts MUST log diagnostics to stderr (not included in result)
- **FR-025**: Action scripts MUST exit with code 0 for success, non-zero for error
- **FR-026**: Action allowlist MUST be defined in `actions/allowlist.yaml` mapping action names to script paths
- **FR-027**: Allowlist entry format MUST be: `action-name: {script: "path/to/script.py", version: "1.0", schema: "path/to/schema.json"}`
- **FR-028**: Version compatibility MUST be checked: action request version must match allowlist version
- **FR-029**: Action scripts MUST have execute permission
- **FR-030**: Action runner MUST enforce timeout (default 300 seconds, configurable per action in allowlist)

#### D) Validation and Execution Pipelines

##### PR Validation Workflow

- **FR-031**: PR validation workflow MUST trigger on pull requests to `main` branch
- **FR-032**: Validation MUST check all files matching `actions/YYYY-MM-DD.md` pattern
- **FR-033**: Validation MUST verify each action entry matches required format (FR-003)
- **FR-034**: Validation MUST verify action names exist in allowlist
- **FR-035**: Validation MUST verify action versions match allowlist versions
- **FR-036**: Validation MUST verify input fields match JSON schema for that action
- **FR-037**: Validation MUST reject PRs that modify checked actions (immutability rule)
- **FR-038**: Validation MUST NOT execute actions or call external APIs
- **FR-039**: Validation MUST NOT have access to production secrets
- **FR-040**: Validation MAY run dry-run preview showing what would execute (without side effects)

##### Main Execution Workflow

- **FR-041**: Execution workflow MUST trigger on push to `main` branch
- **FR-042**: Execution MUST identify changed files matching `actions/YYYY-MM-DD.md`
- **FR-043**: For each changed file, execution MUST parse all actions and identify unchecked ones
- **FR-044**: Execution MUST execute unchecked actions sequentially (not in parallel)
- **FR-045**: For each action execution, system MUST invoke the mapped script with inputs
- **FR-046**: After successful execution, system MUST update action entry: check checkbox, populate outputs, add meta (executedAt, runId)
- **FR-047**: After failed execution, system MUST update action entry: check checkbox, add meta with error message
- **FR-048**: After all actions in a file are processed, system MUST commit changes with message: "Execute actions from YYYY-MM-DD"
- **FR-049**: Execution MUST skip already-checked actions (idempotent execution)
- **FR-050**: Execution workflow MUST have access to production secrets (e.g., JIRA_TOKEN)
- **FR-051**: Execution MUST use concurrency lock to prevent multiple simultaneous runs on same files
- **FR-052**: Execution MUST handle partial failure (some actions succeed, some fail) by processing all actions regardless

#### E) Repository Layout

- **FR-053**: Repository MUST have directory structure:
  ```
  actions/               # Daily action files
    YYYY-MM-DD.md        # One file per day
    allowlist.yaml       # Action allowlist and metadata
  scripts/               # Action implementation scripts
    jira-comment.py      # Example action script
    confluence-comment.py
  schemas/               # JSON schemas for action inputs
    jira-comment.json    # Schema for jira-comment inputs
  tools/                 # Parsing and editing utilities
    parser.py            # Markdown parser
    editor.py            # In-place editor
    validator.py         # Schema validator
  .github/
    workflows/
      pr-validation.yml  # PR validation workflow
      execute-actions.yml # Main execution workflow
  tests/                 # Test fixtures and test code
    fixtures/
      sample-day.md      # Example daily file
      expected-output.md # Expected result after execution
  ```
- **FR-054**: Action scripts MUST be stored in `scripts/` directory
- **FR-055**: Schemas MUST be stored in `schemas/` directory
- **FR-056**: Tools MUST be stored in `tools/` directory

#### F) Testing Strategy

- **FR-057**: System MUST include unit tests for parser using golden file fixtures
- **FR-058**: Parser tests MUST verify correct extraction of action ID, name, version, checkbox state, inputs
- **FR-059**: Editor tests MUST verify in-place updates produce minimal diffs
- **FR-060**: System MUST include unit tests for schema validation against action schemas
- **FR-061**: Validation tests MUST verify detection of missing fields, wrong types, invalid values
- **FR-062**: System MUST include integration tests using mock action scripts (no real API calls)
- **FR-063**: Integration tests MUST verify end-to-end flow: parse → validate → execute → update → commit
- **FR-064**: System MUST provide sample fixtures:
  - `tests/fixtures/sample-day-pending.md` (before execution)
  - `tests/fixtures/sample-day-complete.md` (after execution)
- **FR-065**: Tests MUST verify idempotent execution (re-running doesn't duplicate actions)
- **FR-066**: Tests MUST verify immutability (checked actions cannot be modified)

#### G) Acceptance Criteria (Testable)

- **FR-067**: GIVEN `actions/2026-01-15.md` with two unchecked actions, WHEN merged to main, THEN system executes both, checks them off, writes outputs, commits changes
- **FR-068**: GIVEN workflow re-runs on same commit, WHEN execution runs, THEN already-checked actions are NOT re-executed
- **FR-069**: GIVEN PR with invalid action format, WHEN validation runs, THEN PR fails with actionable error message showing line number and issue
- **FR-070**: GIVEN PR with non-allowlisted action, WHEN validation runs, THEN PR fails indicating action is not in allowlist
- **FR-071**: GIVEN action script that succeeds, WHEN executed, THEN output includes executedAt timestamp, runId, and action outputs
- **FR-072**: GIVEN action script that fails, WHEN executed, THEN output includes executedAt timestamp, runId, and error message
- **FR-073**: GIVEN PR that modifies a checked action, WHEN validation runs, THEN PR fails indicating checked actions are immutable
- **FR-074**: GIVEN daily file with 3 actions where 1 fails, WHEN execution runs, THEN all 3 are processed and file shows success for 2 and error for 1

### Key Entities

- **Daily Action File**: Markdown file named `YYYY-MM-DD.md` containing all actions proposed for that day
- **Action Entry**: Single action defined by checkbox line + YAML block, uniquely identified by action ID
- **Action Script**: Executable script that implements an action type (e.g., post Jira comment)
- **Allowlist**: YAML file mapping action names to script paths, versions, and schemas
- **Action Inputs**: Parameters required to execute an action (e.g., ticket ID, comment text)
- **Action Outputs**: Data returned from successful action execution (e.g., comment URL)
- **Action Metadata**: Execution information (timestamp, run ID, error message)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI can propose an action by creating a PR in under 1 minute (from intent to PR created)
- **SC-002**: PR validation completes in under 30 seconds for files with up to 50 actions
- **SC-003**: Action execution workflow completes within 10 minutes for a daily file with 20 actions (assuming 30-second average per action)
- **SC-004**: 100% of malformed action entries are caught during PR validation (no invalid actions reach main)
- **SC-005**: Daily markdown files remain under 100KB even with 50 actions (compact format goal)
- **SC-006**: Developers can add a new action type in under 1 hour (script + schema + allowlist entry)
- **SC-007**: Execution workflow achieves idempotent behavior (re-running same commit 10 times produces identical final state)
- **SC-008**: Zero execution failures due to race conditions when processing concurrent commits
- **SC-009**: Audit history is 100% accurate (every executed action has complete metadata)
- **SC-010**: Human reviewers can understand action intent from markdown diff without additional documentation

## Assumptions *(optional)*

The following assumptions were made to fill gaps in the feature description:

- **ASM-001**: Python is the preferred implementation language for tooling (parser, editor, validator) based on the problem statement's suggestion
- **ASM-002**: GitHub Actions is the CI/CD platform based on existing repository structure
- **ASM-003**: Actions execute sequentially (not in parallel) to maintain simplicity and avoid complex state management
- **ASM-004**: Action scripts can be written in any language as long as they accept JSON on stdin and output JSON on stdout
- **ASM-005**: Default action timeout is 300 seconds (5 minutes) but configurable per action type
- **ASM-006**: Maximum output size per action is 10KB; larger outputs are truncated with warning
- **ASM-007**: Daily files are created on-demand when first action is added (no pre-creation needed)
- **ASM-008**: Action IDs only need to be unique within a single daily file (not globally unique)
- **ASM-009**: Concurrency control uses GitHub Actions' built-in concurrency groups (no external locking service)
- **ASM-010**: The system targets teams of 1-10 users with 10-50 actions per day (not high-scale enterprise use)

## Out of Scope *(optional)*

The following are explicitly not included in this specification:

- **OOS-001**: Web UI for browsing action history (users browse markdown files directly)
- **OOS-002**: Action rollback or undo functionality (actions are write-only)
- **OOS-003**: Action dependencies or ordering constraints (all actions execute in file order)
- **OOS-004**: Action scheduling or delayed execution (actions execute immediately on merge)
- **OOS-005**: Multi-repository action execution (framework operates within single repository)
- **OOS-006**: Action result notifications (no email/Slack alerts on completion)
- **OOS-007**: Action retry logic (failed actions remain failed; manual re-proposal needed)

## Constraints *(optional)*

- **CON-001**: Markdown format must remain human-readable and editable (no binary encoding)
- **CON-002**: Parser must not depend on heavyweight libraries (prefer standard library where possible)
- **CON-003**: Secrets must never appear in markdown files (only passed to action scripts via environment)
- **CON-004**: Git history must be linear (no force pushes to main)
- **CON-005**: Daily files must not exceed GitHub's 100MB file size limit
- **CON-006**: Action scripts must complete within repository's GitHub Actions timeout limits (6 hours max, but default 5 minutes per action)

## Dependencies *(optional)*

- **DEP-001**: GitHub Actions for CI/CD workflows
- **DEP-002**: Git for version control and concurrency management
- **DEP-003**: Python 3.9+ for tooling (parser, editor, validator)
- **DEP-004**: PyYAML library for YAML parsing
- **DEP-005**: JSON Schema validation library (e.g., jsonschema)
- **DEP-006**: External APIs for action execution (Jira, Confluence, GitHub) - provided by user

## Concrete Examples *(optional)*

### Example 1: Pending Actions (Before Execution)

**File**: `actions/2026-01-15.md`

```markdown
# Actions for 2026-01-15

Daily actions log. Actions are executed when merged to main.

- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: |
    Fixed the bug in user authentication.
    Root cause was incorrect session timeout.
outputs: {}
meta: {}
```

- [ ] `a2` — *confluence-comment* v1.0
```yaml
inputs:
  pageId: "98765"
  comment: "Updated documentation for v2.0 API"
outputs: {}
meta: {}
```
```

### Example 2: Completed Actions (After Execution)

**File**: `actions/2026-01-15.md` (after execution workflow runs)

```markdown
# Actions for 2026-01-15

Daily actions log. Actions are executed when merged to main.

- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: |
    Fixed the bug in user authentication.
    Root cause was incorrect session timeout.
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456789"
  commentId: "456789"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```

- [x] `a2` — *confluence-comment* v1.0
```yaml
inputs:
  pageId: "98765"
  comment: "Updated documentation for v2.0 API"
outputs: {}
meta:
  executedAt: "2026-01-15T14:32:45Z"
  runId: "1234567890"
  error: "API rate limit exceeded: 429 Too Many Requests"
```
```

### Example 3: Allowlist Configuration

**File**: `actions/allowlist.yaml`

```yaml
jira-comment:
  script: "scripts/jira-comment.py"
  version: "1.0"
  schema: "schemas/jira-comment.json"
  timeout: 60

confluence-comment:
  script: "scripts/confluence-comment.py"
  version: "1.0"
  schema: "schemas/confluence-comment.json"
  timeout: 60

github-pr-review:
  script: "scripts/github-pr-review.py"
  version: "1.0"
  schema: "schemas/github-pr-review.json"
  timeout: 120
```

### Example 4: Action Input Schema

**File**: `schemas/jira-comment.json`

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
  },
  "additionalProperties": false
}
```

### Example 5: Action Script Interface

**File**: `scripts/jira-comment.py`

```python
#!/usr/bin/env python3
import sys
import json
import os
import requests

# Read input from stdin
input_data = json.load(sys.stdin)

# Extract inputs
action = input_data["action"]
version = input_data["version"]
inputs = input_data["inputs"]

# Execute action
try:
    # Get Jira credentials from environment
    jira_url = os.environ["JIRA_URL"]
    jira_token = os.environ["JIRA_TOKEN"]
    
    # Post comment
    response = requests.post(
        f"{jira_url}/rest/api/2/issue/{inputs['ticket']}/comment",
        headers={"Authorization": f"Bearer {jira_token}"},
        json={"body": inputs["comment"]},
        timeout=30
    )
    response.raise_for_status()
    
    # Extract result
    result = response.json()
    
    # Output success
    output = {
        "status": "success",
        "outputs": {
            "commentUrl": f"{jira_url}/browse/{inputs['ticket']}#comment-{result['id']}",
            "commentId": str(result["id"])
        }
    }
    
except Exception as e:
    # Log to stderr
    print(f"Error posting Jira comment: {e}", file=sys.stderr)
    
    # Output error
    output = {
        "status": "error",
        "outputs": {},
        "error": str(e)
    }

# Write output to stdout
json.dump(output, sys.stdout)
sys.exit(0 if output["status"] == "success" else 1)
```

### Example 6: PR Validation Workflow

**File**: `.github/workflows/pr-validation.yml`

```yaml
name: Validate Action Proposals

on:
  pull_request:
    branches:
      - main
    paths:
      - 'actions/**.md'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema
      
      - name: Validate action files
        run: |
          python tools/validator.py --mode pr
        # No secrets provided - validation only
```

### Example 7: Main Execution Workflow

**File**: `.github/workflows/execute-actions.yml`

```yaml
name: Execute Actions

on:
  push:
    branches:
      - main
    paths:
      - 'actions/**.md'

concurrency:
  group: execute-actions
  cancel-in-progress: false

jobs:
  execute:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install pyyaml jsonschema requests
      
      - name: Execute pending actions
        env:
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
          CONFLUENCE_URL: ${{ secrets.CONFLUENCE_URL }}
          CONFLUENCE_TOKEN: ${{ secrets.CONFLUENCE_TOKEN }}
        run: |
          python tools/executor.py --commit
      
      - name: Commit results
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add actions/
          git diff --staged --quiet || git commit -m "Execute actions [skip ci]"
          git push
```
