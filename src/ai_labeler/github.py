import os
import json
from typing import Optional
from github import Github
from pydantic import BaseModel
from .config_parser import Config


class PullRequest(BaseModel):
    title: str
    body: str
    files: dict[str, str]
    author: str  # GitHub username


class Issue(BaseModel):
    title: str
    body: str
    author: str  # GitHub username


class Label(BaseModel):
    name: str
    description: Optional[str] = None
    instructions: Optional[str] = None


# Simple cache to store labels per repository
_label_cache: dict[str, list[Label]] = {}


def get_available_labels(
    gh_client: Github, *, repository: str | None = None
) -> list[Label]:
    """Fetch available labels and their descriptions from the repository"""
    repo_name = repository or os.getenv("GITHUB_REPOSITORY")
    if repo_name is None:
        raise ValueError("repository is required")

    # Return cached result if available
    if repo_name in _label_cache:
        return _label_cache[repo_name]

    # Fetch and cache labels
    repo = gh_client.get_repo(repo_name)
    labels = repo.get_labels()
    result = [Label(name=label.name, description=label.description) for label in labels]

    _label_cache[repo_name] = result
    return result.copy()


def apply_labels(
    gh_client: Github,
    labels: list[str],
    *,
    repository: str | None = None,
    number: int | None = None,
    dry_run: bool = False,
) -> None:
    """Apply the chosen labels to the PR/issue"""
    repo_name = repository or os.getenv("GITHUB_REPOSITORY")
    if repo_name is None:
        raise ValueError("repository is required")

    item_number = number or get_event_number()
    if item_number is None:
        raise ValueError("number is required")

    repo = gh_client.get_repo(repo_name)

    # If dry-run is enabled, just print the labels that would be applied
    if dry_run:
        print(f"Dry run: Would apply labels {labels} to #{item_number}")
        return

    item = repo.get_issue(item_number)
    item.add_to_labels(*labels)


def get_event_number(*, event_path: str | None = None) -> int:
    """Get the PR/Issue number from context or input"""
    # Use input if provided
    input_number = os.getenv("INPUT_EVENT-NUMBER")
    if input_number:
        return int(input_number)

    # Use GitHub event context
    gh_event_path = event_path or os.getenv("GITHUB_EVENT_PATH")
    if gh_event_path:
        with open(gh_event_path) as f:
            event = json.load(f)
            number = (
                event.get("number")
                or event.get("pull_request", {}).get("number")
                or event.get("issue", {}).get("number")
            )
            if number:
                return number

    raise ValueError("Could not find PR/Issue number")


def create_label(
    gh_client: Github,
    name: str,
    description: str,
    *,
    repository: str | None = None,
) -> None:
    """Create a new label on the repository"""
    repo_name = repository or os.getenv("GITHUB_REPOSITORY")
    if repo_name is None:
        raise ValueError("repository is required")

    repo = gh_client.get_repo(repo_name)
    repo.create_label(name=name, description=description, color="ededed")


def get_available_labels_from_config(
    gh_client: Github,
    config: "Config",
    *,
    repository: str | None = None,
) -> list[Label]:
    """
    Get all available labels, creating any missing ones from config and filtering
    based on config settings.
    """
    # Get all repo labels
    repo_labels = get_available_labels(gh_client, repository=repository)
    repo_names = {label.name for label in repo_labels}

    # Create any missing labels from config
    for cfg in config.labels:
        if cfg.name not in repo_names:
            print(f"Label {cfg.name} was not found on the repository, creating...")
            create_label(
                gh_client,
                name=cfg.name,
                description=cfg.description or "",
                repository=repository,
            )
            repo_labels.append(
                Label(
                    name=cfg.name,
                    description=cfg.description or "",
                    instructions=cfg.instructions,
                )
            )

    # Filter to only config labels if include_repo_labels is False
    if not config.include_repo_labels:
        config_names = {cfg.name for cfg in config.labels}
        repo_labels = [label for label in repo_labels if label.name in config_names]

    # Enhance labels with config overrides
    config_map = {cfg.name: cfg for cfg in config.labels}

    labels = []
    for label in repo_labels:
        if label.name in config_map:
            cfg = config_map[label.name]
            # Create a new label instead of modifying in place
            label = Label(
                name=label.name,
                description=cfg.description or label.description,
                instructions=cfg.instructions,
            )
        labels.append(label)

    return labels
