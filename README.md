# git-actions

GitOps for actions of your AI assistance

## Actions-as-Markdown Framework

> A framework for proposing and executing automated actions through reviewable pull requests

[![PR Validation](https://github.com/gantrior/git-actions/workflows/PR%20Validation/badge.svg)](https://github.com/gantrior/git-actions/actions)
[![Execute Actions](https://github.com/gantrior/git-actions/workflows/Execute%20Actions/badge.svg)](https://github.com/gantrior/git-actions/actions)

### Overview

The Actions-as-Markdown Framework enables AI assistants and developers to propose automated actions (like posting Jira comments, updating documentation, triggering deployments) as reviewable PRs by editing markdown files. Actions are validated but **not executed** until the PR is merged to `main`. After execution, the system auto-commits results back inline with checked boxes and outputs, creating a complete audit trail.

**Key benefits:**
- ✅ **Safe**: Actions are validated before execution, no surprises
- ✅ **Reviewable**: All actions are visible in PR diffs as plain markdown
- ✅ **Auditable**: Complete history in git with inputs, outputs, and metadata
- ✅ **Extensible**: Easy to add new action types with custom scripts

### Quick Start

See [docs/quickstart.md](docs/quickstart.md) for detailed usage guide.

### Available Actions

| Action | Description | Required Inputs | Environment |
|--------|-------------|----------------|-------------|
| `jira-comment` v1.0 | Post comment to Jira ticket | `ticket`, `comment` | any |
| `confluence-comment` v1.0 | Post comment to Confluence page | `pageId`, `comment` | any |

### Documentation

- **[Quickstart Guide](docs/quickstart.md)** - How to propose and execute actions
- **[Specification](specs/001-actions-markdown-framework/spec.md)** - Complete feature spec
- **[Implementation Plan](specs/001-actions-markdown-framework/plan.md)** - Technical design

## Spec-Kit

This project uses [GitHub Spec Kit](https://github.com/github/spec-kit) for spec-driven development.

See [doc/SPEC-KIT.md](doc/SPEC-KIT.md) for setup details and available commands.
