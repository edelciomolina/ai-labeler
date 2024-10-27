import os
import json
from github import Github
from pydantic import BaseModel
from typing import Optional


class PullRequest(BaseModel):
    title: str
    body: str
    changed_files: list[dict[str, str]]


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
    number = get_event_number()

    # If dry-run is enabled, just print the labels that would be applied
    if os.getenv("INPUT_DRY-RUN", "false").lower() == "true":
        print(f"Dry run: Would apply labels {labels} to #{number}")
        return

    item = repo.get_issue(number)  # works for both PRs and issues
    item.add_to_labels(*labels)


def get_event_number() -> int:
    """Get the PR/Issue number from context or input"""
    # Try GitHub event context first
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
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
