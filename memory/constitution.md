# git-actions Constitution

## Core Principles

### I. Self-Documenting Code (NON-NEGOTIABLE)
Code MUST communicate intent through structure and naming rather than comments.

- Functions, types, and variables MUST be named to express domain intent.
- Inline comments MUST NOT describe *what* the code does.
- Inline comments MAY exist only to explain:
  - WHY a decision was made
  - Tradeoffs or constraints
  - External limitations (protocol, spec, vendor, performance)
- If code requires explanatory comments, it MUST be refactored until it becomes readable without them.

> Rule of thumb: If a comment can be derived by reading the code, it is forbidden.

---

### II. Small Functions by Construction (NON-NEGOTIABLE)
Functions MUST be small to enforce readability and composability.

- Target function size: **≤ 15 non-empty lines**
- Absolute maximum: **25 lines**, allowed only with an explicit WHY comment
- Each function MUST have a single, clear responsibility.
- Nesting depth SHOULD NOT exceed 2 levels.
- Guard clauses and early returns are preferred over nested conditionals.

Large functions indicate missing abstractions and MUST be decomposed.

---

### III. Decomposition over Explanation
Complexity MUST be addressed through decomposition, not documentation.

- Any logical block with a clear purpose SHOULD be extracted into a well-named function.
- Orchestrator functions MAY exist but MUST consist only of:
  - validation calls
  - transformations
  - coordination of domain steps
- Helper functions MUST encode intent through naming rather than comments.

> The correct response to complexity is more functions, not more comments.

---

### IV. Why-Only Comments Rule
Comments are a design artifact, not a teaching aid.

Allowed comment categories:
- **WHY** – rationale, tradeoff, constraint
- **REFERENCE** – spec, ADR, KIP, bug, or external contract
- **WARNING** – invariants, performance, security, or footguns

Disallowed:
- Line-by-line narration
- Restating code behavior
- Explaining syntax or control flow

Example (acceptable):
```
// WHY: retry here avoids partial state divergence between cache and source of truth.
// Ref: SPEC-KIP §Error Handling, ADR-0042
```

---

### V. Naming Is Architecture
Naming decisions define system readability and MUST be treated as architectural choices.

- Names MUST reflect domain language defined in the spec.
- Generic names (`data`, `handler`, `process`, `value`) are forbidden outside trivial scopes.
- Boolean values MUST use intent-revealing prefixes (`is`, `has`, `should`, `can`).
- Function names MUST describe observable behavior, not implementation.

Poor naming is considered a correctness issue.

---

### VI. Spec-First, Test-First Development (NON-NEGOTIABLE)
Behavior MUST be defined before implementation.

- Every feature starts with a SPEC-KIP.
- Tests MUST be written before implementation.
- Tests MUST encode acceptance criteria and observable behavior.
- Implementation MUST only satisfy the written spec and tests—nothing more.

Refactoring is allowed only when tests remain unchanged.

---

### VII. Simplicity and Explicitness
The system MUST remain understandable by a reader unfamiliar with its history.

- Prefer explicit code over clever abstractions.
- YAGNI applies at all levels.
- No speculative generalization without a documented reason.
- Hidden side effects are forbidden.

If behavior is surprising, it is wrong.

---

## Quality Constraints

### Function & Complexity Limits
- Max function size enforced in review and tooling where possible.
- Cyclomatic complexity SHOULD remain minimal and justified when exceeded.

### Error Handling
- Fail fast at boundaries.
- Errors MUST describe violated invariants.
- Caught errors MUST be either fully handled or rethrown with context.
- Silent failure is forbidden.

### Types and Invariants
- Invariants SHOULD be enforced via types and validation functions.
- Comments MUST NOT be used to compensate for weak typing.

---

## Development Workflow

1. Write or update SPEC-KIP
2. Define acceptance criteria
3. Write failing tests
4. Implement with small, composable functions
5. Refactor for readability
6. Review against Constitution checklist

### Review Checklist (Mandatory)
- [ ] Functions ≤ 15 lines or explicitly justified
- [ ] No "what" comments present
- [ ] Names reflect domain intent
- [ ] Complexity handled via decomposition
- [ ] Tests match spec and acceptance criteria
- [ ] No undocumented exceptions to rules

---

## Governance

This Constitution supersedes all other practices. Amendments require documentation, approval, and migration plan.

All PRs and reviews must verify compliance. Complexity must be justified.

**Version**: 1.0.0 | **Ratified**: 2026-01-16 | **Last Amended**: 2026-01-16
