import os
import json
from github import Github
from ai_labeler.github import (
    get_available_labels_from_config,
    apply_labels,
    PullRequest,
    Issue,
    get_event_number,
)
from ai_labeler.ai import labeling_workflow, Config


def run_label_workflow() -> list[str]:
    # Set up GitHub client
    gh = Github(os.getenv("INPUT_GITHUB-TOKEN"))
    repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))

    # Get the PR/Issue number
    number = get_event_number()

    # Load config and get available labels
    config = Config.load()
    available_labels = get_available_labels_from_config(gh, config)

    # Get the item to label
    issue = repo.get_issue(number)
    if issue.pull_request:
        pr = repo.get_pull(number)
        item = PullRequest(
            title=pr.title,
            body=pr.body or "",
            changed_files=[{f.filename: f.patch} for f in pr.get_files()],
        )
    else:
        item = Issue(title=issue.title, body=issue.body or "")

    # Run the labeling workflow
    labels = labeling_workflow(item=item, labels=available_labels)

    # Apply the labels
    apply_labels(gh, labels)

    # Set output for GitHub Actions
    if os.getenv("GITHUB_OUTPUT"):
        with open(os.getenv("GITHUB_OUTPUT"), "a") as f:
            f.write(f"labels={json.dumps(labels)}\n")

    return labels


if __name__ == "__main__":
    run_label_workflow()
