# Research: Actions-as-Markdown Framework

**Feature**: 001-actions-markdown-framework  
**Date**: 2026-01-16  
**Status**: Complete

## Overview

This document captures research findings, technical decisions, and alternatives considered for implementing the Actions-as-Markdown Framework. All NEEDS CLARIFICATION items from Technical Context have been resolved.

---

## 1. Markdown Parsing Strategy

### Decision: Regex + Line-by-Line State Machine

**Rationale**:
- Action entries have a well-defined structure: checkbox line + YAML fence
- Line-by-line parsing preserves non-action content exactly (critical for stable diffs)
- Regex pattern matches exact format: `- [ ] \`action-id\` — *action-name* vVersion`
- State machine tracks whether we're inside a YAML block or outside

**Implementation approach**:
```python
# Pattern to match action header
ACTION_HEADER_PATTERN = r'^- \[([ x])\] `([a-zA-Z0-9-]+)` — \*([a-z-]+)\* v([0-9.]+)$'

# State machine:
# 1. Match header line → extract metadata
# 2. Next line must be "```yaml"
# 3. Collect lines until closing "```"
# 4. Parse YAML content
```

**Alternatives considered**:
1. **Full markdown parser (e.g., markdown-it-py)**: Rejected - too heavyweight, would require tree traversal and custom node types. Adds unnecessary complexity for our simple format.
2. **YAML frontmatter approach**: Rejected - would change the visual format significantly. Frontmatter is typically at file start, not per-action.
3. **JSON embedded in markdown**: Rejected - YAML is more human-readable for multiline strings (using `|` for literals).

**Best practices source**: Python `re` module documentation, state machine patterns from compiler theory.

---

## 2. YAML Parsing and Safety

### Decision: PyYAML with safe_load

**Rationale**:
- PyYAML is the standard Python YAML library (included in stdlib-adjacent)
- `yaml.safe_load()` prevents arbitrary code execution
- Handles nested structures, multiline strings, and escaping automatically

**Implementation approach**:
```python
import yaml

def parse_yaml_block(yaml_text: str) -> dict:
    try:
        return yaml.safe_load(yaml_text)
    except yaml.YAMLError as e:
        raise ParseError(f"Invalid YAML: {e}")
```

**Alternatives considered**:
1. **ruamel.yaml**: Rejected - better for round-trip editing but overkill for our use case. We edit markdown, not YAML directly.
2. **Custom YAML subset parser**: Rejected - reinventing the wheel. PyYAML is battle-tested and sufficient.
3. **JSON instead of YAML**: Rejected - JSON doesn't support multiline strings cleanly without escaping.

**Best practices source**: PyYAML documentation, OWASP recommendations for safe deserialization.

---

## 3. In-Place Markdown Editing

### Decision: Parse → Modify → Reconstruct

**Rationale**:
- Preserve exact formatting and whitespace outside action entries
- Update only the specific action entry being modified
- Generate minimal git diffs (only changed lines)

**Implementation approach**:
```python
def update_action_entry(file_path: str, action_id: str, updates: dict):
    lines = read_file_lines(file_path)
    output_lines = []
    
    in_target_action = False
    in_yaml_block = False
    
    for line in lines:
        if matches_action_header(line):
            current_id = extract_action_id(line)
            if current_id == action_id:
                in_target_action = True
                # Generate updated header and YAML
                output_lines.extend(generate_action_entry(action_id, updates))
                # Skip original YAML block
                continue
        
        if in_target_action and line.startswith("```yaml"):
            in_yaml_block = True
            continue
        
        if in_target_action and in_yaml_block and line.startswith("```"):
            in_yaml_block = False
            in_target_action = False
            continue
        
        if not in_target_action:
            output_lines.append(line)
    
    write_file_lines(file_path, output_lines)
```

**Alternatives considered**:
1. **AST-based editing**: Rejected - markdown AST doesn't preserve formatting perfectly. Would cause whitespace churn.
2. **Sed/awk for editing**: Rejected - harder to test, platform-dependent, error-prone for multiline blocks.
3. **Append-only editing**: Rejected - would grow files indefinitely and make manual review harder.

**Best practices source**: Git diff minimization principles, Linux text processing patterns.

---

## 4. JSON Schema Validation

### Decision: jsonschema library with Draft 7

**Rationale**:
- Industry-standard Python implementation
- Supports all JSON Schema Draft 7 features (patterns, required fields, types)
- Clear error messages for validation failures
- Used by OpenAPI tools, making schemas portable

**Implementation approach**:
```python
from jsonschema import validate, ValidationError
import json

