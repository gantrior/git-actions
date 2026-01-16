# Invalid PR Sample - Should Fail Validation

This file contains invalid actions that should fail PR validation.

## Invalid: Action not in allowlist

- [ ] `invalid-1` — *nonexistent-action* v1.0
```yaml
inputs:
  test: "value"
outputs: {}
meta: {}
```

## Invalid: Version mismatch

- [ ] `invalid-2` — *jira-comment* v2.0
```yaml
inputs:
  ticket: PROJ-123
  comment: "Wrong version"
outputs: {}
meta: {}
```

## Invalid: Schema violation (missing required field)

- [ ] `invalid-3` — *jira-comment* v1.0
```yaml
inputs:
  comment: "Missing ticket field"
outputs: {}
meta: {}
```

## Invalid: Schema violation (pattern mismatch)

- [ ] `invalid-4` — *jira-comment* v1.0
```yaml
inputs:
  ticket: "not-a-valid-pattern"
  comment: "Invalid ticket format"
outputs: {}
meta: {}
```

## Invalid: Checked action (immutability violation)

- [x] `invalid-5` — *jira-comment* v1.0
```yaml
inputs:
  ticket: PROJ-999
  comment: "Already executed action"
outputs:
  commentUrl: "https://jira.example.com/browse/PROJ-999"
meta:
  executedAt: "2026-01-15T10:00:00Z"
```
