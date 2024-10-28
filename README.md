# 🦾🏷️ AI Labeler

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

1. Add this `.github/workflows/ai-labeler.yml` to your repo:

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
      - uses: jlowin/ai-labeler@v0.2.0
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

2. Add your OpenAI API key to your repository's secrets as `OPENAI_API_KEY`.

That's it! The AI will read your repository's existing labels and their descriptions to make smart labeling decisions. Want to improve the AI's accuracy? Just update your label descriptions in GitHub's UI.

## ⚙️ Configuration
This action supports a few required and optional settings. 

### LLM Configuration

You must specify an LLM provider and provide an API key. You can use either OpenAI or Anthropic models:


#### LLM Model

```yaml
- uses: jlowin/ai-labeler@v0.2.0
  with:
    controlflow-llm-model: openai/gpt-4o-mini
```

The `controlflow-llm-model` input determines which model to use. Supported formats:
- OpenAI: `openai/<model-name>` (e.g., "openai/gpt-4o-mini")
- Anthropic: `anthropic/<model-name>` (e.g., "anthropic/claude-3-5-sonnet-20241022")

The default is "openai/gpt-4o-mini". See the [ControlFlow LLM documentation](https://controlflow.ai/guides/configure-llms#automatic-configuration) for more information on supported models.

Note that you must provide an appropriate API key for your selected LLM provider.

#### OpenAI

```yaml
- uses: jlowin/ai-labeler@v0.2.0
  with:
    openai-api-key: ${{ secrets.OPENAI_API_KEY }}
    
    # Optionally specify a different model
    controlflow-llm-model: openai/gpt-4o
```

Set your OpenAI API key as a repository secret named `OPENAI_API_KEY`. Since the default model is `openai/gpt-4o-mini`, you don't need to specify a model unless you want to change it.

#### Anthropic

```yaml
- uses: jlowin/ai-labeler@v0.2.0
  with:
    anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

    # You must specify a model
    controlflow-llm-model: anthropic/claude-3-5-sonnet-20241022
```

Set your Anthropic API key as a repository secret named `ANTHROPIC_API_KEY`. To use Anthropic, you must specify a model.

### Fine-Tuning Configuration File

By default, the action looks for additional configuration in `.github/ai-labeler.yml`. You can specify a different location:

```yaml
- uses: jlowin/ai-labeler@v0.2.0
  with:
    config-path: .github/my-custom-config.yml
```

This file controls the labeling behavior - see the Fine-Tuning section below for details.

## 🎯 Fine-Tuning

You can create a config file to customize the labeling behavior. By default, the action looks for `.github/ai-labeler.yml`.


### Instructions

Global guidance for the AI labeler:

```yaml
instructions: |
  You're our labeling expert! Please help keep our repository organized by:
  - Using 'bug' only for confirmed issues, not feature requests
  - Applying 'help wanted' to good first-time contributor opportunities
  - Being generous with 'good first issue' to encourage new contributors
```

### Include Repository Labels

By default, the AI will use all labels that have been defined in your repository, including the enhanced definitions provided in your fine-tuning file. You can override this behavior to ONLY use the labels defined in this file:

```yaml
# If false, only use labels defined in this file (default: true)
include_repo_labels: false
```

Note that if `include_repo_labels` is `true`, the descriptions and instructions you provide in this file will override any defined in the repository. 

### Label Definitions

In the labels section, you can define or enhance specific labels that you want the AI to use. Any labels defined here that do not already exist in your repository will be created automatically. Note that this section's behavior is impacted by the `include_repo_labels` setting.

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

### Context Files

By default, the LLM context includes a variety of information about the issue or PR in question, as well as information about available labels. You can specify additional files the AI should consider when making decisions:

```yaml
context_files:
  - .github/CODEOWNERS
  - CONTRIBUTING.md
  - .github/ISSUE_TEMPLATE/bug_report.md
```

## 🎨 Examples

Here are some examples of interesting labeling behaviors you can configure:

### Basic Label Application

This example shows a basic configuration for a `bug` label, including instructions for the AI to follow when labeling issues.

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

### Maintainer-Specific Labels

By adding `CODEOWNERS` to the context files, the AI can use that information to label issues that need review from specific teams.

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

### Release Note Management

GitHub can [automatically generate release notes](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes#configuring-automatically-generated-release-notes) for each release, using labels to categorize changes. You can use the AI labeler to determine whether a change should be excluded from release notes, or appears to introduce a breaking change, both of which can be reflected in the generated release notes.

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

### Automated Triage

Labels are often used for triaging issues, and the AI labeler can use the provided content to assist with a first pass.

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
### Size-based Labeling

Global instructions for labeling PRs based on the number of lines changed:

```yaml
instructions: |
  When labeling pull requests, apply size labels based on these criteria:
  - 'size/XS': 0-9 lines changed
  - 'size/S': 10-29 lines changed
  - 'size/M': 30-99 lines changed
  - 'size/L': 100-499 lines changed
  - 'size/XL': 500+ lines changed
  
  Don't count changes to:
  - Auto-generated files
  - Package-lock.json or similar
  - Simple formatting changes
```

### Security Review Routing

Based on the contents of the PR, the AI can apply a `security-review` label and mark the issue as high priority.


```yaml
instructions: |
  Apply 'security-review' label if the changes involve:
  - Authentication/authorization code
  - Cryptographic operations
  - File system access
  - Network requests
  - Environment variables
  - Dependencies with known vulnerabilities
  
  Also apply 'high-priority' if the changes are in:
  - auth/*
  - security/*
  - crypto/*

context_files:
  - .github/SECURITY.md
  - .github/CODEOWNERS
```

### Automated Dependency Management

For dependency-related changes, the AI can apply a `dependencies` label and add additional labels based on the change type.

```yaml
instructions: |
  For dependency-related changes:
  1. Apply 'dependencies' label to all dependency updates
  2. Additionally:
    - Apply 'security' if it's a security update
    - Apply 'breaking-change' if it's a major version bump
    - Apply 'ci-only' if it only affects dev/test dependencies
  
  For package.json changes:
  - Apply 'frontend-deps' if touching frontend dependencies
  - Apply 'backend-deps' if touching backend dependencies
```

### Avoid Spam PRs

The AI can help maintain PR quality by applying labels based on the PR contents.

```yml
labels:
  - needs-improvement:
    description: "PR needs substantial improvements to meet quality standards"
    instructions: |
      Apply this label to PRs that show signs of being low-effort or opportunistic:
      
      Documentation:
      - Unnecessary formatting changes
      - Broken or circular links
      - Machine-translated content
      
      Code:
      - Changes that introduce complexity without justification
      - Copy-pasted code without attribution
      - Changes that bypass tests or reduce coverage
      - Trivial variable renaming
      
      Patterns:
      - PRs that ignore project conventions
      - Auto-generated or templated content
      - PRs that copy issues without adding value
      
      However, be careful not to discourage genuine first-time contributors who may be unfamiliar with best practices.
      If the PR can be improved with guidance, also apply the 'help-wanted' label.

  - invalid:
    description: "PR does not meet contribution guidelines or appears to be spam"
    instructions: |
      Apply this label when a PR appears to be:
      - Automated spam content
      - Deliberately gaming contribution counts
      - Excessive self-promotion
      - Pure promotional content without value
      
      When this label is applied, include a comment explaining why and link to contributing guidelines.

context_files:
  - .github/pull_request_template.md
  - CONTRIBUTING.md
  - CODE_OF_CONDUCT.md
```

## 🤝 Contributing

Issues and PRs welcome! And don't worry about labels – we've got that covered! 😉