def validate_action_inputs(action_name: str, inputs: dict, schema_path: str):
    with open(schema_path) as f:
        schema = json.load(f)
    
    try:
        validate(instance=inputs, schema=schema)
    except ValidationError as e:
        raise ActionValidationError(
            f"Action '{action_name}' inputs invalid: {e.message}"
        )
```

**Alternatives considered**:
1. **Pydantic models**: Rejected - requires defining Python classes for each action. JSON Schema is more portable and language-agnostic.
2. **Custom validation logic**: Rejected - schema evolution would require code changes. JSON Schema is declarative.
3. **Cerberus**: Rejected - smaller ecosystem, less tooling support than JSON Schema.

**Best practices source**: JSON Schema specification (draft-07), OpenAPI schema practices.

---

## 5. Action Script Execution Model

### Decision: Subprocess with stdin/stdout JSON + Timeout

**Rationale**:
- Language-agnostic: scripts can be Python, Bash, Node.js, etc.
- stdin/stdout is universal IPC mechanism
- JSON is simple to parse in any language
- subprocess.run() provides timeout and error handling

**Implementation approach**:
```python
import subprocess
import json

def execute_action_script(script_path: str, inputs: dict, timeout: int) -> dict:
    input_json = json.dumps({
        "action": action_name,
        "version": version,
        "inputs": inputs
    })
    
    result = subprocess.run(
        [script_path],
        input=input_json,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=os.environ  # Pass secrets via environment
    )
    
    if result.returncode != 0:
        return {
            "status": "error",
            "outputs": {},
            "error": result.stderr or "Script exited with non-zero code"
        }
    
    return json.loads(result.stdout)
```

**Alternatives considered**:
1. **HTTP API for actions**: Rejected - requires running a server, adds deployment complexity. Scripts are simpler.
2. **File-based communication**: Rejected - slower, requires temp file management, race conditions possible.
3. **Python-only actions (import modules)**: Rejected - limits extensibility. Users can't use other languages.

**Best practices source**: Unix philosophy (small tools, stdin/stdout), subprocess best practices from Python docs.

---

## 6. Concurrency Control

### Decision: GitHub Actions concurrency groups + File-level locking

**Rationale**:
- GitHub Actions provides built-in `concurrency: group` feature
- Prevents multiple execution workflows from running simultaneously
- File-level locking not needed - GitHub handles serialization
- Single execution workflow processes all changed files in one run

**Implementation approach**:
```yaml
# .github/workflows/execute-actions.yml
concurrency:
  group: execute-actions
  cancel-in-progress: false  # Don't cancel - let queued runs execute
```

**Alternatives considered**:
1. **Git-based locking (lockfiles)**: Rejected - race conditions possible, cleanup issues if workflow crashes.
2. **Database locking**: Rejected - no database in this system. Violates simplicity constraint.
3. **Redis/distributed lock**: Rejected - external dependency, overkill for single-repo use case.

**Best practices source**: GitHub Actions concurrency documentation, distributed systems patterns.

---

## 7. Git Auto-Commit Strategy

### Decision: Immediate commit per action + [skip ci] tag

**Rationale**:
- Commit after each action execution prevents lost work if workflow crashes mid-run
- `[skip ci]` prevents infinite execution loops (merge triggers execution triggers commit triggers execution...)
- Git conflicts are rare (execution workflow has exclusive lock)
- If conflict occurs, append execution result at top of file

**Implementation approach**:
```python
def commit_action_result(file_path: str, action_id: str):
    subprocess.run(["git", "add", file_path], check=True)
    
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        capture_output=True
    )
    
    if result.returncode != 0:  # There are changes
        subprocess.run(
            ["git", "commit", "-m", f"Execute action {action_id} [skip ci]"],
            check=True
        )
        subprocess.run(["git", "push"], check=True)
```

**Alternatives considered**:
1. **Batch commit after all actions**: Rejected - if workflow fails mid-run, lose all results. Partial state is valuable.
2. **Separate audit log file**: Rejected - violates spec requirement for inline results. Harder to correlate actions with results.
3. **No auto-commit (manual review)**: Rejected - defeats automation purpose. Human review happens at PR stage.

**Best practices source**: GitHub Actions workflow patterns, Git commit strategies for automation.

---

## 8. Error Handling Philosophy

### Decision: Fail-safe with detailed error messages

**Rationale**:
- Parsing errors MUST halt immediately (corrupt data is worse than no data)
- Execution errors MUST NOT halt (one action failure shouldn't block others)
- All errors MUST include context (file, line, action ID, field)

**Implementation approach**:
```python
# Parser: halt on error
def parse_daily_file(file_path: str) -> list[Action]:
    try:
        return parse_actions(file_path)
    except ParseError as e:
        print(f"ERROR: {file_path}:{e.line}: {e.message}")
        sys.exit(1)  # Fail fast

