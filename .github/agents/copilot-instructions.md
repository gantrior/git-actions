# git-actions Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-16

## Active Technologies
- Python 3.9+ + PyYAML (>=6.0), jsonschema (>=4.17.0), requests (>=2.28.0) (002-ai-action-hooks)
- Files (YAML for hook configurations, markdown for action audit trail) (002-ai-action-hooks)

- Python 3.9+ + PyYAML (YAML parsing), jsonschema (schema validation), requests (HTTP for action scripts) (001-actions-markdown-framework)

## Project Structure

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

## Commands

```bash
# Run tests
cd tools && pytest

# Validate daily file
python tools/validator.py --file actions/2026-01-15.md --mode pr

# Execute pending actions (local testing)
python tools/executor.py --file actions/2026-01-15.md

# Lint Python code
ruff check tools/ scripts/
```

## Code Style

Python 3.9+: Follow PEP 8, use type hints, small functions (≤15 lines per constitution)

## Recent Changes
- 002-ai-action-hooks: Added Python 3.9+ + PyYAML (>=6.0), jsonschema (>=4.17.0), requests (>=2.28.0)

- 001-actions-markdown-framework: Added Python 3.9+ + PyYAML (YAML parsing), jsonschema (schema validation), requests (HTTP for action scripts)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
