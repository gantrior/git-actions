"""Executor for running pending actions and committing results.

This module provides functionality to execute pending actions from daily files,
capture outputs, update the markdown file, and optionally commit results to git.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import subprocess
import json
import time
import os
from datetime import datetime, timezone

from tools.parser import parse_daily_file, ActionEntry
from tools.editor import update_action_entry, ActionUpdate
from tools.validator import load_allowlist, get_current_environment


@dataclass
class ActionResult:
    """Result of executing a single action.
    
    Attributes:
        action_id: Action identifier
        action_name: Action type name
        status: Execution status (success, error, skipped)
        outputs: Outputs from action script
        error: Error message if execution failed
        executed_at: ISO 8601 timestamp when execution completed
        run_id: GitHub Actions workflow run ID
        duration_seconds: Time taken to execute action
    """
    action_id: str
    action_name: str
    status: str
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    executed_at: Optional[str] = None
    run_id: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class ExecutionReport:
    """Summary of action executions.
    
    Attributes:
        total_actions: Total actions in file
        pending_actions: Actions that were pending before execution
        executed_actions: Actions that were executed (attempted)
        successful_actions: Actions that completed successfully
        failed_actions: Actions that failed with errors
        skipped_actions: Actions skipped due to environment mismatch
        results: Detailed result for each executed action
    """
    total_actions: int = 0
    pending_actions: int = 0
    executed_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    skipped_actions: int = 0
    results: List[ActionResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize execution report to dictionary.
        
        Returns:
            Dictionary representation of execution report
        """
        return {
            "total_actions": self.total_actions,
            "pending_actions": self.pending_actions,
            "executed_actions": self.executed_actions,
            "successful_actions": self.successful_actions,
            "failed_actions": self.failed_actions,
            "skipped_actions": self.skipped_actions,
            "results": [
                {
                    "action_id": r.action_id,
                    "action_name": r.action_name,
                    "status": r.status,
                    "outputs": r.outputs,
                    "error": r.error,
                    "executed_at": r.executed_at,
                    "run_id": r.run_id,
                    "duration_seconds": r.duration_seconds
                }
                for r in self.results
            ]
        }
    
    def print_summary(self) -> None:
        """Print human-readable execution summary."""
        print("✅ Execution complete")
        print(f"   Total actions: {self.total_actions}")
        print(f"   Pending: {self.pending_actions}")
        print(f"   Executed: {self.executed_actions}")
        print(f"   Successful: {self.successful_actions}")
        print(f"   Failed: {self.failed_actions}")
        print(f"   Skipped: {self.skipped_actions}")
        
        if self.failed_actions > 0:
            print("\nFailed actions:")
            for result in self.results:
                if result.status == "error":
                    print(f"  ❌ {result.action_id} ({result.action_name}): {result.error}")


def execute_action_script(
    script_path: str,
    action_data: Dict[str, Any],
    timeout: int = 300
) -> Dict[str, Any]:
    """Execute a single action script and return result.
    
    Args:
        script_path: Path to executable action script
        action_data: Dictionary with action, version, and inputs
        timeout: Maximum execution time in seconds
    
    Returns:
        Dictionary with status, outputs, and optional error
    """
    try:
        # Prepare input JSON
        input_json = json.dumps(action_data)
        
        # Execute script with timeout
        start_time = time.time()
        result = subprocess.run(
            [script_path],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )
        duration = time.time() - start_time
        
        # Parse JSON output from stdout (regardless of exit code)
        try:
            output_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            # If parsing fails and we have a non-zero exit code, try stderr
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else f"Script exited with code {result.returncode}"
                return {"status": "error", "outputs": {}, "error": error_msg}
            # If exit code is 0 but JSON is invalid, that's an error
            return {"status": "error", "outputs": {}, "error": f"Invalid JSON output from script: {str(e)}"}
        
        # Validate output structure
        if not isinstance(output_data, dict):
            return {
                "status": "error",
                "outputs": {},
                "error": "Script output must be a JSON object"
            }
        
        # Extract status and outputs
        status = output_data.get("status", "success")
        outputs = output_data.get("outputs", {})
        error = output_data.get("error")
        
        return {
            "status": status,
            "outputs": outputs if status == "success" else {},
            "error": error
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "outputs": {},
            "error": f"Timeout after {timeout}s"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "outputs": {},
            "error": f"Script not found: {script_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "outputs": {},
            "error": f"Unexpected error: {str(e)}"
        }


