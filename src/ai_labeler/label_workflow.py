import os
from github import Github
from .github import (
    get_available_labels,
    apply_labels,
    PullRequest,
    Issue,
    get_event_number,
)
from .ai import labeling_workflow


def run_label_workflow() -> None:
    # Set up GitHub client
    gh = Github(os.getenv("INPUT_GITHUB-TOKEN"))
    repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))

    # Get the PR/Issue number
    number = get_event_number()

    # Get available labels
    available_labels = get_available_labels(gh)

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
    chosen_labels = labeling_workflow(item, available_labels)

    # Apply the labels
    apply_labels(gh, chosen_labels)


if __name__ == "__main__":
    run_label_workflow()
