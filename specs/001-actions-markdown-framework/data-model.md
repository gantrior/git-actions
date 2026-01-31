# Data Model: Actions-as-Markdown Framework

**Feature**: 001-actions-markdown-framework  
**Date**: 2026-01-16

## Overview

This document defines the core entities, their attributes, relationships, and validation rules for the Actions-as-Markdown Framework. All entities are represented in markdown files and YAML configurations - no database schema.

---

## Entities

### 1. Daily Action File

**Description**: A markdown file containing all actions proposed for a specific calendar day.

**Storage**: Git repository at `actions/YYYY-MM-DD.md`

**Attributes**:
- `filename`: String matching pattern `YYYY-MM-DD.md` (e.g., `2026-01-15.md`)
- `date`: ISO 8601 date derived from filename (e.g., `2026-01-15`)
- `actions`: List of Action Entries (0 to N, typically 10-50 per day)
- `free_text`: Non-action markdown content (headings, comments, etc.)

**Validation Rules**:
- Filename MUST match regex `^\d{4}-\d{2}-\d{2}\.md$`
- Date portion MUST be a valid calendar date
- File size SHOULD NOT exceed 100KB
- Actions MUST have unique IDs within the file

**Relationships**:
- Contains 0..N Action Entries
- Each Action Entry references an Allowlist Entry

**State Transitions**:
1. **Created** → File created when first action is proposed
2. **Modified** → New actions added via PR
3. **Merged** → PR merged to main, actions become pending
4. **Executing** → Execution workflow processes actions
5. **Complete** → All actions marked as checked

**Lifecycle**:
```
[PR Created] → [Validation] → [Merged to main] → [Execution] → [Auto-commit results]
```

---

### 2. Action Entry

**Description**: A single executable action within a daily file, represented by a checkbox line + YAML block.

**Storage**: Inline within Daily Action File

**Attributes**:
- `id`: String, unique within daily file (e.g., `a1`, `jira-001`)
- `name`: String, action type name (e.g., `jira-comment`, must exist in allowlist)
- `version`: String, semantic version (e.g., `1.0`, `2.1`)
- `is_checked`: Boolean, execution status (`[ ]` = false, `[x]` = true)
- `inputs`: Object (action-specific parameters, validated against schema)
- `outputs`: Object (results from execution, empty until executed)
- `meta`: Object (execution metadata: `executedAt`, `runId`, `error`)

**Validation Rules**:
- `id` MUST match pattern `[a-zA-Z0-9-]+`
- `id` MUST be unique within daily file
- `name` MUST exist in allowlist
- `version` MUST match allowlist version exactly
- `inputs` MUST validate against JSON schema for that action
- `is_checked` = false → `outputs` and `meta` MUST be empty objects `{}`
- `is_checked` = true → `meta.executedAt` and `meta.runId` MUST be present
- Checked actions are IMMUTABLE (PRs modifying them MUST be rejected)

**Relationships**:
- Belongs to exactly 1 Daily Action File
- References exactly 1 Allowlist Entry (by `name`)
- References exactly 1 Action Schema (via allowlist entry)
- MAY reference 1 Action Script (if `name` is in allowlist)

**State Transitions**:
1. **Proposed** → `is_checked = false`, `outputs = {}`, `meta = {}`
2. **Executing** → Script invoked, results pending
3. **Completed** → `is_checked = true`, outputs and meta populated
4. **Failed** → `is_checked = true`, `meta.error` populated, `outputs = {}`

**Format Example**:
```markdown
- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Fixed bug"
outputs: {}
meta: {}
```
```

After execution:
```markdown
- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Fixed bug"
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
  commentId: "456"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```
```

---

### 3. Allowlist Entry

**Description**: Registry entry defining a valid action type, its script, schema, and execution constraints.

**Storage**: YAML file at `actions/allowlist.yaml`

**Attributes**:
- `action_name`: String, unique identifier for action type (e.g., `jira-comment`)
- `script`: String, path to executable script (e.g., `scripts/jira-comment.py`)
- `version`: String, semantic version (e.g., `1.0`)
- `schema`: String, path to JSON schema file (e.g., `schemas/jira-comment.json`)
- `timeout`: Integer, max execution time in seconds (default 300)
- `environment`: Enum, execution environment constraint (`any`, `ci-only`, `local-only`)

