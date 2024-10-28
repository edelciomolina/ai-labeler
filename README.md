# 🤖 AI Labeler

Let an LLM handle the labeling! 

This GitHub Action uses AI to label your issues and PRs, keeping your repo organized so you can focus on what matters.



## ✨ Features

- **Smart Analysis**: Understands context from titles, descriptions, and code changes
- **Incremental**: Works alongside other label management tools and manual labeling
- **Zero Config**: Works out of the box with your existing GitHub labels
- **Customizable**: Fine-tune behavior with optional configuration
- **Reliable**: Supports OpenAI and Anthropic's latest models, orchestrated with ControlFlow

## 🚀 Quick Start

1. Add `.github/workflows/ai-labeler.yml` to your repo.
2. Add your API key(s) to your repository's secrets using the same names as `ai-labeler.yml` expects.

Here is a full example of `ai-labeler.yml` that you can copy and paste into your repo. Make sure to set the `OPENAI_API_KEY` secret!


```yaml
name: AI Labeler

# Trigger on issues and PRs
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

          # --- Optional settings ---
          
          # Optional: use a different model
          # controlflow-llm-model: anthropic/claude-3-sonnet-20240229
          
          # Required if using an Anthropic model:
          # anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}

          # Optional: your config file path
          # config-path: .github/ai-labeler.yml
```


That's it! The AI will read your repository's existing labels and their descriptions to make smart labeling decisions. Want to improve the AI's accuracy? Just update your label descriptions in GitHub's UI.

## 🎯 Fine-Tuning (Optional)

You can create a config file to provide additional instructions and control over the labeling behavior. Labels defined in the config will be created on your repository if they don't exist.

### Configuration Options

Create `.github/ai-labeler.yml` (default location; can be overridden by setting the `config-path` input) with any of these options:

- `instructions`: Overall guidance for the AI labeler
- `include_repo_labels`: Whether to include repository labels not defined in config (default: true)
- `labels`: Label definitions
  - `description`: What the label means
  - `instructions`: Detailed criteria for applying the label

Here's an example that shows some of the ways you can guide the AI's decisions:

```yaml
# Give the AI some personality and guidance
instructions: |
  You're our labeling expert! Please help keep our repository organized by:
  - Using 'bug' only for confirmed issues, not feature requests
  - Applying 'help wanted' to good first-time contributor opportunities
  - Being generous with 'good first issue' to encourage new contributors


# If false, only use labels defined in this file (default: true)
include_repo_labels: false

# Define or enhance specific label behaviors
labels:
  # simple form: just the name
  - includes-question

  # expanded form: name, optional description, and optional instructions
  - maintainer:
    description: "Opened by a maintainer (@abc, @xyz, etc.)"

  - documentation:
    description: "Documentation changes"
    instructions: |
      Apply when changes are primarily documentation-focused:
      - Changes to README, guides, or other .md files
      - Updates to docstrings or inline documentation
      - Issues requesting clearer docs or examples
      - For PRs, look for changes in docs/ directory or .md files
        
  - deps:
    description: "Dependency updates"
    instructions: |
      For changes to project dependencies:
      - Updates to requirements.txt, pyproject.toml, etc.
      - Version bumps in package configs
      - Don't apply for documentation-only dependency changes
      
  - security:
    description: "Security-related changes"
    instructions: |
      High priority! Apply when:
      - Issue describes a security vulnerability
      - PR fixes a security issue
      - Changes touch security-critical code paths
      Look especially at changes in security/, auth/, or crypto/ directories

  - ui:
    description: "User interface changes"
    instructions: |
      For frontend and UI-related changes:
      - Changes to HTML/CSS/JS in frontend/
      - Visual design updates
      - UX improvements
      - User-facing text changes
```

## 🤝 Contributing

Issues and PRs welcome! And don't worry about labels – we've got that covered! 😉
