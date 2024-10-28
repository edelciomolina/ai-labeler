import os
from pathlib import Path
import yaml
from enum import Enum
import controlflow as cf
from typing import Union
from dataclasses import dataclass
from .github import PullRequest, Issue, Label


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
        workspace_path = os.getenv("GITHUB_WORKSPACE")
        config_path = os.getenv("INPUT_CONFIG-PATH", ".github/ai-labeler.yml")
        full_path = Path(workspace_path) / config_path

        try:
            with open(full_path) as f:
                data = yaml.safe_load(f)

            # Convert the labels dict to use LabelConfig objects
            label_configs = {
                name: LabelConfig(**cfg) if isinstance(cfg, dict) else LabelConfig(cfg)
                for name, cfg in data.get("labels", {}).items()
            }

            print(f"Loaded config from {config_path}")

            return cls(
                instructions=data.get("instructions", ""),
                include_repo_labels=data.get("include_repo_labels", True),
                labels=label_configs,
            )
        except FileNotFoundError:
            print(f"No config file found at {config_path}, using default config")
            # If no config file exists, return default config
            return cls(
                instructions="",
                include_repo_labels=True,
                labels={},
            )


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue], labels: list[Label]
) -> list[str]:
    # Load configuration
    config = Config.load()

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
