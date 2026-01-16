# git-actions

GitOps for actions of your AI assistance

## Actions-as-Markdown Framework

> A framework for proposing and executing automated actions through reviewable pull requests

### Overview

The Actions-as-Markdown Framework enables AI assistants and developers to propose automated actions (like posting Jira comments, updating documentation, triggering deployments) as reviewable PRs by editing markdown files. Actions are validated but **not executed** until the PR is merged to `main`. After execution, the system auto-commits results back inline with checked boxes and outputs, creating a complete audit trail.

**This is a framework repository** - it provides the core tools and workflows. To use this framework:
1. Set up this framework in your repository
2. Define your own actions in `actions/allowlist.yaml`
3. Create action scripts in `scripts/` with JSON schemas in `schemas/`
4. Use the provided workflows for PR validation and execution

**Key benefits:**
- ✅ **Safe**: Actions are validated before execution, no surprises
- ✅ **Reviewable**: All actions are visible in PR diffs as plain markdown
- ✅ **Auditable**: Complete history in git with inputs, outputs, and metadata
- ✅ **Extensible**: Easy to add new action types with custom scripts

### Quick Start

See [docs/quickstart.md](docs/quickstart.md) for detailed usage guide on how to:
- Define custom actions for your use case
- Propose actions via pull requests
- Configure validation and execution workflows

### Documentation

- **[Quickstart Guide](docs/quickstart.md)** - How to use the framework
- **[Adding Actions](docs/adding-actions.md)** - Guide for adding new action types
- **[Specification](specs/001-actions-markdown-framework/spec.md)** - Complete feature spec
- **[Implementation Plan](specs/001-actions-markdown-framework/plan.md)** - Technical design

### Core Components

- **Parser** (`tools/parser.py`) - Parses markdown action files
- **Validator** (`tools/validator.py`) - Schema and allowlist validation
- **Executor** (`tools/executor.py`) - Action execution engine
- **Workflows** (`.github/workflows/`) - Templates for PR validation and execution

## Spec-Kit

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven development.

See [doc/SPEC-KIT.md](doc/SPEC-KIT.md) for setup details and available commands.
