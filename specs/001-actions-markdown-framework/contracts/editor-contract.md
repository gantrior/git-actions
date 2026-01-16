# Editor Contract

**Module**: `tools/editor.py`  
**Purpose**: Update action entries in daily files with minimal diffs

---

## Public Interface

### Function: `update_action_entry(file_path: str, action_id: str, updates: ActionUpdate) -> None`

**Description**: Update a specific action entry in-place, preserving all other content.

**Input**:
- `file_path`: Path to daily markdown file
- `action_id`: ID of action to update (e.g., `"a1"`)
- `updates`: `ActionUpdate` object containing fields to modify

**Output**: None (modifies file in-place)

**Errors**:
- `FileNotFoundError`: File does not exist
- `ActionNotFoundError`: No action with specified ID exists in file
- `InvalidUpdateError`: Attempting to modify immutable checked action
- `IOError`: File write permission denied

**Behavior**:
- Locate action entry by ID
- Verify action is not checked (if modifying inputs)
- Replace only the targeted action entry
- Preserve exact formatting and whitespace of all other content
- Generate minimal git diff (only changed lines)

**Immutability Rules**:
- Cannot modify checked actions (`[x]`) in general
- Exception: Execution workflow CAN update checked actions to add outputs/meta
- PR validation MUST reject any PR modifying checked actions

---

### Class: `ActionUpdate`

**Description**: Specifies which fields to update in an action entry.

**Attributes**:
- `check: bool | None` - Set to True to check the action, False to uncheck, None to leave unchanged
- `outputs: dict | None` - New outputs (replaces existing), None to leave unchanged
- `meta: dict | None` - New metadata (replaces existing), None to leave unchanged

**Validation**:
- At least one field must be non-None
- Cannot set `check=False` if action is already checked (immutability)
- Cannot modify `inputs` (inputs are immutable once action is proposed)

**Example**:
```python
# Check action and add outputs
update = ActionUpdate(
    check=True,
    outputs={"commentUrl": "https://..."},
    meta={"executedAt": "2026-01-15T14:32:11Z", "runId": "123"}
)
```

---

### Exception: `ActionNotFoundError`

**Description**: Raised when specified action ID does not exist in file.

**Attributes**:
- `action_id: str` - The action ID that was not found
- `file_path: str` - Path to file that was searched

**Format**:
```
ActionNotFoundError: Action 'a1' not found in actions/2026-01-15.md
```

---

### Exception: `InvalidUpdateError`

**Description**: Raised when attempting an invalid update (e.g., modifying checked action).

**Attributes**:
- `message: str` - Description of why update is invalid
- `action_id: str` - Action that was targeted

**Format**:
```
InvalidUpdateError: Cannot modify checked action 'a1' (action is immutable)
```

---

## Implementation Notes

### Update Algorithm

```python
def update_action_entry(file_path, action_id, updates):
    lines = read_file_lines(file_path)
    output_lines = []
    
    found = False
    in_target_action = False
    in_yaml_block = False
    
    for i, line in enumerate(lines):
        # Check if this line is an action header
        match = ACTION_HEADER_PATTERN.match(line)
        if match:
            current_id = match.group(2)
            if current_id == action_id:
                found = True
                in_target_action = True
                
                # Validate update is allowed
                is_checked = match.group(1) == 'x'
                if is_checked and updates.inputs is not None:
                    raise InvalidUpdateError(f"Cannot modify inputs of checked action '{action_id}'")
                
                # Generate updated action entry
                updated_entry = generate_action_entry(
                    action_id=action_id,
                    name=match.group(3),
                    version=match.group(4),
                    is_checked=updates.check if updates.check is not None else is_checked,
                    inputs=original_inputs,  # Preserve inputs
                    outputs=updates.outputs if updates.outputs is not None else original_outputs,
                    meta=updates.meta if updates.meta is not None else original_meta
                )
                output_lines.extend(updated_entry)
                continue
        
        # Skip original YAML block for target action
        if in_target_action and line.startswith("```yaml"):
            in_yaml_block = True
            continue
        
        if in_target_action and in_yaml_block and line.startswith("```"):
            in_yaml_block = False
            in_target_action = False
            continue
        
        if in_target_action and in_yaml_block:
            # Skip lines in original YAML block
            continue
        
        # Preserve all non-target lines
        if not in_target_action:
            output_lines.append(line)
    
    if not found:
        raise ActionNotFoundError(action_id, file_path)
    
    write_file_lines(file_path, output_lines)
```

### Diff Minimization

**Goal**: Only changed action entry appears in git diff

**Strategy**:
1. Preserve exact whitespace and formatting outside target action
2. Don't reorder actions
3. Don't modify unrelated YAML blocks
4. Use consistent indentation for YAML (2 spaces)

**Bad diff** (modifies unrelated lines):
```diff
- # Actions for 2026-01-15
+ # Actions for 2026-01-15  
  
- - [ ] `a1` — *jira-comment* v1.0
+ - [x] `a1` — *jira-comment* v1.0
```

**Good diff** (only target action):
```diff
- - [ ] `a1` — *jira-comment* v1.0
+ - [x] `a1` — *jira-comment* v1.0
  ```yaml
  inputs:
    ticket: PROJ-123
-   comment: "Fixed bug"
- outputs: {}
- meta: {}
+   comment: "Fixed bug"  
+ outputs:
+   commentUrl: "https://..."
+ meta:
+   executedAt: "2026-01-15T14:32:11Z"
```

---

### Example Usage

```python
from tools.editor import update_action_entry, ActionUpdate, InvalidUpdateError

try:
    # Mark action as complete and add results
    update = ActionUpdate(
        check=True,
        outputs={"commentUrl": "https://jira.example.com/..."},
        meta={
            "executedAt": "2026-01-15T14:32:11Z",
            "runId": "1234567890"
        }
    )
    
    update_action_entry("actions/2026-01-15.md", "a1", update)
    print("Action a1 marked as complete")
    
except InvalidUpdateError as e:
    print(f"ERROR: {e}")
    sys.exit(1)
```

---

## Test Coverage Requirements

- ✅ Update unchecked action to checked
- ✅ Add outputs to action
- ✅ Add metadata to action
- ✅ Update multiple fields simultaneously
- ✅ Preserve non-action content exactly
- ✅ Preserve other actions unchanged
- ✅ Generate minimal diff (only changed action)
- ✅ Reject update to checked action (immutability)
- ✅ Raise error when action ID not found
- ✅ Handle action at start/middle/end of file
- ✅ Handle file with single action
- ✅ Handle file with multiple actions
