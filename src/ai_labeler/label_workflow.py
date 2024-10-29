import os
import json
from pathlib import Path
from github import Github
from ai_labeler.config_parser import Config
from ai_labeler.github import (
    get_available_labels_from_config,
    apply_labels,
    PullRequest,
    Issue,
    get_event_number,
)
from ai_labeler.ai import labeling_workflow


def run_label_workflow_from_env() -> list[str]:
    """Helper that loads config from environment and runs the workflow"""
    return run_label_workflow(
        github_token=os.getenv("INPUT_GITHUB-TOKEN"),
        github_repository=os.getenv("GITHUB_REPOSITORY"),
        event_number=int(os.getenv("INPUT_EVENT-NUMBER"))
        if os.getenv("INPUT_EVENT-NUMBER")
        else None,
        config_path=os.getenv("INPUT_CONFIG-PATH"),
        github_workspace=os.getenv("GITHUB_WORKSPACE"),
        dry_run=os.getenv("INPUT_DRY-RUN", "false").lower() == "true",
        github_output=os.getenv("GITHUB_OUTPUT"),
    )


def run_label_workflow(
    *,
    github_token: str,
    github_repository: str,
    event_number: int | None = None,
    config_path: str | None = None,
    github_workspace: str | None = None,
    dry_run: bool = False,
    github_output: str | None = None,
) -> list[str]:
    """Main workflow function that accepts explicit configuration"""

    config_path = config_path or ".github/ai-labeler.yml"
    github_workspace = github_workspace or os.getenv("GITHUB_WORKSPACE", "")
    github_output = github_output or os.getenv("GITHUB_OUTPUT")

    # Create full config path
    full_config_path = Path(github_workspace) / config_path

    # Set up GitHub client
    gh = Github(github_token)
    repo = gh.get_repo(github_repository)

    # Get the PR/Issue number
    number = event_number or get_event_number()

    # Load config and get available labels
    config = Config.load(config_path=str(full_config_path))
    available_labels = get_available_labels_from_config(gh, config)

    # Get the item to label
    issue = repo.get_issue(number)
    if issue.pull_request:
        pr = repo.get_pull(number)
        item = PullRequest(
            title=pr.title,
            body=pr.body or "",
            files={f.filename: f.patch for f in pr.get_files()},
            author=pr.user.login,
        )
    else:
        item = Issue(
            title=issue.title,
            body=issue.body or "",
            author=issue.user.login,
        )

    # Run the labeling workflow
    labels = labeling_workflow(
        item=item,
        labels=available_labels,
        instructions=config.instructions,
        context_files=config.load_context_files(),
    )

    # Apply the labels
    apply_labels(gh, labels, dry_run=dry_run)

    # Set output for GitHub Actions
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"labels={json.dumps(labels)}\n")

    return labels


if __name__ == "__main__":
    run_label_workflow_from_env()