**Validation Rules**:
- `action_name` MUST match pattern `[a-z-]+` (lowercase with hyphens)
- `script` MUST be a valid file path to an executable script
- `version` MUST match pattern `[0-9]+\.[0-9]+`
- `schema` MUST be a valid file path to a JSON Schema file
- `timeout` MUST be positive integer, max 3600 (1 hour)
- `environment` MUST be one of: `any`, `ci-only`, `local-only`

**Relationships**:
- Referenced by 0..N Action Entries
- References 1 Action Schema (via `schema` path)
- References 1 Action Script (via `script` path)

**Example**:
```yaml
jira-comment:
  script: "scripts/jira-comment.py"
  version: "1.0"
  schema: "schemas/jira-comment.json"
  timeout: 60
  environment: "any"

github-pr-review:
  script: "scripts/github-pr-review.py"
  version: "1.0"
  schema: "schemas/github-pr-review.json"
  timeout: 120
  environment: "ci-only"
```

---

### 4. Action Schema

**Description**: JSON Schema document defining required and optional input fields for an action type.

**Storage**: JSON file at `schemas/{action-name}.json`

**Attributes**:
- `$schema`: String, JSON Schema version (typically `http://json-schema.org/draft-07/schema#`)
- `type`: String, always `"object"` for action inputs
- `required`: Array of strings, required field names
- `properties`: Object, field definitions with types, patterns, constraints
- `additionalProperties`: Boolean, typically `false` to prevent unknown fields

**Validation Rules**:
- MUST be valid JSON Schema Draft 7 document
- `type` MUST be `"object"`
- `required` array MUST list all mandatory input fields
- Each property SHOULD have clear `description`

**Relationships**:
- Referenced by exactly 1 Allowlist Entry
- Used to validate 0..N Action Entry inputs

**Example** (schemas/jira-comment.json):
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

---

### 5. Action Script

**Description**: Executable program that performs the action (posts to API, runs command, etc.).

**Storage**: File at path specified in allowlist (e.g., `scripts/jira-comment.py`)

**Interface**:
- **Input**: JSON on stdin with format:
  ```json
  {
    "action": "jira-comment",
    "version": "1.0",
    "inputs": {
      "ticket": "PROJ-123",
      "comment": "Fixed bug"
    }
  }
  ```
- **Output**: JSON on stdout with format:
  ```json
  {
    "status": "success",
    "outputs": {
      "commentUrl": "https://jira.example.com/...",
      "commentId": "456"
    }
  }
  ```
  OR on error:
  ```json
  {
    "status": "error",
    "outputs": {},
    "error": "API rate limit exceeded: 429 Too Many Requests"
  }
  ```
- **Exit code**: 0 for success, non-zero for error
- **Stderr**: Diagnostic logs (not captured in action results)

**Validation Rules**:
- MUST have execute permission (`chmod +x`)
- MUST accept JSON on stdin
- MUST output valid JSON on stdout
- MUST exit within timeout period
- MUST NOT write secrets to stdout or stderr

**Relationships**:
- Referenced by exactly 1 Allowlist Entry
- Executed by 0..N Action Entries

---

### 6. Execution Metadata

**Description**: Metadata recorded after action execution (success or failure).

**Storage**: Inline within Action Entry `meta` field

**Attributes**:
- `executedAt`: ISO 8601 timestamp (e.g., `"2026-01-15T14:32:11Z"`)
- `runId`: String, GitHub Actions workflow run ID (e.g., `"1234567890"`)
- `error`: String, error message if execution failed (optional, only present if status = error)

**Validation Rules**:
- `executedAt` MUST be valid ISO 8601 timestamp with timezone
- `runId` MUST be non-empty string
- `error` field SHOULD be present only when execution failed

**Lifecycle**:
- Created when action execution completes (success or failure)
- Immutable once written (checkbox prevents re-execution)

---

## Relationships Diagram

```
Daily Action File (1)
  ├─ contains ──> Action Entry (0..N)
  │                 ├─ references ──> Allowlist Entry (1)
  │                 │                   ├─ references ──> Action Schema (1)
  │                 │                   └─ references ──> Action Script (1)
  │                 └─ contains ──> Execution Metadata (0..1)
  └─ stored in ──> Git Repository
```

---

## Key Invariants

