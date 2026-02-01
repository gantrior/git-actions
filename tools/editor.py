"""In-place markdown editor for updating action entries.

This module provides functionality to update action entries in daily files
by checking boxes and adding outputs/meta while preserving the exact format
and minimal diffs.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import yaml


@dataclass
class ActionUpdate:
    """Represents an update to an action entry.

    Attributes:
        action_id: ID of the action to update
        check_box: If True, mark action as checked
        outputs: New outputs to add (merged with existing)
        meta: New metadata to add (merged with existing)
    """

    action_id: str
    check_box: bool = False
    outputs: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None


class ActionNotFoundError(Exception):
    """Raised when the specified action ID is not found in the file."""

    pass


class InvalidUpdateError(Exception):
    """Raised when an update operation is invalid (e.g., modifying a checked action)."""

    pass


# Regex pattern to match action header line
ACTION_HEADER_PATTERN = re.compile(r"^(- \[)([ xX])(\] `[a-zA-Z0-9-]+` — \*[a-z-]+\* v[0-9.]+)$")


def update_action_entry(
    content: str, update: ActionUpdate, allow_modify_checked: bool = False
) -> str:
    """Update an action entry in a daily file with minimal changes.

    This function performs an in-place update of an action entry by:
    1. Finding the action by ID
    2. Optionally checking the checkbox
    3. Updating the outputs and meta fields in the YAML block

    The function preserves the exact formatting and makes minimal changes
    to ensure clean git diffs.

    Args:
        content: Raw markdown content of the daily file
        update: ActionUpdate object specifying what to change
        allow_modify_checked: If False (default), raises error when trying
            to modify an already-checked action (immutability enforcement)

    Returns:
        Updated markdown content as a string

    Raises:
        ActionNotFoundError: If the action ID is not found
        InvalidUpdateError: If trying to modify a checked action when
            allow_modify_checked is False
    """
    lines = content.split("\n")
    action_found = False
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line is an action header
        # We need to extract the action ID separately
        header_match = re.match(
            r"^- \[([ xX])\] `([a-zA-Z0-9-]+)` — \*([a-z-]+)\* v([0-9.]+)$", line
        )

        if header_match and header_match.group(2) == update.action_id:
            action_found = True
            current_checked = header_match.group(1).lower() == "x"

            # Check immutability constraint
            if current_checked and not allow_modify_checked:
                raise InvalidUpdateError(
                    f"Cannot modify checked action '{update.action_id}'. "
                    "Checked actions are immutable."
                )

            # Update checkbox if requested
            if update.check_box and not current_checked:
                # Replace the checkbox character
                match = ACTION_HEADER_PATTERN.match(line)
                if match:
                    lines[i] = match.group(1) + "x" + match.group(3)

            # Move to YAML block
            i += 1
            if i >= len(lines) or lines[i].strip() != "```yaml":
                raise InvalidUpdateError(
                    f"Expected '```yaml' after action header for action '{update.action_id}'"
                )

            # Collect YAML content
            yaml_lines = []
            i += 1
            yaml_start = i
            while i < len(lines):
                if lines[i].strip() == "```":
                    break
                yaml_lines.append(lines[i])
                i += 1

            # Parse current YAML
            yaml_content = "\n".join(yaml_lines)
            try:
                data = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError as e:
                raise InvalidUpdateError(f"Invalid YAML in action '{update.action_id}': {str(e)}")

            # Update outputs and meta
            if update.outputs is not None:
                current_outputs = data.get("outputs", {})
                current_outputs.update(update.outputs)
                data["outputs"] = current_outputs

            if update.meta is not None:
                current_meta = data.get("meta", {})
                current_meta.update(update.meta)
                data["meta"] = current_meta

            # Serialize back to YAML with consistent formatting
            # Use default_flow_style=False for readable block style
            new_yaml = yaml.dump(
                data, default_flow_style=False, sort_keys=False, allow_unicode=True
            )

            # Remove trailing newline that yaml.dump adds
            new_yaml = new_yaml.rstrip("\n")

            # Replace the YAML lines
            new_yaml_lines = new_yaml.split("\n")
            lines[yaml_start:i] = new_yaml_lines

            # Update i to point after the new YAML content
            i = yaml_start + len(new_yaml_lines)

            break

        i += 1

    if not action_found:
        raise ActionNotFoundError(f"Action '{update.action_id}' not found in file")

    return "\n".join(lines)
