"""Unit tests for parser.py module."""

import pytest
from tools.parser import parse_daily_file, ParseError, ActionEntry


def test_parse_empty_file():
    """Empty file should return empty list."""
    content = ""
    actions = parse_daily_file(content)
    assert actions == []


def test_parse_file_with_no_actions():
    """File with only free text should return empty list."""
    content = """# Daily Actions

Nothing to do today!
"""
    actions = parse_daily_file(content)
    assert actions == []


def test_parse_single_pending_action():
    """Parse a single unchecked action."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test comment"
outputs: {}
meta: {}
```
"""
    actions = parse_daily_file(content)
    assert len(actions) == 1
    
    action = actions[0]
    assert action.id == "a1"
    assert action.name == "test-action"
    assert action.version == "1.0"
    assert action.is_checked is False
    assert action.inputs == {"ticket": "PROJ-123", "comment": "Test comment"}
    assert action.outputs == {}
    assert action.meta == {}
    assert action.line_number == 1


def test_parse_checked_action():
    """Parse a completed action with outputs and meta."""
    content = """- [x] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test comment"
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
  commentId: "456"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```
"""
    actions = parse_daily_file(content)
    assert len(actions) == 1
    
    action = actions[0]
    assert action.is_checked is True
    assert action.outputs == {
        "commentUrl": "https://jira.example.com/browse/PROJ-123#comment-456",
        "commentId": "456"
    }
    assert action.meta == {
        "executedAt": "2026-01-15T14:32:11Z",
        "runId": "1234567890"
    }


def test_parse_multiple_actions():
    """Parse multiple actions from fixture file."""
    with open('tests/fixtures/sample-day-pending.md', 'r') as f:
        content = f.read()
    
    actions = parse_daily_file(content, filename='sample-day-pending.md')
    assert len(actions) == 3
    
    # Check first action
    assert actions[0].id == "a1"
    assert actions[0].name == "test-action"
    assert actions[0].inputs["ticket"] == "PROJ-123"
    
    # Check second action (multiline comment)
    assert actions[1].id == "a2"
    assert "Updated documentation" in actions[1].inputs["comment"]
    assert "PR #456" in actions[1].inputs["comment"]
    
    # Check third action (different action type)
    assert actions[2].id == "a3"
    assert actions[2].name == "test-action"


def test_parse_uppercase_x_in_checkbox():
    """Uppercase X in checkbox should be treated as checked."""
    content = """- [X] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    actions = parse_daily_file(content)
    assert len(actions) == 1
    assert actions[0].is_checked is True


def test_parse_action_id_with_hyphens():
    """Action IDs can contain hyphens."""
    content = """- [ ] `jira-update-001` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    actions = parse_daily_file(content)
    assert len(actions) == 1
    assert actions[0].id == "jira-update-001"


def test_parse_error_missing_yaml_fence():
    """Should raise ParseError if YAML fence is missing."""
    content = """- [ ] `a1` — *test-action* v1.0
inputs:
  ticket: PROJ-123
"""
    with pytest.raises(ParseError) as exc_info:
        parse_daily_file(content, filename="test.md")
    
    assert "Expected '```yaml'" in str(exc_info.value)
    assert "line 1" in str(exc_info.value)
    assert "test.md" in str(exc_info.value)


def test_parse_error_unclosed_yaml_fence():
    """Should raise ParseError if YAML fence is not closed."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
"""
    with pytest.raises(ParseError) as exc_info:
        parse_daily_file(content, filename="test.md")
    
    assert "Missing closing '```'" in str(exc_info.value)
    assert "a1" in str(exc_info.value)


def test_parse_error_invalid_yaml():
    """Should raise ParseError for invalid YAML syntax."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
  invalid yaml syntax:
    - [ this is not valid
```
"""
    with pytest.raises(ParseError) as exc_info:
        parse_daily_file(content, filename="test.md")
    
    assert "Invalid YAML" in str(exc_info.value)
    assert "a1" in str(exc_info.value)


def test_parse_error_yaml_not_dict():
    """Should raise ParseError if YAML is not a dictionary."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
- list item 1
- list item 2
```
"""
    with pytest.raises(ParseError) as exc_info:
        parse_daily_file(content, filename="test.md")
    
    assert "must be a dictionary" in str(exc_info.value)


def test_parse_error_inputs_not_dict():
    """Should raise ParseError if inputs is not a dictionary."""
    content = """- [ ] `a1` — *test-action* v1.0
```yaml
inputs: "not a dict"
outputs: {}
meta: {}
```
"""
    with pytest.raises(ParseError) as exc_info:
        parse_daily_file(content, filename="test.md")
    
    assert "'inputs' must be a dictionary" in str(exc_info.value)


def test_parse_with_free_text_mixed():
    """Parser should preserve free text and extract actions correctly."""
    content = """# Daily Actions for 2026-01-15

Some introduction text here.

- [ ] `a1` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```

More text in between.

- [ ] `a2` — *test-action* v1.0
```yaml
inputs:
  ticket: PROJ-124
outputs: {}
meta: {}
```

End notes.
"""
    actions = parse_daily_file(content)
    assert len(actions) == 2
    assert actions[0].id == "a1"
    assert actions[1].id == "a2"
