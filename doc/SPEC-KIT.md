# Spec Kit Initialization

This project has been initialized with [GitHub Spec Kit](https://github.com/github/spec-kit), a toolkit for spec-driven development.

## What is Spec Kit?

Spec Kit enables you to build high-quality software faster by focusing on product scenarios and predictable outcomes. It provides a structured workflow for:

1. **Constitution** - Define core principles and conventions for your project
2. **Specify** - Create detailed specifications for features
3. **Clarify** - Resolve ambiguities and edge cases
4. **Plan** - Generate technical implementation plans
5. **Tasks** - Break down work into actionable steps
6. **Implement** - Execute the implementation with AI assistance

## Available Commands

The following spec-kit commands are available through GitHub Copilot or other AI assistants:

- `/speckit.constitution` - Define or update project principles and conventions
- `/speckit.specify` - Create or update feature specifications
- `/speckit.clarify` - Identify and resolve specification ambiguities
- `/speckit.plan` - Generate technical implementation plans
- `/speckit.tasks` - Break down plans into actionable tasks
- `/speckit.checklist` - Generate or update implementation checklists
- `/speckit.analyze` - Analyze code and specifications
- `/speckit.implement` - Guide implementation process
- `/speckit.taskstoissues` - Convert tasks to GitHub issues

## Directory Structure

```
.github/
  agents/           # AI agent command definitions
  workflows/        # GitHub Actions workflows
memory/
  constitution.md   # Project constitution (customizable)
scripts/
  bash/            # Shell scripts for automation
  powershell/      # PowerShell scripts (alternative)
templates/         # Templates for specs, plans, and tasks
```

## Getting Started

1. **Define Your Constitution**: Edit `memory/constitution.md` to define your project's core principles
2. **Create a Spec**: Use `/speckit.specify <feature description>` to start a new feature
3. **Generate a Plan**: Use `/speckit.plan` to create an implementation plan
4. **Break Down Tasks**: Use `/speckit.tasks` to create actionable tasks

## Configuration

This project is configured for:
- **AI Assistant**: GitHub Copilot
- **Script Type**: POSIX Shell (bash/zsh)

## Learn More

- [Spec Kit Documentation](https://github.github.io/spec-kit/)
- [Spec Kit Repository](https://github.com/github/spec-kit)
- [Spec-Driven Development Guide](https://github.com/github/spec-kit/blob/main/spec-driven.md)
