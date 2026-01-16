# Sample Completed Daily File

This file shows what actions look like after execution.

- [x] `complete-1` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-123
  comment: Fixed authentication bug in login flow
outputs:
  commentUrl: https://jira.example.com/browse/PROJ-123#comment-12345
  commentId: '12345'
meta:
  executedAt: '2026-01-15T14:32:11Z'
  runId: '1234567890'
```

- [x] `complete-2` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-456
  comment: |-
    Updated documentation for the new API endpoints.
    See PR #789 for implementation details.
outputs:
  commentUrl: https://jira.example.com/browse/PROJ-456#comment-12346
  commentId: '12346'
meta:
  executedAt: '2026-01-15T14:35:22Z'
  runId: '1234567890'
```
