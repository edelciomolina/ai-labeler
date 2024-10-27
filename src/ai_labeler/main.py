from enum import Enum
import os
import controlflow as cf
from github import Github
from pydantic import BaseModel
from typing import Optional, Union


class PullRequest(BaseModel):
    title: str
    body: str
    changed_files: list[str]


class Issue(BaseModel):
    title: str
    body: str


class Label(BaseModel):
    name: str
    description: Optional[str] = None


def get_available_labels(gh_client: Github) -> list[Label]:
    """Fetch available labels and their descriptions from the repository"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    labels = repo.get_labels()
    return [Label(name=label.name, description=label.description) for label in labels]


def apply_labels(gh_client: Github, labels: list[str]) -> None:
    """Apply the chosen labels to the PR/issue"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    number = int(os.getenv("GITHUB_EVENT_NUMBER"))

    # If dry-run is enabled, just print the labels that would be applied
    if os.getenv("INPUT_DRY-RUN", "false").lower() == "true":
        print(f"Dry run: Would apply labels {labels} to #{number}")
        return

    item = repo.get_issue(number)  # works for both PRs and issues
    item.add_to_labels(*labels)


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue], labels: list[Label]
) -> list[str]:
    LabelChoice = Enum(
        "LabelChoice", {label.name: label.name for label in labels}, type=str
    )

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions="""
        You are an expert at categorizing GitHub issues and pull requests.
        Analyze the content carefully and assign appropriate labels from the available set. You may assign zero or more labels.
        Consider the label descriptions to better understand their intended usage.
        Be conservative - only assign labels when you're confident they apply.
        """,
    )

    # Task to analyze and choose labels
    decision = cf.run(
        "Analyze the PR/issue and choose appropriate labels",
        result_type=list[LabelChoice],
        context={"pr_or_issue": item, "all_labels": labels},
        agents=[labeler],
    )

    # The decision.result.labels should still contain just the label names
    return [label.value for label in decision]


def get_event_number() -> int:
    """Get the PR/Issue number from context or input"""
    # Try GitHub event context first
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
        import json

        with open(event_path) as f:
            event = json.load(f)
            return (
                event.get("number")
                or event.get("pull_request", {}).get("number")
                or event.get("issue", {}).get("number")
            )

    # Fall back to input if provided
    input_number = os.getenv("INPUT_EVENT-NUMBER")
    if input_number:
        return int(input_number)

    raise ValueError("Could not find PR/Issue number")


def main() -> None:
    # Set up GitHub client
    gh = Github(os.getenv("INPUT_GITHUB-TOKEN"))
    repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))

    # For debugging
    print("Available environment variables:")
    for k, v in os.environ.items():
        if k.startswith(("GITHUB_", "INPUT_")):
            print(f"{k}={v}")

    # Get the PR/Issue number
    number = get_event_number()
    event_type = os.getenv("GITHUB_EVENT_NAME")

    # Get available labels
    available_labels = get_available_labels(gh)

    # Get the item (PR or issue)
    if event_type == "pull_request":
        pr = repo.get_pull(number)
        item = PullRequest(
            title=pr.title,
            body=pr.body or "",
            changed_files=[f.filename for f in pr.get_files()],
        )
    else:  # issue
        issue = repo.get_issue(number)
        item = Issue(title=issue.title, body=issue.body or "")

    # Run the labeling workflow
    chosen_labels = labeling_workflow(item, available_labels)

    # Apply the labels
    apply_labels(gh, chosen_labels)


if __name__ == "__main__":
    main()
