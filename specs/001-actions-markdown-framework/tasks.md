---

description: "Task list for Actions-as-Markdown Framework implementation"
---

# Tasks: Actions-as-Markdown Framework

**Input**: Design documents from `/specs/001-actions-markdown-framework/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT explicitly requested in the feature specification. Test tasks are included only where critical for TDD workflow or contract validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `tools/`, `scripts/`, `schemas/`, `actions/`, `tests/` at repository root
- Paths assume single project structure as defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure (tools/, scripts/, schemas/, actions/, tests/fixtures/, .github/workflows/)
- [x] T002 Initialize Python project with requirements.txt (pyyaml, jsonschema, requests, pytest)
- [x] T003 [P] Create actions/allowlist.yaml with initial structure (empty action registry)
- [x] T004 [P] Create .gitignore to exclude __pycache__, .pytest_cache, *.pyc

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Implement ActionEntry class in tools/parser.py (data structure for parsed actions)
- [x] T006 [P] Implement ParseError exception class in tools/parser.py with line number tracking
- [x] T007 Implement parse_daily_file() function in tools/parser.py (regex + state machine parser per parser-contract.md)
- [x] T008 [P] Create test fixtures in tests/fixtures/sample-day-pending.md (2-3 unchecked actions for testing)
- [x] T009 Create unit tests in tests/unit/test_parser.py for parse_daily_file() function
- [x] T010 [P] Implement ActionUpdate class in tools/editor.py (data structure for updates)
- [x] T011 [P] Implement ActionNotFoundError and InvalidUpdateError exceptions in tools/editor.py
- [x] T012 Implement update_action_entry() function in tools/editor.py (in-place markdown editor per editor-contract.md)
- [x] T013 Create unit tests in tests/unit/test_editor.py for update_action_entry() function
- [x] T014 [P] Implement Allowlist and AllowlistEntry classes in tools/validator.py
- [x] T015 [P] Implement ValidationResult and ValidationError classes in tools/validator.py
- [x] T016 Implement load_allowlist() function in tools/validator.py (parse allowlist.yaml)
- [x] T017 Implement validate_inputs() function in tools/validator.py (JSON schema validation)
- [x] T018 Implement validate_daily_file() function in tools/validator.py (full validation per validator-contract.md)
- [x] T019 Create unit tests in tests/unit/test_validator.py for validation functions
- [x] T020 [P] Implement ExecutionReport and ActionResult classes in tools/executor.py
- [x] T021 Implement execute_action_script() function in tools/executor.py (subprocess stdin/stdout per executor-contract.md)
- [x] T022 Implement commit_action_result() function in tools/executor.py (git auto-commit with [skip ci])
- [x] T023 Implement execute_actions_from_file() function in tools/executor.py (main execution loop)
- [x] T024 Create mock action script in tests/fixtures/mock-success.py for testing
- [x] T025 Create integration tests in tests/integration/test_executor.py for execution workflow

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - AI Proposes Action via PR (Priority: P1) 🎯 MVP

**Goal**: Enable safe, reviewable action proposals without immediate execution. AI/developers can create PRs with new actions that are validated but not executed until merged.

**Independent Test**: Create a PR with a new action entry, verify validation passes, confirm no external API calls during PR checks.

### Implementation for User Story 1

- [x] T026 [P] [US1] Create example action schema in schemas/jira-comment.json (ticket + comment fields per spec examples)
- [x] T027 [P] [US1] Create example action script in scripts/jira-comment.py (stdin/stdout JSON interface per spec)
- [x] T028 [US1] Add jira-comment entry to actions/allowlist.yaml (script path, version 1.0, schema path, timeout 60, environment any)
- [x] T029 [P] [US1] Create PR validation CLI in tools/validator.py (--mode pr argument, exits 0 on success, 1 on failure)
- [x] T030 [US1] Create .github/workflows/pr-validation.yml (triggers on PR to main, validates actions/*.md files, no secrets)
- [x] T031 [US1] Create sample daily file in tests/fixtures/sample-pr-valid.md for testing PR validation
- [x] T032 [US1] Create sample daily file in tests/fixtures/sample-pr-invalid.md (invalid schema, version mismatch) for testing validation failures
- [x] T033 [US1] Test PR validation workflow end-to-end (create test PR, verify validation runs, check output)

**Checkpoint**: At this point, User Story 1 should be fully functional - PRs with actions can be validated without execution

---

## Phase 4: User Story 2 - Execute Actions on Merge (Priority: P1)

**Goal**: When a PR with actions is merged to main, execute all pending actions and auto-commit results inline with checked boxes and outputs.

**Independent Test**: Merge a PR with pending actions, verify workflow executes them, confirm markdown is updated with results and committed to main.

### Implementation for User Story 2

- [x] T034 [P] [US2] Create executor CLI in tools/executor.py (--file, --commit, --allowlist arguments)
- [x] T035 [US2] Add git configuration to executor (set user.name and user.email for automation commits)
- [x] T036 [US2] Implement environment detection in tools/executor.py (CI vs local via CI env var)
- [x] T037 [US2] Implement environment constraint checking in execute_actions_from_file() (skip actions with mismatched environment)
- [x] T038 [US2] Create .github/workflows/execute-actions.yml (triggers on push to main for actions/*.md, has concurrency group, includes secrets)
- [x] T039 [US2] Add workflow run ID capture in tools/executor.py (from GITHUB_RUN_ID environment variable)
- [x] T040 [US2] Create test fixtures in tests/fixtures/sample-day-complete.md (expected output after execution)
- [x] T041 [US2] Test execution workflow end-to-end (merge actions to main, verify execution, check committed results)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - full proposal → validation → merge → execution → commit flow

---

## Phase 5: User Story 3 - Human Reviews Action Proposal (Priority: P2)

**Goal**: Human reviewers can clearly understand what actions will execute by reading the markdown diff in a PR.

**Independent Test**: Create a PR with actions and verify a human can understand what will happen from the markdown diff alone.

### Implementation for User Story 3

- [x] T042 [P] [US3] Add immutability check in tools/validator.py (reject PRs that modify checked actions in PR mode)
- [x] T043 [US3] Create test fixtures in tests/fixtures/sample-modify-checked.md (PR attempting to modify checked action)
- [x] T044 [US3] Add immutability validation test in tests/unit/test_validator.py (verify checked action modification rejected)
- [x] T045 [US3] Create README.md in repository root with overview of framework and link to quickstart.md
- [x] T046 [US3] Copy quickstart.md from specs/ to repository root docs/ directory for user visibility

**Checkpoint**: User Story 3 complete - human review process is safe with immutability enforcement

---

## Phase 6: User Story 4 - Add New Action Type (Priority: P3)

**Goal**: Developers can extend the framework by adding new action types with their own scripts and schemas.

**Independent Test**: Add a new action script and schema, use it in a daily file, verify it executes correctly.

### Implementation for User Story 4

- [x] T047 [P] [US4] Create second example action schema in schemas/confluence-comment.json (pageId + comment fields)
- [x] T048 [P] [US4] Create second example action script in scripts/confluence-comment.py (demonstrates extensibility)
- [x] T049 [US4] Add confluence-comment entry to actions/allowlist.yaml
- [ ] T050 [US4] Create developer guide in docs/adding-actions.md (how to add new action types per quickstart section)
- [ ] T051 [US4] Create example showing two different action types in same daily file in tests/fixtures/sample-multi-action.md
- [ ] T052 [US4] Test adding and executing new action type end-to-end

**Checkpoint**: User Story 4 complete - framework is extensible for new action types

---

## Phase 7: User Story 5 - Environment-Specific Actions (Priority: P3)

**Goal**: Support actions that can only run in specific environments (ci-only, local-only, any).

**Independent Test**: Create a "local-only" action, run CI execution workflow, verify it skips the action appropriately.

### Implementation for User Story 5

- [ ] T053 [P] [US5] Add environment field to AllowlistEntry class in tools/validator.py (any, ci-only, local-only)
- [ ] T054 [US5] Update allowlist schema validation in load_allowlist() to require environment field
- [ ] T055 [US5] Implement action skip logic in execute_actions_from_file() (mark skipped actions with meta.skipped and reason)
- [ ] T056 [P] [US5] Create example ci-only action in scripts/github-pr-review.py (demonstrates CI-specific action)
- [ ] T057 [P] [US5] Create example local-only action in scripts/local-desktop-action.py (demonstrates local-specific action)
- [ ] T058 [US5] Add environment constraint examples to actions/allowlist.yaml (github-pr-review ci-only, local-desktop-action local-only)
- [ ] T059 [US5] Update editor to handle skipped action status in update_action_entry()
- [ ] T060 [US5] Create test for environment-based skipping in tests/integration/test_environment_constraints.py
- [ ] T061 [US5] Test environment skipping end-to-end (create local-only action, execute in CI, verify skipped)

**Checkpoint**: User Story 5 complete - environment constraints working correctly

---

## Phase 8: User Story 6 - Audit Action History (Priority: P3)

**Goal**: Users can review execution history by browsing daily markdown files which serve as append-only audit logs.

**Independent Test**: Review a daily markdown file after actions have executed and verify all historical information is readable.

### Implementation for User Story 6

- [ ] T062 [P] [US6] Create example multi-day scenario in tests/fixtures/ (2026-01-15.md, 2026-01-16.md with mix of success/failure)
- [ ] T063 [US6] Add timestamp formatting helpers in tools/executor.py (consistent ISO 8601 format)
- [ ] T064 [US6] Ensure error messages in meta.error are human-readable and actionable
- [ ] T065 [US6] Create audit log example in docs/audit-example.md (shows how to review history)
- [ ] T066 [US6] Add git log commands to quickstart.md for reviewing action history
- [ ] T067 [US6] Test audit trail completeness (execute multiple actions over time, verify all metadata present)

**Checkpoint**: All user stories complete - full framework functionality delivered

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T068 [P] Add comprehensive docstrings to all functions in tools/ following Google Python style
- [ ] T069 [P] Add type hints to all function signatures in tools/ (Python 3.9+ annotations)
- [ ] T070 [P] Create main README.md for repository with feature overview, quickstart link, architecture diagram
- [ ] T071 Add error handling improvements across all tools (clear error messages with context)
- [ ] T072 Add logging configuration in tools/ (structured logging to stderr for debugging)
- [ ] T073 [P] Create CONTRIBUTING.md with development setup, testing, and PR guidelines
- [ ] T074 [P] Add output size limit enforcement in execute_action_script() (1MB max, truncate with warning)
- [ ] T075 Run all tests with pytest to verify complete test coverage
- [ ] T076 Validate against quickstart.md scenarios (follow all quickstart examples manually)
- [ ] T077 Review all file sizes and optimize if any daily file fixtures exceed 100KB target

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-8)**: All depend on Foundational phase completion
  - User Story 1 (Phase 3): Can start after Foundational - No dependencies on other stories
  - User Story 2 (Phase 4): Depends on User Story 1 (requires PR validation workflow)
  - User Story 3 (Phase 5): Depends on User Story 1 (requires validation framework)
  - User Story 4 (Phase 6): Can start after Foundational - Independent of US1/US2/US3
  - User Story 5 (Phase 7): Depends on User Story 2 (requires execution framework)
  - User Story 6 (Phase 8): Depends on User Story 2 (requires execution and commit)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation → US1 (independent)
- **User Story 2 (P1)**: Foundation → US1 → US2
- **User Story 3 (P2)**: Foundation → US1 → US3
- **User Story 4 (P3)**: Foundation → US4 (independent of US1/US2/US3)
- **User Story 5 (P3)**: Foundation → US1 → US2 → US5
- **User Story 6 (P3)**: Foundation → US1 → US2 → US6

### Within Each Phase

**Foundational Phase (Critical Path)**:
1. Parser class and exceptions (T005-T006) → Parser implementation (T007) → Parser tests (T008-T009)
2. Editor class and exceptions (T010-T011) → Editor implementation (T012) → Editor tests (T013)
3. Validator classes (T014-T015) → Validator functions (T016-T018) → Validator tests (T019)
4. Executor classes (T020) → Executor functions (T021-T023) → Mock scripts (T024) → Executor tests (T025)

**User Story Phases**:
- All [P] tasks within a story can run in parallel
- Dependencies within story: schemas/scripts → allowlist → workflows → testing

### Parallel Opportunities

- All Setup tasks (T001-T004) can run in parallel
- Within Foundational:
  - T005-T006 (parser classes) || T010-T011 (editor classes) || T014-T015 (validator classes) || T020 (executor classes)
  - T008 (fixtures) can run anytime before T009 (parser tests)
  - T024 (mock scripts) can run anytime before T025 (executor tests)
- Within each User Story, all tasks marked [P] can run in parallel
- User Story 4 (Phase 6) can start immediately after Foundational, in parallel with US1/US2/US3

---

## Parallel Example: Foundational Phase

```bash
# Launch all class definitions in parallel:
Task T005: "Implement ActionEntry class in tools/parser.py"
Task T006: "Implement ParseError exception in tools/parser.py"
Task T010: "Implement ActionUpdate class in tools/editor.py"
Task T011: "Implement exceptions in tools/editor.py"
Task T014: "Implement Allowlist classes in tools/validator.py"
Task T015: "Implement ValidationResult classes in tools/validator.py"
Task T020: "Implement ExecutionReport classes in tools/executor.py"

