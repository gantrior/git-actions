# Validator Contract

**Module**: `tools/validator.py`  
**Purpose**: Validate action entries against allowlist and schemas

---

## Public Interface

### Function: `validate_daily_file(file_path: str, allowlist_path: str, schemas_dir: str, mode: str = "pr") -> ValidationResult`

**Description**: Validate all actions in a daily file.

**Input**:
- `file_path`: Path to daily markdown file to validate
- `allowlist_path`: Path to allowlist YAML file (e.g., `actions/allowlist.yaml`)
- `schemas_dir`: Directory containing JSON schemas (e.g., `schemas/`)
- `mode`: Validation mode - `"pr"` (strict, rejects checked modifications) or `"execution"` (lenient)

**Output**: `ValidationResult` object

**Errors**:
- `FileNotFoundError`: File, allowlist, or schema not found
- `ParseError`: Malformed daily file or allowlist

**Behavior**:
- Parse daily file to extract actions
- Load allowlist configuration
- For each action:
  - Check action name exists in allowlist
  - Verify version matches allowlist version
  - Load JSON schema for action type
  - Validate inputs against schema
  - Check environment constraints
  - (PR mode only) Reject if checked actions modified
- Return validation result with all errors

---

### Class: `ValidationResult`

**Description**: Result of validating a daily file.

**Attributes**:
- `is_valid: bool` - True if all validations passed
- `errors: list[ValidationError]` - List of validation errors (empty if valid)
- `warnings: list[str]` - Non-critical warnings

**Methods**:
- `to_dict() -> dict`: Serialize to dictionary
- `print_report() -> None`: Print human-readable validation report

**Example**:
```python
result = validate_daily_file("actions/2026-01-15.md", "actions/allowlist.yaml", "schemas/")
if not result.is_valid:
    result.print_report()
    sys.exit(1)
```

---

### Class: `ValidationError`

**Description**: Represents a single validation failure.

**Attributes**:
- `action_id: str` - ID of action that failed validation
- `error_type: str` - Category of error (e.g., `"allowlist"`, `"schema"`, `"version"`, `"immutability"`)
- `message: str` - Human-readable error description
- `line_number: int | None` - Line number in file where error occurred

**Error Types**:
- `"allowlist"`: Action name not in allowlist
- `"version"`: Version mismatch between action and allowlist
- `"schema"`: Input validation failed against JSON schema
- `"immutability"`: Attempt to modify checked action (PR mode only)
- `"environment"`: Action cannot run in current environment
- `"format"`: Malformed action entry

**Format**:
```
ValidationError:
  Action: a1 (jira-comment v1.0)
  Type: schema
  Line: 42
  Message: Field 'ticket' is required but missing
```

---

### Function: `load_allowlist(allowlist_path: str) -> Allowlist`

**Description**: Load and parse allowlist YAML file.

**Input**:
- `allowlist_path`: Path to `allowlist.yaml`

**Output**: `Allowlist` object

**Errors**:
- `FileNotFoundError`: Allowlist file not found
- `AllowlistParseError`: Malformed YAML or invalid structure

---

### Class: `Allowlist`

**Description**: Parsed allowlist configuration.

**Attributes**:
- `entries: dict[str, AllowlistEntry]` - Map of action name to configuration

**Methods**:
- `get_entry(action_name: str) -> AllowlistEntry | None`: Get config for action type
- `is_allowed(action_name: str) -> bool`: Check if action is in allowlist
- `validate_version(action_name: str, version: str) -> bool`: Check version match

---

### Class: `AllowlistEntry`

**Description**: Configuration for a single action type.

**Attributes**:
- `script: str` - Path to action script
- `version: str` - Expected version
- `schema: str` - Path to JSON schema
- `timeout: int` - Timeout in seconds (default 300)
- `environment: str` - Environment constraint (`"any"`, `"ci-only"`, `"local-only"`)

**Methods**:
- `can_run_in_environment(current_env: str) -> bool`: Check if action can run in environment

---

### Function: `validate_inputs(inputs: dict, schema_path: str) -> list[str]`

**Description**: Validate action inputs against JSON schema.

**Input**:
- `inputs`: Dictionary of input parameters
- `schema_path`: Path to JSON Schema file

**Output**: List of error messages (empty if valid)

**Errors**:
- `FileNotFoundError`: Schema file not found
- `SchemaParseError`: Malformed JSON schema

**Example**:
```python
errors = validate_inputs(
    {"ticket": "PROJ-123", "comment": "Fixed"},
    "schemas/jira-comment.json"
)

if errors:
    for error in errors:
        print(f"Validation error: {error}")
```

---

## Implementation Notes

### Validation Flow

```
1. Parse daily file → list[ActionEntry]
2. Load allowlist → Allowlist
3. For each action:
   a. Check action.name in allowlist → Error if not found
   b. Check action.version == allowlist.version → Error if mismatch
   c. Load schema from allowlist.schema path
   d. Validate action.inputs against schema → Collect errors
   e. (PR mode) Check action.is_checked → Error if true and modified
4. Collect all errors → ValidationResult
```

### JSON Schema Validation

```python
from jsonschema import validate, ValidationError as SchemaValidationError
import json

def validate_inputs(inputs, schema_path):
    with open(schema_path) as f:
        schema = json.load(f)
    
    errors = []
    try:
        validate(instance=inputs, schema=schema)
    except SchemaValidationError as e:
        # Convert jsonschema errors to human-readable messages
        errors.append(f"{e.message} at {'.'.join(str(p) for p in e.path)}")
    
    return errors
```

### Environment Detection

```python
def get_current_environment() -> str:
    """Detect if running in CI or locally."""
    if os.environ.get("CI") == "true":
        return "ci"
    else:
        return "local"
```

### PR Mode vs Execution Mode

**PR Mode** (`mode="pr"`):
- Strict validation
- Reject any modification to checked actions
- No secrets available (cannot test actual execution)
- Goal: Catch format/schema errors early

**Execution Mode** (`mode="execution"`):
- Lenient validation
- Allow updating checked actions (to add outputs/meta)
- Secrets available in environment
- Goal: Prepare for safe execution

---

### Example Usage

```python
from tools.validator import validate_daily_file, ValidationResult

# In PR validation workflow
result = validate_daily_file(
    file_path="actions/2026-01-15.md",
    allowlist_path="actions/allowlist.yaml",
    schemas_dir="schemas/",
    mode="pr"
)

if not result.is_valid:
    print("❌ Validation failed:")
    result.print_report()
    sys.exit(1)
else:
    print("✅ All actions are valid")
```

**Output on error**:
```
❌ Validation failed:

actions/2026-01-15.md:
  Action 'a1' (jira-comment v1.0) - Line 42
    [schema] Field 'ticket' is required but missing
  
  Action 'a2' (confluence-comment v2.0) - Line 58
    [version] Version mismatch: action has v2.0, allowlist expects v1.0
```

---

## Test Coverage Requirements

- ✅ Validate action with valid inputs
- ✅ Detect action name not in allowlist
- ✅ Detect version mismatch
- ✅ Detect missing required input field
- ✅ Detect invalid input type (e.g., string instead of number)
- ✅ Detect invalid input pattern (e.g., malformed ticket ID)
- ✅ Detect modification to checked action (PR mode)
- ✅ Allow update to checked action (execution mode)
- ✅ Validate multiple actions in single file
- ✅ Collect all errors (don't stop at first error)
- ✅ Handle environment constraints correctly
- ✅ Load allowlist successfully
- ✅ Load JSON schemas successfully
- ✅ Generate clear error messages with line numbers
