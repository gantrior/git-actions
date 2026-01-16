# Implementation Plan: Actions-as-Markdown Framework

**Branch**: `001-actions-markdown-framework` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-actions-markdown-framework/spec.md`

## Summary

The Actions-as-Markdown Framework enables AI assistants and developers to propose automated actions (e.g., posting Jira comments) as reviewable PRs by editing markdown files. Actions are stored in daily markdown files (`actions/YYYY-MM-DD.md`) with a max-compact format (checkbox + YAML block). No action executes until the PR is merged to `main`. After execution, the system auto-commits results back to `main` by checking off the action and appending outputs inline. The framework provides safety through PR validation, human review, and an append-only audit trail.

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: PyYAML (YAML parsing), jsonschema (schema validation), requests (HTTP for action scripts)  
**Storage**: Git repository (daily markdown files in `actions/` directory, no external database)  
**Testing**: pytest (unit tests, integration tests with fixtures), mock action scripts  
**Target Platform**: GitHub Actions (CI/CD), Linux (ubuntu-latest runner)  
**Project Type**: single (CLI tools + workflow automation scripts)  
**Performance Goals**: PR validation <30s for 50 actions, execution <10min for 20 actions (30s avg per action)  
**Constraints**: Markdown human-readable/editable, daily files <100KB, no secrets in markdown, action timeout 5min default  
**Scale/Scope**: 1-10 users, 10-50 actions/day, single repository

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Self-Documenting Code ✓
- **Status**: COMPLIANT
- **Rationale**: Python allows descriptive function names (e.g., `parse_action_entry`, `validate_against_schema`, `execute_action_with_timeout`). Domain concepts from spec (action entry, allowlist, daily file) map directly to code structures.

### II. Small Functions by Construction ✓
- **Status**: COMPLIANT
- **Rationale**: Parser, editor, validator, and executor can be decomposed into small functions (parse header, extract YAML, check schema, invoke script, update checkbox). Target ≤15 lines per function is achievable.

### III. Decomposition over Explanation ✓
- **Status**: COMPLIANT
- **Rationale**: Complex operations (parse daily file, execute actions sequentially, commit results) naturally decompose into pipelines of well-named functions. No need for explanatory comments.

### IV. Why-Only Comments Rule ✓
- **Status**: COMPLIANT
- **Rationale**: Few WHY comments needed: (1) why sequential not parallel execution, (2) why idempotent execution check, (3) why concurrency lock. No "what" comments required.

### V. Naming Is Architecture ✓
- **Status**: COMPLIANT
- **Rationale**: Spec provides clear domain language: action entry, allowlist, inputs/outputs/meta, pending/completed. Names reflect spec terminology directly.

### VI. Spec-First, Test-First Development ✓
- **Status**: COMPLIANT
- **Rationale**: Spec already written with acceptance criteria (FR-067 to FR-074). Tests use golden file fixtures (FR-057 to FR-066). Implementation follows spec exactly.

### VII. Simplicity and Explicitness ✓
- **Status**: COMPLIANT
- **Rationale**: No hidden side effects. Parser reads, validator validates, executor executes + commits. Each tool has single responsibility. YAGNI applied (no retry logic, no scheduling, no rollback per OOS).

**GATE RESULT**: ✅ **PASSED** - All constitution principles are satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-actions-markdown-framework/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
actions/                 # Daily action files (created on demand)
  YYYY-MM-DD.md          # Daily action entries
  allowlist.yaml         # Action type registry

scripts/                 # Action implementation scripts
  jira-comment.py        # Example: post Jira comment
  confluence-comment.py  # Example: post Confluence comment

schemas/                 # JSON schemas for action inputs
  jira-comment.json      # Schema for jira-comment action
  confluence-comment.json

tools/                   # Core framework utilities
  parser.py              # Parse markdown actions
  editor.py              # In-place markdown editor
  validator.py           # Schema + allowlist validator
  executor.py            # Action execution engine

.github/
  workflows/
    pr-validation.yml    # PR validation workflow (no execution)
    execute-actions.yml  # Main execution workflow (post-merge)

tests/
  unit/
    test_parser.py       # Parser unit tests
    test_editor.py       # Editor unit tests
    test_validator.py    # Validator unit tests
  integration/
    test_end_to_end.py   # Full workflow tests
  fixtures/
    sample-day-pending.md   # Before execution
    sample-day-complete.md  # After execution
```

**Structure Decision**: Single project structure selected. All tools are Python CLI scripts with clear separation of concerns (parsing, validation, execution). GitHub Actions workflows orchestrate the tools. No frontend/backend split needed - this is a pure automation framework.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. This section intentionally left empty.

---

## Phase Completion Status

### ✅ Phase 0: Research (Complete)

**Output**: `research.md`

**Summary**: All technical unknowns resolved. Key decisions documented:
- Markdown parsing: Regex + state machine
- YAML handling: PyYAML safe_load
- Validation: jsonschema library
- Execution: subprocess stdin/stdout
- Concurrency: GitHub Actions groups
- Testing: Golden files + mock scripts

### ✅ Phase 1: Design & Contracts (Complete)

**Outputs**:
- `data-model.md` - 6 core entities with full lifecycle definitions
- `contracts/parser-contract.md` - Parse daily files to ActionEntry objects
- `contracts/editor-contract.md` - Update actions with minimal diffs
- `contracts/validator-contract.md` - Validate against allowlist and schemas
- `contracts/executor-contract.md` - Execute actions and commit results
- `quickstart.md` - Complete user guide for proposing actions
- `.github/agents/copilot-instructions.md` - Updated agent context

**Constitution Re-check**: ✅ **PASSED**
- Data model uses clear domain names (ActionEntry, Allowlist, Daily File)
- Contracts specify small, focused interfaces (parse, validate, execute)
- No hidden complexity introduced
- All behavior explicit and testable

### ⏸️ Phase 2: Tasks (Deferred)

Phase 2 (task breakdown) will be handled by the `/speckit.tasks` command, not by `/speckit.plan`. This command stops after Phase 1 planning as designed.
