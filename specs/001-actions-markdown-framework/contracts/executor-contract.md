# Executor Contract

**Module**: `tools/executor.py`  
**Purpose**: Execute pending actions and commit results

---

## Public Interface

### Function: `execute_actions_from_file(file_path: str, allowlist_path: str, commit: bool = False) -> ExecutionReport`

**Description**: Execute all pending (unchecked) actions in a daily file.

**Input**:
- `file_path`: Path to daily markdown file
- `allowlist_path`: Path to allowlist YAML file
- `commit`: If True, commit results to git after each action execution

**Output**: `ExecutionReport` object with summary of executions

**Errors**:
- `FileNotFoundError`: File or allowlist not found
- `ParseError`: Malformed daily file
- Does NOT raise errors for action execution failures (captured in results)

**Behavior**:
- Parse daily file → Extract all actions
- Filter to unchecked actions only
- For each unchecked action:
  - Check environment constraint
  - Load action script from allowlist
  - Execute script with inputs (stdin/stdout JSON)
  - Capture outputs or error
  - Update action entry in file (check box, populate outputs/meta)
  - If `commit=True`, commit changes to git immediately
- Return execution report

---

### Class: `ExecutionReport`

**Description**: Summary of action executions.

**Attributes**:
- `total_actions: int` - Total actions in file
- `pending_actions: int` - Actions that were pending before execution
- `executed_actions: int` - Actions that were executed (attempted)
- `successful_actions: int` - Actions that completed successfully
- `failed_actions: int` - Actions that failed with errors
- `skipped_actions: int` - Actions skipped due to environment mismatch
- `results: list[ActionResult]` - Detailed result for each executed action

**Methods**:
- `to_dict() -> dict`: Serialize to dictionary
- `print_summary() -> None`: Print human-readable execution summary

**Example**:
```python
report = execute_actions_from_file("actions/2026-01-15.md", "actions/allowlist.yaml", commit=True)
report.print_summary()
# Output:
# ✅ Execution complete
#    Total actions: 5
#    Executed: 3
#    Successful: 2
#    Failed: 1
#    Skipped: 0
```

---

### Class: `ActionResult`

**Description**: Result of executing a single action.

**Attributes**:
- `action_id: str` - Action identifier
- `action_name: str` - Action type name
- `status: str` - Execution status (`"success"`, `"error"`, `"skipped"`)
- `outputs: dict` - Outputs from action script (empty if error)
- `error: str | None` - Error message if execution failed
- `executed_at: str` - ISO 8601 timestamp when execution completed
- `run_id: str` - GitHub Actions workflow run ID (if available)
- `duration_seconds: float` - Time taken to execute action

---

### Function: `execute_action_script(script_path: str, action_data: dict, timeout: int) -> dict`

**Description**: Execute a single action script and return result.

**Input**:
- `script_path`: Path to executable action script
- `action_data`: Dictionary with format:
  ```python
  {
      "action": "jira-comment",
      "version": "1.0",
      "inputs": {"ticket": "PROJ-123", "comment": "Fixed"}
  }
  ```
- `timeout`: Maximum execution time in seconds

**Output**: Dictionary with format:
```python
{
    "status": "success",  # or "error"
    "outputs": {"commentUrl": "https://..."},  # empty if error
    "error": None  # or error message string
}
```

**Errors**:
- Does NOT raise exceptions (captures errors in returned dict)
- Timeout → Returns `{"status": "error", "error": "Timeout after {timeout}s"}`
- Script crash → Returns `{"status": "error", "error": "Script exited with code {code}"}`
- Invalid JSON output → Returns `{"status": "error", "error": "Invalid JSON output from script"}`

**Behavior**:
- Invoke script as subprocess
- Pass `action_data` as JSON on stdin
- Read JSON response from stdout
- Enforce timeout
- Capture stderr for logging (not included in result)
- Return structured result

---

### Function: `commit_action_result(file_path: str, action_id: str, message: str = None) -> None`

**Description**: Commit action result to git repository.

**Input**:
- `file_path`: Path to file to commit (e.g., `actions/2026-01-15.md`)
- `action_id`: Action ID for commit message
- `message`: Optional custom commit message (default: `"Execute action {action_id} [skip ci]"`)

**Output**: None

**Errors**:
- `GitError`: Git command failed

**Behavior**:
- Stage file with `git add {file_path}`
- Check if there are changes with `git diff --staged --quiet`
- If changes exist:
  - Commit with message containing `[skip ci]` tag
  - Push to remote
- If no changes, skip commit

**Git Configuration**:
```python
# Set git identity for automation commits
subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])
```

