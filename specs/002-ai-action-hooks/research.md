# Research: AI Action Hooks for Task Management Integration

**Feature**: 002-ai-action-hooks  
**Date**: 2026-01-19  
**Status**: Complete

## Overview

This document captures research findings and design decisions for implementing hook functionality in the Actions-as-Markdown Framework. Research focused on hook execution patterns, error handling strategies, and integration approaches with the existing action execution pipeline.

## Research Topics

### 1. Hook Execution Model

**Decision**: Use event-driven architecture with explicit lifecycle hooks

**Rationale**: 
- The Actions-as-Markdown Framework already has a clear action lifecycle (parse → validate → execute)
- Adding explicit hook points (before_execute, after_success, after_failure, after_timeout) provides clear extension points
- Event-driven model allows multiple hooks to subscribe to the same lifecycle event without coupling
- Maintains backwards compatibility by making hooks optional

**Alternatives Considered**:
- **Observer pattern with dynamic registration**: Rejected because it adds runtime complexity and makes hook discovery harder to audit
- **Decorator-based hooks**: Rejected because Python decorators would require modifying action scripts, breaking the markdown-first approach
- **Middleware chain**: Rejected because it implies sequential processing when hooks should be independent

**References**: 
- Existing `executor.py` has clear execution phases that can be extended
- Django signals pattern (event-driven, decoupled)
- GitHub Actions workflow hooks (on: success, on: failure)

---

### 2. Hook Configuration Format

**Decision**: YAML configuration file (`actions/hooks.yaml`) with JSON Schema validation

**Rationale**:
- Consistent with existing `actions/allowlist.yaml` format
- Declarative configuration is reviewable in PRs (core framework principle)
- JSON Schema validation provides clear error messages
- YAML supports comments for documentation
- File-based config integrates naturally with git audit trail

**Alternatives Considered**:
- **Python configuration file**: Rejected because it requires code execution to parse, violates "review before execute" principle
- **Database storage**: Rejected because it breaks git-based auditability
- **Embedded in action markdown**: Rejected because it couples action definition with hook configuration

**Configuration Structure**:
```yaml
hooks:
  - id: update_jira_status
    lifecycle_event: after_success
    task_type_filter: ["jira_comment", "jira_update"]
    execution_mode: async
    enabled: true
    script: scripts/hooks/update_jira.py
    config:
      jira_url: https://jira.example.com
      status_field: customfield_10001
```

**References**:
- Existing `allowlist.yaml` structure
- JSON Schema RFC 7159
- GitHub Actions workflow syntax

---

### 3. Hook Execution Safety

**Decision**: Sandbox hook execution with timeout, error isolation, and retry logic

**Rationale**:
- Hook failures must not prevent action completion (per FR-006)
- Asynchronous hooks use fire-and-forget to prevent blocking
- Synchronous hooks have 30-second timeout to prevent indefinite hangs
- Failed hooks are logged but don't fail the action
- Retry logic (3 attempts with exponential backoff) handles transient failures

**Implementation Strategy**:
- Use Python's `subprocess` with timeout for hook script execution
- Capture stdout/stderr for audit logging
- Async hooks run in separate process, detached from action execution
- Sync hooks run with timeout, action waits for completion or timeout

**Alternatives Considered**:
- **In-process execution**: Rejected due to potential for memory leaks and crashes affecting main process
- **No timeout**: Rejected because hung hooks could block action execution indefinitely
- **No retry**: Rejected because network failures to task management systems are common and transient

**References**:
- Python `subprocess` module timeout parameter
- Celery retry patterns
- AWS Lambda error handling (isolate, timeout, retry)

---

### 4. Hook Ordering and Dependencies

**Decision**: Explicit numeric ordering (execution_order: 1, 2, 3...) within each lifecycle event

**Rationale**:
- Simple and predictable execution order
- Easy to understand from configuration file
- Prevents need for complex dependency graphs
- Hooks at same lifecycle event with same order number execute in parallel

**Alternatives Considered**:
- **Dependency DAG**: Rejected as over-engineered for initial version, can be added later if needed
- **Alphabetical by hook ID**: Rejected because it's implicit and hard to reason about
- **Random order**: Rejected because it makes debugging impossible

**Loop Prevention**:
- Maximum execution depth of 10 (prevents infinite recursion)
- Track hook call stack to detect cycles
- Error if depth exceeded with clear message

**References**:
- GitHub Actions job dependencies
- systemd unit ordering
- Make target dependencies

---

### 5. Task Management System Integration

**Decision**: Plugin-based architecture with hook scripts as integration points

**Rationale**:
- No single task management system works for all users
- Hook scripts provide flexibility to integrate with any system (Jira, Linear, Asana, GitHub Issues, etc.)
- Scripts receive context via stdin (JSON), return results via stdout
- Exit code 0 = success, non-zero = failure
- Standard contract allows easy testing and mocking

**Hook Script Contract**:
```json
Input (stdin):
{
  "task_id": "TASK-123",
  "action_type": "jira_comment",
  "status": "success",
  "output": "Comment posted successfully",
  "metadata": {...}
}

Output (stdout):
{
  "success": true,
  "message": "Updated Jira status to Done",
  "details": {...}
}
```

**Alternatives Considered**:
- **Built-in integrations**: Rejected because it creates maintenance burden and limits flexibility
- **Webhook-based**: Rejected because it requires external services and complicates local testing
- **Python imports**: Rejected because it couples hook implementation to framework internals

**References**:
- Unix pipe philosophy (stdin/stdout contract)
- GitHub Actions custom actions (script-based)
- Git hooks (script-based lifecycle integration)

---

### 6. Audit Trail and Logging

**Decision**: Structured logging to file with hook execution details, maintains git-based audit trail

**Rationale**:
- Every hook execution logged with: timestamp, hook_id, lifecycle_event, task_id, status, duration, error (if any)
- Log file in repository (`logs/hook-executions.log`) ensures git history
- JSON Lines format for easy parsing and analysis
- Retention policy: keep last 1000 entries (prevents unbounded growth)

**Log Entry Format**:
```json
{"timestamp": "2026-01-19T11:07:24Z", "hook_id": "update_jira", "event": "after_success", "task_id": "TASK-123", "status": "success", "duration_ms": 342}
```

**Alternatives Considered**:
- **Database logging**: Rejected because it breaks git-based auditability
- **Syslog**: Rejected because it's not portable and harder to review in PRs
- **No logging**: Rejected because it violates auditability requirement (FR-011)

**References**:
- JSON Lines specification
- ELK stack logging patterns
- AWS CloudWatch Logs structured logging

---

## Summary of Key Decisions

1. **Architecture**: Event-driven hooks with explicit lifecycle points (before_execute, after_success, after_failure, after_timeout)
2. **Configuration**: YAML file (`actions/hooks.yaml`) with JSON Schema validation
3. **Execution**: Subprocess-based with timeout, error isolation, and retry logic
4. **Ordering**: Numeric execution_order field, parallel execution for same order
5. **Integration**: Script-based plugins using stdin/stdout contract
6. **Auditability**: JSON Lines logging to file in repository

## Open Questions

None - all technical decisions resolved.

## Next Steps

Proceed to Phase 1 to generate:
- data-model.md (entities and relationships)
- contracts/ (JSON schemas for hook config and script I/O)
- quickstart.md (developer guide for using hooks)
