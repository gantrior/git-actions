"""Unit tests for editor.py module."""

import pytest
from tools.editor import update_action_entry, ActionUpdate, ActionNotFoundError, InvalidUpdateError


def test_update_check_box():
    """Update should check the checkbox."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(action_id="a1", check_box=True)
    result = update_action_entry(content, update)
    
    assert "- [x] `a1`" in result
    assert "- [ ] `a1`" not in result


def test_update_outputs():
    """Update should add outputs to the YAML block."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(
        action_id="a1",
        outputs={"commentUrl": "https://example.com", "commentId": "456"}
    )
    result = update_action_entry(content, update)
    
    assert "commentUrl: https://example.com" in result
    assert "commentId: '456'" in result or "commentId: \"456\"" in result


def test_update_meta():
    """Update should add metadata to the YAML block."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(
        action_id="a1",
        meta={"executedAt": "2026-01-15T14:32:11Z", "runId": "1234567890"}
    )
    result = update_action_entry(content, update)
    
    assert "executedAt: '2026-01-15T14:32:11Z'" in result or "executedAt: \"2026-01-15T14:32:11Z\"" in result
    assert "runId: '1234567890'" in result or "runId: \"1234567890\"" in result


def test_update_all_fields():
    """Update should handle checkbox, outputs, and meta together."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(
        action_id="a1",
        check_box=True,
        outputs={"commentUrl": "https://example.com"},
        meta={"executedAt": "2026-01-15T14:32:11Z"}
    )
    result = update_action_entry(content, update)
    
    assert "- [x] `a1`" in result
    assert "commentUrl: https://example.com" in result
    assert "executedAt:" in result


def test_update_preserves_inputs():
    """Update should not modify the inputs field."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Test comment"
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(
        action_id="a1",
        outputs={"commentUrl": "https://example.com"}
    )
    result = update_action_entry(content, update)
    
    assert "ticket: PROJ-123" in result
    assert "comment: Test comment" in result


def test_update_merges_existing_outputs():
    """Update should merge with existing outputs, not replace them."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs:
  existingField: "value1"
meta: {}
```
"""
    update = ActionUpdate(
        action_id="a1",
        outputs={"newField": "value2"}
    )
    result = update_action_entry(content, update)
    
    assert "existingField: value1" in result
    assert "newField: value2" in result


def test_update_multiple_actions_updates_correct_one():
    """When file has multiple actions, should update only the specified one."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```

- [ ] `a2` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-124
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(action_id="a2", check_box=True)
    result = update_action_entry(content, update)
    
    # a1 should remain unchecked
    assert "- [ ] `a1`" in result
    # a2 should be checked
    assert "- [x] `a2`" in result


def test_update_action_not_found():
    """Should raise ActionNotFoundError if action ID doesn't exist."""
    content = """- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```
"""
    update = ActionUpdate(action_id="nonexistent", check_box=True)
    
    with pytest.raises(ActionNotFoundError) as exc_info:
        update_action_entry(content, update)
    
    assert "nonexistent" in str(exc_info.value)


def test_update_checked_action_raises_error_by_default():
    """Should raise InvalidUpdateError when trying to modify a checked action."""
    content = """- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs:
  commentUrl: "https://example.com"
meta:
  executedAt: "2026-01-15T14:32:11Z"
```
"""
    update = ActionUpdate(action_id="a1", outputs={"newField": "value"})
    
    with pytest.raises(InvalidUpdateError) as exc_info:
        update_action_entry(content, update)
    
    assert "immutable" in str(exc_info.value).lower()
    assert "a1" in str(exc_info.value)


def test_update_checked_action_allowed_with_flag():
    """Should allow modifying checked action when allow_modify_checked=True."""
    content = """- [x] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs:
  commentUrl: "https://example.com"
meta:
  executedAt: "2026-01-15T14:32:11Z"
```
"""
    update = ActionUpdate(action_id="a1", outputs={"newField": "value"})
    result = update_action_entry(content, update, allow_modify_checked=True)
    
    assert "newField: value" in result
    assert "- [x] `a1`" in result  # Should remain checked


def test_update_preserves_free_text():
    """Update should not modify free text outside action blocks."""
    content = """# Daily Actions

Some introduction text.

- [ ] `a1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
outputs: {}
meta: {}
```

Some closing notes.
"""
    update = ActionUpdate(action_id="a1", check_box=True)
    result = update_action_entry(content, update)
    
    assert "# Daily Actions" in result
    assert "Some introduction text." in result
    assert "Some closing notes." in result
