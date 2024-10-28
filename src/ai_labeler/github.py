import os
import json
from github import Github
from pydantic import BaseModel
from dataclasses import dataclass


class PullRequest(BaseModel):
    title: str
    body: str
    changed_files: list[dict[str, str]]


class Issue(BaseModel):
    title: str
    body: str


@dataclass
class Label:
    name: str
    description: str = ""
    instructions: str | None = None


# Simple cache to store labels per repository
_label_cache: dict[str, list[Label]] = {}


def get_available_labels(gh_client: Github) -> list[Label]:
    """Fetch available labels and their descriptions from the repository"""
    repo_name = os.getenv("GITHUB_REPOSITORY")

    # Return cached result if available
    if repo_name in _label_cache:
        return _label_cache[repo_name]

    # Fetch and cache labels
    repo = gh_client.get_repo(repo_name)
    labels = repo.get_labels()
    result = [Label(name=label.name, description=label.description) for label in labels]

    _label_cache[repo_name] = result
    return result


def apply_labels(gh_client: Github, labels: list[str]) -> None:
    """Apply the chosen labels to the PR/issue"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    number = get_event_number()

    # If dry-run is enabled, just print the labels that would be applied
    if os.getenv("INPUT_DRY-RUN", "false").lower() == "true":
        print(f"Dry run: Would apply labels {labels} to #{number}")
        return

    item = repo.get_issue(number)
    item.add_to_labels(*labels)


def get_event_number() -> int:
    """Get the PR/Issue number from context or input"""

    # Use input if provided
    input_number = os.getenv("INPUT_EVENT-NUMBER")
    if input_number:
        return int(input_number)

    # Use GitHub event context
    event_path = os.getenv("GITHUB_EVENT_PATH")
    if event_path:
        with open(event_path) as f:
            event = json.load(f)
            return (
                event.get("number")
                or event.get("pull_request", {}).get("number")
                or event.get("issue", {}).get("number")
            )

    raise ValueError("Could not find PR/Issue number")


def create_label(gh_client: Github, name: str, description: str) -> None:
    """Create a new label on the repository"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    repo.create_label(name=name, description=description, color="ededed")