# Executor: continue on error
def execute_actions(actions: list[Action]):
    for action in actions:
        try:
            result = execute_action(action)
        except Exception as e:
            result = {"status": "error", "error": str(e)}
        
        # Always record result, even if error
        update_action_entry(action.id, result)
```

**Alternatives considered**:
1. **Warnings instead of errors**: Rejected - silent failures lead to corrupt state. Better to be explicit.
2. **Retry logic**: Rejected - out of scope (OOS-007). Failed actions require manual re-proposal.
3. **Error accumulation with summary**: Rejected - loses context. Immediate error output is clearer.

**Best practices source**: Erlang "let it crash" philosophy (adapted), Python error handling guidelines.

---

## 9. Testing Strategy

### Decision: Golden file tests + Mock action scripts

**Rationale**:
- Golden files provide clear before/after examples
- Easy to review test expectations (human-readable markdown)
- Mock scripts avoid external API dependencies in tests
- Pytest fixtures provide clean test setup/teardown

**Implementation approach**:
```python
# tests/fixtures/sample-day-pending.md (before execution)
# tests/fixtures/sample-day-complete.md (after execution)

def test_execute_actions_updates_file():
    # Copy fixture to temp location
    temp_file = copy_fixture("sample-day-pending.md")
    
    # Execute with mock script
    execute_actions_from_file(temp_file, mock_script_dir)
    
    # Compare with expected output
    expected = read_fixture("sample-day-complete.md")
    actual = read_file(temp_file)
    
    assert actual == expected
```

**Mock action script**:
```python
#!/usr/bin/env python3
# tests/mock_actions/mock-success.py
import sys, json
input_data = json.load(sys.stdin)
output = {"status": "success", "outputs": {"result": "mocked"}}
json.dump(output, sys.stdout)
```

**Alternatives considered**:
1. **Property-based testing (Hypothesis)**: Rejected - overkill for deterministic parsing. Golden files are clearer.
2. **Live API integration tests**: Rejected - flaky, slow, requires credentials. Mock scripts are faster and reliable.
3. **Snapshot testing**: Rejected - similar to golden files but less explicit about expectations.

**Best practices source**: Pytest documentation, golden file testing patterns from compiler projects.

---

## 10. Idempotent Execution

### Decision: Check checkbox state before execution

**Rationale**:
- Checkbox `[x]` vs `[ ]` is source of truth for "already executed"
- Simple boolean check before invoking script
- Handles workflow re-runs gracefully (no duplicate API calls)

**Implementation approach**:
```python
def execute_pending_actions(actions: list[Action]):
    for action in actions:
        if action.is_checked:
            print(f"Skipping {action.id} (already executed)")
            continue
        
        # Execute unchecked actions only
        result = execute_action_script(action)
        update_and_commit(action.id, result)
```

**Alternatives considered**:
1. **Execution timestamp tracking**: Rejected - checkbox is simpler and visible in markdown.
2. **Database of executed action IDs**: Rejected - no database in system. Markdown is source of truth.
3. **Hash-based change detection**: Rejected - if inputs change, validation should catch it. Checkbox is sufficient.

**Best practices source**: Idempotency patterns from infrastructure-as-code tools (Terraform, Ansible).

---

## Summary of Key Decisions

| Area | Decision | Why |
|------|----------|-----|
| Parsing | Regex + state machine | Simple, preserves formatting |
| YAML | PyYAML safe_load | Industry standard, secure |
| Editing | In-place reconstruction | Minimal diffs |
| Validation | jsonschema library | Portable, standard |
| Execution | Subprocess stdin/stdout | Language-agnostic |
| Concurrency | GitHub Actions groups | Built-in, reliable |
| Auto-commit | Per-action + [skip ci] | Fail-safe, no loops |
| Errors | Halt parse, continue execute | Balanced safety |
| Testing | Golden files + mocks | Clear, fast |
| Idempotency | Checkbox state check | Simple, visible |

---

## No Further Clarifications Needed

All technical context items from plan.md are now resolved:
- ✅ Language/Version: Python 3.9+ confirmed
- ✅ Dependencies: PyYAML, jsonschema, requests selected
- ✅ Testing: pytest with golden files decided
- ✅ Constraints: Addressed via design decisions above

**Phase 0 complete.** Ready for Phase 1 (Data Model & Contracts).