---

## Implementation Notes

### Execution Flow

```
1. Parse daily file → list[ActionEntry]
2. Filter to unchecked actions → list[ActionEntry]
3. For each unchecked action:
   a. Load allowlist entry
   b. Check environment constraint → Skip if mismatch
   c. Prepare action data (inputs, version)
   d. Execute script with timeout
   e. Capture result (outputs or error)
   f. Update action entry in file
   g. (Optional) Commit immediately
4. Return ExecutionReport
```

### Script Execution

```python
import subprocess
import json
import os

def execute_action_script(script_path, action_data, timeout):
    start_time = time.time()
    
    try:
        # Prepare input JSON
        input_json = json.dumps(action_data)
        
        # Execute script with timeout
        result = subprocess.run(
            [script_path],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ,  # Pass environment (includes secrets)
            check=False  # Don't raise on non-zero exit
        )
        
        # Parse output
        if result.returncode == 0:
            try:
                output_data = json.loads(result.stdout)
                return output_data
            except json.JSONDecodeError:
                return {
                    "status": "error",
                    "outputs": {},
                    "error": "Invalid JSON output from script"
                }
        else:
            # Script exited with error
            stderr = result.stderr.strip() if result.stderr else "No error message"
            return {
                "status": "error",
                "outputs": {},
                "error": f"Script failed: {stderr}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "outputs": {},
            "error": f"Timeout after {timeout} seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "outputs": {},
            "error": str(e)
        }
```

### Immediate Commit Strategy

**Why commit after each action?**
- Prevents loss of results if workflow crashes mid-execution
- Partial progress is valuable for debugging
- Avoids re-executing already-completed actions on retry

**Commit message format**:
```
Execute action {action_id} [skip ci]
```

**The `[skip ci]` tag**:
- Prevents infinite loop (commit → push → trigger execution → commit → ...)
- GitHub Actions recognizes this tag and skips workflow trigger

### Environment Constraint Handling

```python
def should_skip_action(action_entry, allowlist_entry):
    """Determine if action should be skipped based on environment."""
    current_env = "ci" if os.environ.get("CI") == "true" else "local"
    
    env_constraint = allowlist_entry.environment
    
    if env_constraint == "any":
        return False
    elif env_constraint == "ci-only" and current_env == "local":
        return True
    elif env_constraint == "local-only" and current_env == "ci":
        return True
    else:
        return False
```

**Skipped actions**:
- Checkbox remains unchecked
- `meta` field updated with skip reason:
  ```yaml
  meta:
    skipped: true
    reason: "Environment mismatch: action requires local, running in ci"
  ```

---

### Example Usage

```python
from tools.executor import execute_actions_from_file, ExecutionReport

# Execute all pending actions in daily file
report = execute_actions_from_file(
    file_path="actions/2026-01-15.md",
    allowlist_path="actions/allowlist.yaml",
    commit=True  # Commit results to git
)

# Print summary
report.print_summary()

# Check for failures
if report.failed_actions > 0:
    print("\n❌ Some actions failed:")
    for result in report.results:
        if result.status == "error":
            print(f"  - {result.action_id}: {result.error}")
```

**Output**:
```
✅ Execution complete
   Total actions: 3
   Executed: 3
   Successful: 2
   Failed: 1
   Skipped: 0

❌ Some actions failed:
  - a2: API rate limit exceeded: 429 Too Many Requests
```

---

### CLI Interface

The executor will be invoked from GitHub Actions workflow:

```bash
python tools/executor.py --file actions/2026-01-15.md --commit
```

**CLI Arguments**:
- `--file`: Path to daily file (required)
- `--commit`: Enable git auto-commit (flag)
- `--allowlist`: Path to allowlist (default: `actions/allowlist.yaml`)

**Exit codes**:
- `0`: Execution completed (even if some actions failed)
- `1`: Fatal error (file not found, parse error, etc.)

---

## Test Coverage Requirements

- ✅ Execute single pending action successfully
- ✅ Execute action that returns error
- ✅ Execute action that times out
- ✅ Execute multiple actions sequentially
- ✅ Skip already-checked actions (idempotency)
- ✅ Skip actions with environment mismatch
- ✅ Update action entry with outputs on success
- ✅ Update action entry with error on failure
- ✅ Commit results to git after each action
- ✅ Handle script that outputs invalid JSON
- ✅ Handle script that crashes
- ✅ Generate accurate execution report
- ✅ Preserve order of action execution
- ✅ Handle file with no pending actions
- ✅ Handle file with mix of pending and completed actions