# Then implement main functions sequentially per module
```

## Parallel Example: User Story 1

```bash
# Launch schemas and scripts in parallel:
Task T026: "Create schema in schemas/jira-comment.json"
Task T027: "Create script in scripts/jira-comment.py"
Task T029: "Create PR validation CLI in tools/validator.py"

# Then allowlist and workflow sequentially
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T025) - **CRITICAL PATH**
3. Complete Phase 3: User Story 1 (T026-T033) - PR validation
4. Complete Phase 4: User Story 2 (T034-T041) - Execution
5. **STOP and VALIDATE**: Test complete workflow (propose → validate → merge → execute → commit)
6. Deploy/demo if ready - **THIS IS MVP**

### Incremental Delivery

1. Setup + Foundational → Foundation ready (T001-T025)
2. Add User Story 1 → PR validation working (T026-T033)
3. Add User Story 2 → Execution working (T034-T041) → **MVP COMPLETE**
4. Add User Story 3 → Review safety enhanced (T042-T046)
5. Add User Story 4 → Framework extensible (T047-T052)
6. Add User Story 5 → Environment constraints (T053-T061)
7. Add User Story 6 → Audit history complete (T062-T067)
8. Polish → Production ready (T068-T077)

### Parallel Team Strategy

With multiple developers:

1. **Team Phase**: Everyone completes Setup + Foundational together (T001-T025)
2. Once Foundational is done (T025 complete):
   - **Developer A**: User Story 1 (T026-T033)
   - **Developer B**: User Story 4 (T047-T052) - can start immediately, independent
   - Developer A completes US1
3. **Developer A**: User Story 2 (T034-T041) - depends on US1
4. **Developer C**: User Story 3 (T042-T046) - can start after US1
5. Once US2 complete:
   - **Developer D**: User Story 5 (T053-T061)
   - **Developer E**: User Story 6 (T062-T067)
6. **Team Phase**: Polish together (T068-T077)

---

## Notes

- [P] tasks = different files, no dependencies within same phase
- [Story] label (US1-US6) maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are included for critical contracts and integration points, not comprehensive TDD
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP = User Stories 1 + 2 only (T001-T041)
- Full feature = All user stories (T001-T077)
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- File paths are explicit in every task description
- All tasks follow required checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
