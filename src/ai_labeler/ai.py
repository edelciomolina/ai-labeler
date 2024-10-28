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
    name: str
    description: str | None = None
    instructions: str | None = None


@dataclass
class Config:
    instructions: str
    include_repo_labels: bool
    labels: list[LabelConfig]
    context_files: list[str] = None  # New field

    @classmethod
    def load(cls) -> "Config":
        # Get config path from action input, falling back to default
        workspace_path = os.getenv("GITHUB_WORKSPACE", "")
        config_path = os.getenv("INPUT_CONFIG-PATH", ".github/ai-labeler.yml")
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
                    # Dict with additional properties
                    name = item.pop("name")
                    label_configs.append(LabelConfig(name=name, **item))

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


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue], labels: list[Label]
) -> list[str]:
    # Load configuration and context files
    config = Config.load()
    context_files = config.load_context_files()

    LabelChoice = Enum(
        "LabelChoice", {label.name: label.name for label in labels}, type=str
    )

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions=f"""
        You are an expert at categorizing GitHub issues and pull requests.
        
        Be conservative - only assign labels when you're confident they apply.
        
        Your context includes a description of the issue or PR, as well as all
        available labels and any additional description or instructions, and
        also any other files from the repo that may be relevant to your task.
        
        Additional instructions:
        
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
        context={
            "pr_or_issue": item,
            "all_labels": labels,
            "additional_files": context_files,
        },
        agents=[labeler],
        model_kwargs=dict(tool_choice="required"),
    )

    return [label.value for label in decision]
