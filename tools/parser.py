"""Markdown parser for daily action files.

This module provides functionality to parse daily action files (YYYY-MM-DD.md)
and extract action entries with their metadata, inputs, outputs, and execution status.
"""

import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import yaml


@dataclass
class ActionEntry:
    """Represents a single action entry from a daily file.
    
    Attributes:
        id: Unique identifier within the daily file (e.g., 'a1', 'jira-001')
        name: Action type name (must exist in allowlist)
        version: Semantic version string (e.g., '1.0', '2.1')
        is_checked: Execution status (False = pending, True = completed)
        inputs: Action-specific parameters (validated against schema)
        outputs: Execution results (empty until executed)
        meta: Execution metadata (executedAt, runId, error)
        line_number: Line number in source file where action starts
    """
    id: str
    name: str
    version: str
    is_checked: bool
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    meta: Dict[str, Any]
    line_number: int


class ParseError(Exception):
    """Raised when parsing a daily file fails.
    
    Attributes:
        message: Human-readable error description
        line_number: Line number where error occurred (if applicable)
        filename: Name of file being parsed (if applicable)
    """
    def __init__(self, message: str, line_number: Optional[int] = None, filename: Optional[str] = None):
        self.message = message
        self.line_number = line_number
        self.filename = filename
        
        full_message = message
        if filename:
            full_message = f"{filename}: {full_message}"
        if line_number is not None:
            full_message = f"{full_message} (line {line_number})"
        
        super().__init__(full_message)


# Regex pattern to match action header line
# Format: - [ ] `action-id` — *action-name* vVersion
# or:     - [x] `action-id` — *action-name* vVersion
ACTION_HEADER_PATTERN = re.compile(
    r'^- \[([ xX])\] `([a-zA-Z0-9-]+)` — \*([a-z-]+)\* v([0-9.]+)$'
)


def parse_daily_file(content: str, filename: Optional[str] = None) -> List[ActionEntry]:
    """Parse a daily action file and extract all action entries.
    
    Args:
        content: Raw markdown content of the daily file
        filename: Optional filename for error reporting
    
    Returns:
        List of ActionEntry objects in order of appearance
    
    Raises:
        ParseError: If file format is invalid or YAML parsing fails
    """
    lines = content.split('\n')
    actions = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        match = ACTION_HEADER_PATTERN.match(line)
        
        if match:
            # Extract metadata from header line
            is_checked = match.group(1).lower() == 'x'
            action_id = match.group(2)
            action_name = match.group(3)
            version = match.group(4)
            line_number = i + 1  # 1-indexed for human readability
            
            # Next line must be opening YAML fence
            i += 1
            if i >= len(lines) or lines[i].strip() != '```yaml':
                raise ParseError(
                    f"Expected '```yaml' after action header for action '{action_id}'",
                    line_number=line_number,
                    filename=filename
                )
            
            # Collect YAML content until closing fence
            yaml_lines = []
            i += 1
            yaml_start_line = i + 1
            while i < len(lines):
                if lines[i].strip() == '```':
                    # Found closing fence
                    break
                yaml_lines.append(lines[i])
                i += 1
            else:
                # Reached end of file without closing fence
                raise ParseError(
                    f"Missing closing '```' for action '{action_id}'",
                    line_number=yaml_start_line,
                    filename=filename
                )
            
            # Parse YAML content
            yaml_content = '\n'.join(yaml_lines)
            try:
                data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                raise ParseError(
                    f"Invalid YAML in action '{action_id}': {str(e)}",
                    line_number=yaml_start_line,
                    filename=filename
                )
            
            # Validate YAML structure
            if not isinstance(data, dict):
                raise ParseError(
                    f"Action YAML must be a dictionary for action '{action_id}'",
                    line_number=yaml_start_line,
                    filename=filename
                )
            
            # Extract required fields with defaults
            inputs = data.get('inputs', {})
            outputs = data.get('outputs', {})
            meta = data.get('meta', {})
            
            if not isinstance(inputs, dict):
                raise ParseError(
                    f"'inputs' must be a dictionary for action '{action_id}'",
                    line_number=yaml_start_line,
                    filename=filename
                )
            if not isinstance(outputs, dict):
                raise ParseError(
                    f"'outputs' must be a dictionary for action '{action_id}'",
                    line_number=yaml_start_line,
                    filename=filename
                )
            if not isinstance(meta, dict):
                raise ParseError(
                    f"'meta' must be a dictionary for action '{action_id}'",
                    line_number=yaml_start_line,
                    filename=filename
                )
            
            # Create action entry
            action = ActionEntry(
                id=action_id,
                name=action_name,
                version=version,
                is_checked=is_checked,
                inputs=inputs,
                outputs=outputs,
                meta=meta,
                line_number=line_number
            )
            actions.append(action)
        
        i += 1
    
    return actions