def commit_action_result(
    file_path: str,
    action_id: str,
    message: Optional[str] = None
) -> None:
    """Commit action result to git repository.
    
    Args:
        file_path: Path to file to commit
        action_id: Action ID for commit message
        message: Optional custom commit message
    
    Raises:
        subprocess.CalledProcessError: Git command failed
    """
    # Default commit message
    if message is None:
        message = f"Execute action {action_id} [skip ci]"
    
    # Stage the file
    subprocess.run(
        ["git", "add", file_path],
        check=True,
        capture_output=True
    )
    
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--staged", "--quiet"],
        capture_output=True
    )
    
    # If exit code is 1, there are changes to commit
    if result.returncode == 1:
        # Commit the changes
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
            capture_output=True
        )
        
        # Push to remote
        subprocess.run(
            ["git", "push"],
            check=True,
            capture_output=True
        )


def execute_actions_from_file(
    file_path: str,
    allowlist_path: str,
    commit: bool = False
) -> ExecutionReport:
    """Execute all pending (unchecked) actions in a daily file.
    
    Args:
        file_path: Path to daily markdown file
        allowlist_path: Path to allowlist YAML file
        commit: If True, commit results to git after each action
    
    Returns:
        ExecutionReport with summary and detailed results
    
    Raises:
        FileNotFoundError: File or allowlist not found
        ParseError: Malformed daily file
    """
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse actions from file
    actions = parse_daily_file(content, filename=file_path)
    
    # Load allowlist
    allowlist = load_allowlist(allowlist_path)
    
    # Get current environment
    current_env = get_current_environment()
    
    # Get GitHub run ID if available
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    
    # Initialize report
    report = ExecutionReport()
    report.total_actions = len(actions)
    
    # Filter to unchecked actions
    pending_actions = [a for a in actions if not a.is_checked]
    report.pending_actions = len(pending_actions)
    
    # Execute each pending action
    for action in pending_actions:
        # Get allowlist entry
        entry = allowlist.get_entry(action.name)
        if entry is None:
            # Skip if not in allowlist (should be caught by validation)
            continue
        
        # Check environment constraint
        if not entry.can_run_in_environment(current_env):
            # Skip action due to environment mismatch
            result = ActionResult(
                action_id=action.id,
                action_name=action.name,
                status="skipped",
                error=f"Action requires '{entry.environment}' environment, current is '{current_env}'"
            )
            report.results.append(result)
            report.skipped_actions += 1
            
            # Update action with skip status
            # (Note: For now we don't update skipped actions in the file)
            continue
        
        # Prepare action data for script
        action_data = {
            "action": action.name,
            "version": action.version,
            "inputs": action.inputs
        }
        
        # Execute the action script
        start_time = time.time()
        script_result = execute_action_script(
            script_path=entry.script,
            action_data=action_data,
            timeout=entry.timeout
        )
        duration = time.time() - start_time
        
        # Get current timestamp
        executed_at = datetime.now(timezone.utc).isoformat()
        
        # Create action result
        result = ActionResult(
            action_id=action.id,
            action_name=action.name,
            status=script_result["status"],
            outputs=script_result["outputs"],
            error=script_result["error"],
            executed_at=executed_at,
            run_id=run_id,
            duration_seconds=duration
        )
        report.results.append(result)
        report.executed_actions += 1
        
        if result.status == "success":
            report.successful_actions += 1
        else:
            report.failed_actions += 1
        
        # Update action with outputs and meta
        meta = {
            "executedAt": executed_at,
            "runId": run_id
        }
        if result.error:
            meta["error"] = result.error
        
        update = ActionUpdate(
            action_id=action.id,
            check_box=True,
            outputs=result.outputs,
            meta=meta
        )
        
        # Re-read file content (in case it was modified)
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Update the action
        updated_content = update_action_entry(
            content,
            update,
            allow_modify_checked=False  # First update, action is unchecked
        )
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        # Commit if requested
        if commit:
            try:
                commit_action_result(file_path, action.id)
            except subprocess.CalledProcessError as e:
                # Log error but continue execution
                print(f"Warning: Failed to commit action {action.id}: {str(e)}")
    
    return report
