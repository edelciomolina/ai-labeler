import os
import json
import yaml
from pathlib import Path
from dataclasses import dataclass
from github import Github
from ai_labeler.github import (
    get_available_labels_from_config,
    apply_labels,
    PullRequest,
    Issue,
    get_event_number,
)
from ai_labeler.ai import labeling_workflow


@dataclass
class LabelConfig:
    name: str
    description: str | None = None
    instructions: str | None = None


@dataclass
class Config:
    instructions: str
    include_repo_labels: bool
    labels: list[LabelConfig]
    context_files: list[str] = None

    @classmethod
    def load(cls, workspace_path: str = None, config_path: str = None) -> "Config":
        # Get config path from parameters, falling back to defaults
        workspace_path = workspace_path or os.getenv("GITHUB_WORKSPACE", "")
        config_path = config_path or os.getenv(
            "INPUT_CONFIG-PATH", ".github/ai-labeler.yml"
        )
        full_path = Path(workspace_path) / config_path

        try:
            with open(full_path) as f:
                data = yaml.safe_load(f)

            labels_data = data.get("labels", [])
            label_configs = []

            for item in labels_data:
                if isinstance(item, str):
                    # Simple string label
                    label_configs.append(LabelConfig(name=item))
                else:
                    # Dict with label name as key
                    # item is like {"label_name": {"description": "...", "instructions": "..."}}
                    name, props = next(iter(item.items()))
                    if props is None:
                        props = {}
                    label_configs.append(
                        LabelConfig(
                            name=name,
                            description=props.get("description"),
                            instructions=props.get("instructions"),
                        )
                    )

            return cls(
                instructions=data.get("instructions", ""),
                include_repo_labels=data.get("include_repo_labels", True),
                labels=label_configs,
                context_files=data.get("context_files", []),
            )
        except FileNotFoundError:
            # If no config file exists, return default config
            return cls(
                instructions="",
                include_repo_labels=True,
                labels=[],
                context_files=[],
            )

    def load_context_files(self, workspace_path: str = None) -> dict[str, str]:
        """Load the contents of context files"""
        if not workspace_path:
            workspace_path = os.getenv("GITHUB_WORKSPACE", "")

        context = {}
        for file_path in self.context_files or []:
            full_path = Path(workspace_path) / file_path
            try:
                with open(full_path) as f:
                    context[file_path] = f.read()
            except FileNotFoundError:
                print(f"Warning: Context file {file_path} not found")
        return context


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
    # Set up GitHub client
    gh = Github(github_token)
    repo = gh.get_repo(github_repository)

    # Get the PR/Issue number
    number = event_number or get_event_number()

    # Load config and get available labels
    ai_config = Config.load(
        workspace_path=github_workspace,
        config_path=config_path,
    )
    available_labels = get_available_labels_from_config(gh, ai_config)

    # Get the item to label
    issue = repo.get_issue(number)
    if issue.pull_request:
        pr = repo.get_pull(number)
        item = PullRequest(
            title=pr.title,
            body=pr.body or "",
            changed_files=[{f.filename: f.patch} for f in pr.get_files()],
            author=pr.user.login,
        )
    else:
        item = Issue(
            title=issue.title,
            body=issue.body or "",
            author=issue.user.login,
        )

    # Run the labeling workflow
    labels = labeling_workflow(item=item, labels=available_labels)

    # Apply the labels
    apply_labels(gh, labels, dry_run=dry_run)

    # Set output for GitHub Actions
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"labels={json.dumps(labels)}\n")

    return labels


if __name__ == "__main__":
    run_label_workflow_from_env()
