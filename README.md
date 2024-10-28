# 🤖 AI Labeler

Let an LLM handle the labeling! 

This GitHub Action uses AI to label your issues and PRs, keeping your repo organized so you can focus on what matters.

## ✨ Features

- **Smart Analysis**: Understands context from titles, descriptions, and code changes
- **Context-Aware**: Uses repository files (CODEOWNERS, templates, etc.) to make informed decisions
- **Incremental**: Works alongside other label management tools and manual labeling
- **Zero Config**: Works out of the box with your existing GitHub labels
- **Customizable**: Fine-tune behavior with optional configuration
- **Reliable**: Supports OpenAI and Anthropic's latest models, orchestrated with ControlFlow

## 🚀 Quick Start

1. Add `.github/workflows/ai-labeler.yml` to your repo. Here is a ready-to-use example:

```yaml
name: AI Labeler

on:
  issues:
    types: [opened, reopened]
  pull_request:
    types: [opened, reopened]

jobs:
  ai-labeler:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: jlowin/ai-labeler@v0.1.0
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

2. Add your OpenAI API key to your repository's secrets as `OPENAI_API_KEY`.

That's it! The AI will read your repository's existing labels and their descriptions to make smart labeling decisions. Want to improve the AI's accuracy? Just update your label descriptions in GitHub's UI.

## ⚙️ Configuration

The action supports these inputs:

- `openai-api-key`: OpenAI API key (required unless using Anthropic)
- `anthropic-api-key`: Anthropic API key (required if using an Anthropic model)
- `controlflow-llm-model`: Model to use (default: "openai/gpt-4o-mini")
- `config-path`: Path to config file (default: ".github/ai-labeler.yml")
- `dry-run`: Set to "true" to preview labels without applying them
- `github-token`: GitHub token (default: github.token)
- `event-number`: PR/Issue number (usually auto-detected)

## 🎯 Fine-Tuning

You can create a config file to customize the labeling behavior. By default, the action looks for `.github/ai-labeler.yml`.

### Configuration Options

#### 1. Instructions

Global guidance for the AI labeler:

```yaml
instructions: |
  You're our labeling expert! Please help keep our repository organized by:
  - Using 'bug' only for confirmed issues, not feature requests
  - Applying 'help wanted' to good first-time contributor opportunities
  - Being generous with 'good first issue' to encourage new contributors
```

#### 2. Include Repository Labels

Control whether to use existing repository labels:

```yaml
# If false, only use labels defined in this file (default: true)
include_repo_labels: false
```

#### 3. Label Definitions

Define or enhance specific labels:

```yaml
labels:
  # Simple form: just the name
  - question

  # Expanded form with description and instructions
  - documentation:
    description: "Documentation changes"
    instructions: |
      Apply when changes are primarily documentation-focused:
      - Changes to README, guides, or other .md files
      - Updates to docstrings or inline documentation
```

#### 4. Context Files

Specify additional files the AI should consider when making decisions:

```yaml
context_files:
  - .github/CODEOWNERS
  - CONTRIBUTING.md
  - .github/ISSUE_TEMPLATE/bug_report.md
```

## 🎨 Configuration Examples

Here are some examples of interesting labeling behaviors you can configure:

### 1. Basic Label Application

```yaml
labels:
  - bug:
    description: "Something isn't working"
    instructions: |
      Apply when the issue describes unexpected behavior with:
      - Clear error messages
      - Steps to reproduce
      - Expected vs actual behavior
```

### 2. Maintainer-Specific Labels

```yaml
labels:
  - frontend-review:
    description: "Needs review from frontend team"
    instructions: |
      Apply when changes touch frontend code:
      - Check if files are in frontend/ or ui/ directories
      - Check CODEOWNERS for @frontend-team ownership
      - Look for changes to CSS, JavaScript, or React components

  - backend-review:
    description: "Needs review from backend team"
    instructions: |
      Apply for changes to backend systems:
      - Check if files are in backend/ or api/ directories
      - Check CODEOWNERS for @backend-team ownership
      - Look for database or API changes

context_files:
  - .github/CODEOWNERS
```

### 3. Release Note Management

```yaml
labels:
  - skip-release-notes:
    description: "Exclude from release notes"
    instructions: |
      Apply to changes that don't need release notes:
      - Simple typo fixes
      - Internal documentation updates
      - CI/CD tweaks
      - Version bumps in test files
      - Changes to development tools

  - breaking-change:
    description: "Introduces breaking changes"
    instructions: |
      Apply when changes require user action:
      - API signature changes
      - Configuration format updates
      - Dependency requirement changes
      - Removed features or endpoints
```

### 4. Automated Triage

```yaml
labels:
  - needs-reproduction:
    description: "Issue needs steps to reproduce"
    instructions: |
      Apply to bug reports that need more info:
      - Check issue templates for missing required info
      - Look for clear reproduction steps
      - Check for environment details

  - good-first-issue:
    description: "Good for newcomers"
    instructions: |
      Apply to encourage new contributors:
      - Small, well-defined scope
      - Clear success criteria
      - Minimal prerequisite knowledge
      - Good documentation exists

context_files:
  - .github/ISSUE_TEMPLATE/bug_report.md
  - CONTRIBUTING.md
```

## 🤝 Contributing

Issues and PRs welcome! And don't worry about labels – we've got that covered! 😉