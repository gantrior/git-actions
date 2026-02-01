# git-actions

GitOps for actions of your AI assistance

## Actions-as-Markdown Framework

> A framework for proposing and executing automated actions through
> reviewable pull requests

### Overview

The Actions-as-Markdown Framework enables AI assistants and developers to
propose automated actions (like posting Jira comments, updating documentation,
triggering deployments) as reviewable PRs by editing markdown files. Actions
are validated but **not executed** until the PR is merged to `main`. After
execution, the system auto-commits results back inline with checked boxes and
outputs, creating a complete audit trail.

**This is a framework repository** - it provides the core tools and workflows.
To use this framework in your repository:

1. Follow the [Installation Guide](docs/installation.md) to set up the
   framework
2. Define your own actions in `actions/allowlist.yaml`
3. Create action scripts in `scripts/` with JSON schemas in `schemas/`
4. Use the provided workflows for PR validation and execution

**Key benefits:**

- ✅ **Safe**: Actions are validated before execution, no surprises
- ✅ **Reviewable**: All actions are visible in PR diffs as plain markdown
- ✅ **Auditable**: Complete history in git with inputs, outputs, and metadata
- ✅ **Extensible**: Easy to add new action types with custom scripts

### Getting Started

**New to the framework?** Start here:

1. **[Installation Guide](docs/installation.md)** - Set up the framework in
   your repository
2. **[Quickstart Guide](docs/quickstart.md)** - Learn how to use the framework

The installation guide covers:

- How to install the framework to your repository
- GitHub Actions workflow setup with examples
- Branch protection configuration
- Creating your first custom action with templates

### Documentation

- **[Installation Guide](docs/installation.md)** - Install the framework in
  your repository
- **[Quickstart Guide](docs/quickstart.md)** - How to use the framework
- **[Adding Actions](docs/adding-actions.md)** - Guide for adding new action
  types
- **[Specification](specs/001-actions-markdown-framework/spec.md)** - Complete
  feature spec
- **[Implementation Plan](specs/001-actions-markdown-framework/plan.md)** -
  Technical design

### Core Components

- **Parser** (`tools/parser.py`) - Parses markdown action files
- **Validator** (`tools/validator.py`) - Schema and allowlist validation
- **Executor** (`tools/executor.py`) - Action execution engine
- **Workflows** (`.github/workflows/`) - Templates for PR validation and
  execution

## Spec-Kit

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) for
spec-driven development.

See [doc/SPEC-KIT.md](doc/SPEC-KIT.md) for setup details and available
commands.
