import os
import yaml
from enum import Enum
import controlflow as cf
from typing import Union
from dataclasses import dataclass
from .github import PullRequest, Issue, Label, create_label, get_available_labels


@dataclass
class LabelConfig:
    description: str
    instructions: str | None = None


@dataclass
class Config:
    instructions: str
    include_repo_labels: bool
    labels: dict[str, LabelConfig]

    @classmethod
    def load(cls) -> "Config":
        # Get config path from action input, falling back to default
        config_path = os.getenv("INPUT_CONFIG-PATH", ".github/ai-labeler.yml")

        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            # Convert the labels dict to use LabelConfig objects
            label_configs = {
                name: LabelConfig(**cfg) if isinstance(cfg, dict) else LabelConfig(cfg)
                for name, cfg in data.get("labels", {}).items()
            }

            return cls(
                instructions=data.get("instructions", ""),
                include_repo_labels=data.get("include_repo_labels", True),
                labels=label_configs,
            )
        except FileNotFoundError:
            # If no config file exists, return default config
            return cls(
                instructions="",
                include_repo_labels=True,
                labels={},
            )


def sync_config_labels(config: Config, gh_client) -> list[Label]:
    """
    Ensure all labels from config exist on the repo and return updated label list.
    """
    existing_labels = get_available_labels(gh_client)
    existing_names = {label.name for label in existing_labels}

    # Create any missing labels
    for name, cfg in config.labels.items():
        if name not in existing_names:
            create_label(gh_client, name=name, description=cfg.description)
            existing_labels.append(Label(name=name, description=cfg.description))

    return existing_labels


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue], labels: list[Label], gh_client
) -> list[str]:
    # Load configuration
    config = Config.load()

    # Ensure all config labels exist and get updated label list
    labels = sync_config_labels(config, gh_client)

    # If strict_labels is True, filter labels to only those in config
    if not config.include_repo_labels:
        labels = [label for label in labels if label.name in config.labels]

    # Enhance labels with config instructions
    for label in labels:
        if label.name in config.labels:
            cfg = config.labels[label.name]
            label.description = cfg.description
            label.instructions = cfg.instructions

    LabelChoice = Enum(
        "LabelChoice", {label.name: label.name for label in labels}, type=str
    )

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions=f"""
        You are an expert at categorizing GitHub issues and pull requests.
        
        Be conservative - only assign labels when you're confident they apply.
        
        {config.instructions}
        """.strip(),
    )

    # Task to analyze and choose labels
    decision = cf.run(
        """
        Analyze the PR/issue carefully and assign appropriate labels from the
        available set. You may assign any number of labels, including no labels.
        You should do your best to assign labels based on what would be most
        helpful to the repo maintainers, taking the label descriptions into
        account as well as any additional instructions.
        """,
        result_type=list[LabelChoice],
        context={"pr_or_issue": item, "all_labels": labels},
        agents=[labeler],
        model_kwargs=dict(tool_choice="required"),
    )

    return [label.value for label in decision]
