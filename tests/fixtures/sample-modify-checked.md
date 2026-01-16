# Sample - Modifying Checked Action (Should Fail)

This file attempts to modify a checked action, which should fail PR validation.

- [x] `modified-action` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "MODIFIED COMMENT - This should fail validation"
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-123#comment-456"
  commentId: "456"
meta:
  executedAt: "2026-01-15T14:32:11Z"
  runId: "1234567890"
```