1. **Uniqueness**: Action IDs unique within daily file, not globally
2. **Immutability**: Checked actions (`[x]`) cannot be modified
3. **Append-only**: Daily files grow by appending actions (no deletions during normal operation)
4. **Version matching**: Action entry version MUST match allowlist version exactly
5. **Schema compliance**: Action inputs MUST validate against schema before execution
6. **Environment constraints**: Actions with `ci-only` skip when run locally, `local-only` skip in CI
7. **Atomic execution**: Each action execution + commit is atomic (no partial states)

---

## Data Flow

```
[Developer proposes action in PR]
  ↓ (validation - no execution)
[PR validation workflow]
  ├─ Parse daily file → Action Entries
  ├─ Check action names exist in Allowlist
  ├─ Validate inputs against Schema
  ├─ Reject if checked actions modified
  └─ PASS or FAIL (no external calls)

[PR merged to main]
  ↓ (execution workflow triggered)
[Execution workflow]
  ├─ Parse daily file → Action Entries
  ├─ Filter to unchecked actions
  ├─ For each unchecked action:
  │   ├─ Load Allowlist Entry
  │   ├─ Check environment constraint
  │   ├─ Invoke Action Script (stdin/stdout)
  │   ├─ Capture outputs or error
  │   ├─ Update Action Entry (check box, populate outputs/meta)
  │   └─ Commit + push immediately
  └─ Complete (all actions processed)
```

---

## State Machine: Action Entry

```
┌─────────────┐
│  Proposed   │  is_checked = false, outputs = {}, meta = {}
│  [ ] action │
└──────┬──────┘
       │ (merge to main)
       ↓
┌─────────────┐
│  Pending    │  Unchecked, waiting for execution workflow
│  [ ] action │
└──────┬──────┘
       │ (execution workflow starts)
       ↓
┌─────────────┐
│  Executing  │  Script running, results pending
└──────┬──────┘
       │
       ├─ (success) ──────────────────────┐
       │                                   ↓
       │                          ┌─────────────┐
       │                          │  Completed  │  [x], outputs populated
       │                          │  [x] action │
       │                          └─────────────┘
       │
       └─ (failure) ──────────────────────┐
                                          ↓
                                 ┌─────────────┐
                                 │   Failed    │  [x], error in meta
                                 │  [x] action │
                                 └─────────────┘
```

---

## Example Data Flow: Jira Comment Action

1. **Proposal** (PR):
   ```markdown
   - [ ] `a1` — *jira-comment* v1.0
   ```yaml
   inputs:
     ticket: PROJ-123
     comment: "Fixed authentication bug"
   outputs: {}
   meta: {}
   ```
   ```

2. **Validation**:
   - Parse action entry → Extract `jira-comment`, v1.0, inputs
   - Load `actions/allowlist.yaml` → Find `jira-comment` entry
   - Load `schemas/jira-comment.json` → Validate inputs
   - Check: `ticket` matches pattern `^[A-Z]+-[0-9]+$` ✓
   - Check: `comment` is non-empty string ✓
   - Result: PASS

3. **Merge to main** → Execution workflow triggered

4. **Execution**:
   - Parse daily file → Find unchecked actions
   - Action `a1` is unchecked → Execute
   - Load allowlist → `script: scripts/jira-comment.py`, `timeout: 60`
   - Invoke script:
     ```bash
     echo '{"action":"jira-comment","version":"1.0","inputs":{...}}' | scripts/jira-comment.py
     ```
   - Script outputs:
     ```json
     {"status":"success","outputs":{"commentUrl":"https://...","commentId":"456"}}
     ```
   - Update action entry → Check box, populate outputs and meta
   - Commit to git with message: `Execute action a1 [skip ci]`
   - Push to main

5. **Final state**:
   ```markdown
   - [x] `a1` — *jira-comment* v1.0
   ```yaml
   inputs:
     ticket: PROJ-123
     comment: "Fixed authentication bug"
   outputs:
     commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
     commentId: "456"
   meta:
     executedAt: "2026-01-15T14:32:11Z"
     runId: "1234567890"
   ```
   ```

---

## Conclusion

This data model provides a complete specification of all entities, their attributes, relationships, and state transitions for the Actions-as-Markdown Framework. All entities are text-based (markdown, YAML, JSON) with no database required. The model supports the full lifecycle from proposal to execution to audit.
