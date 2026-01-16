# Parser Contract

**Module**: `tools/parser.py`  
**Purpose**: Parse markdown daily files to extract action entries

---

## Public Interface

### Function: `parse_daily_file(file_path: str) -> list[ActionEntry]`

**Description**: Parse a daily action file and return all action entries.

**Input**:
- `file_path`: Absolute or relative path to daily markdown file (e.g., `actions/2026-01-15.md`)

**Output**: List of `ActionEntry` objects

**Errors**:
- `FileNotFoundError`: File does not exist
- `ParseError`: Malformed action entry (includes line number and specific error)
- `IOError`: File read permission denied

**Behavior**:
- Preserves order of actions as they appear in file
- Ignores non-action markdown content (headings, comments, etc.)
- Validates action header format strictly
- Parses YAML block for each action

---

### Class: `ActionEntry`

**Description**: Represents a single parsed action from a daily file.

**Attributes**:
- `id: str` - Unique action identifier (e.g., `"a1"`, `"jira-001"`)
- `name: str` - Action type name (e.g., `"jira-comment"`)
- `version: str` - Action version (e.g., `"1.0"`)
- `is_checked: bool` - Execution status (True if `[x]`, False if `[ ]`)
- `inputs: dict` - Action-specific parameters
- `outputs: dict` - Execution results (empty until executed)
- `meta: dict` - Execution metadata (empty until executed)
- `line_number: int` - Line number where action starts (for error reporting)

**Methods**:
- `to_dict() -> dict`: Serialize to dictionary representation
- `is_pending() -> bool`: Return True if action is unchecked

**Validation**:
- `id` matches pattern `[a-zA-Z0-9-]+`
- `name` matches pattern `[a-z-]+`
- `version` matches pattern `[0-9]+\.[0-9]+`
- `inputs`, `outputs`, `meta` are valid dictionaries

---

### Exception: `ParseError`

**Description**: Raised when daily file contains malformed action entry.

**Attributes**:
- `message: str` - Human-readable error description
- `file_path: str` - Path to file being parsed
- `line_number: int` - Line number where error occurred
- `context: str` - Surrounding lines for debugging

**Format**:
```
ParseError: {file_path}:{line_number}: {message}
Context:
  {line-2}
  {line-1}
> {error line}  <-- ERROR
  {line+1}
```

---

## Implementation Notes

### Regex Pattern for Action Header

```python
ACTION_HEADER_PATTERN = r'^- \[([ x])\] `([a-zA-Z0-9-]+)` — \*([a-z-]+)\* v([0-9.]+)$'
```

Capture groups:
1. Checkbox state: `' '` or `'x'`
2. Action ID: alphanumeric + hyphens
3. Action name: lowercase + hyphens
4. Version: numbers and dots

### State Machine

```
State: SCANNING
  - If line matches ACTION_HEADER_PATTERN → State: YAML_START
  - Else → Continue scanning

State: YAML_START
  - If line is "```yaml" → State: IN_YAML_BLOCK
  - Else → Raise ParseError("Expected YAML block after action header")

State: IN_YAML_BLOCK
  - Accumulate lines
  - If line is "```" → Parse accumulated YAML → State: SCANNING
  - If EOF reached → Raise ParseError("Unclosed YAML block")
```

### Example Usage

```python
from tools.parser import parse_daily_file, ActionEntry, ParseError

try:
    actions = parse_daily_file("actions/2026-01-15.md")
    
    for action in actions:
        print(f"Action {action.id}: {action.name} v{action.version}")
        if action.is_pending():
            print("  Status: Pending execution")
        else:
            print(f"  Status: Completed at {action.meta.get('executedAt')}")
            
except ParseError as e:
    print(f"ERROR: {e}")
    sys.exit(1)
```

---

## Test Coverage Requirements

- ✅ Parse valid action entry (pending)
- ✅ Parse valid action entry (completed with outputs)
- ✅ Parse multiple actions in single file
- ✅ Preserve action order
- ✅ Ignore non-action markdown content
- ✅ Detect malformed action header (invalid ID, missing version, etc.)
- ✅ Detect malformed YAML block (syntax error, unclosed block)
- ✅ Handle empty daily file (return empty list)
- ✅ Handle file with only non-action content (return empty list)
- ✅ Provide accurate line numbers in error messages
