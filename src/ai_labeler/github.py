import os
import json
import re
from typing import Optional, List
from github import Github
from pydantic import BaseModel, Field
from .config_parser import Config


class LinkedItem(BaseModel):
    """Represents a linked GitHub issue or PR"""

    number: int
    title: str
    body: str
    labels: List[str]
    type: str = Field(..., pattern="^(issue|pull_request)$")


class PullRequest(BaseModel):
    title: str
    body: str
    files: dict[str, str | None]
    author: str  # GitHub username
    linked_items: List[LinkedItem] = Field(default_factory=list)


class Issue(BaseModel):
    title: str
    body: str
    author: str  # GitHub username
    linked_items: List[LinkedItem] = Field(default_factory=list)


class Label(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None


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
    return result.copy()


def apply_labels(gh_client: Github, labels: list[str], dry_run: bool = False) -> None:
    """Apply the chosen labels to the PR/issue"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    number = get_event_number()

    # If dry-run is enabled, just print the labels that would be applied
    if dry_run:
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


def get_available_labels_from_config(
    gh_client: Github,
    config: "Config",
    *,
    include_repo_labels: bool = True,
) -> list[Label]:
    """
    Get all available labels, creating any missing ones from config and filtering
    based on settings.
    """
    # Get all repo labels
    repo_labels = get_available_labels(gh_client)
    repo_names = {label.name.lower() for label in repo_labels}

    # Create any missing labels from config
    for cfg in config.labels:
        if cfg.name.lower() not in repo_names:
            print(f"Label {cfg.name} was not found on the repository, creating...")
            create_label(gh_client, name=cfg.name, description=cfg.description or "")
            repo_labels.append(
                Label(
                    name=cfg.name,
                    description=cfg.description or "",
                    instructions=cfg.instructions,
                )
            )

    # Filter to only config labels if include_repo_labels is False
    if not include_repo_labels:
        config_names = {cfg.name for cfg in config.labels}
        repo_labels = [label for label in repo_labels if label.name in config_names]

    # Enhance labels with config overrides
    config_map = {cfg.name: cfg for cfg in config.labels}

    labels = []
    for label in repo_labels:
        if label.name in config_map:
            cfg = config_map[label.name]
            label = Label(
                name=label.name,
                description=cfg.description or label.description,
                instructions=cfg.instructions,
            )
        labels.append(label)

    return labels


def parse_github_links(text: str) -> List[int]:
    """Extract GitHub issue/PR numbers from text using common formats:
    - #123
    - repo#123
    - org/repo#123
    """
    # Match #123 format
    numbers = set()

    # Basic #123 format
    matches = re.finditer(r"(?:^|\s)#(\d+)(?:\s|$)", text)
    numbers.update(int(m.group(1)) for m in matches)

    # org/repo#123 or repo#123 format (only care about numbers in current repo)
    matches = re.finditer(r"(?:[\w-]+/)?[\w-]+#(\d+)", text)
    numbers.update(int(m.group(1)) for m in matches)

    return sorted(numbers)


def fetch_linked_items(gh_client: Github, numbers: List[int]) -> List[LinkedItem]:
    """Fetch full context of linked issues/PRs"""
    repo = gh_client.get_repo(os.getenv("GITHUB_REPOSITORY"))
    linked_items = []

    for number in numbers:
        try:
            issue = repo.get_issue(number)
            item_type = "pull_request" if issue.pull_request else "issue"

            linked_items.append(
                LinkedItem(
                    number=number,
                    title=issue.title,
                    body=issue.body or "",
                    labels=[label.name for label in issue.labels],
                    type=item_type,
                )
            )
        except Exception as e:
            print(f"Warning: Failed to fetch item #{number}: {e}")

    return linked_items
