import os
from typing import Optional
from pydantic import BaseModel
import yaml


from pathlib import Path


class LabelConfig(BaseModel):
    name: str
    description: str | None = None
    instructions: str | None = None


class Config(BaseModel):
    instructions: Optional[str] = None
    labels: list[LabelConfig] = []
    context_files: list[str] = []

    @classmethod
    def load(cls, config_path: str) -> "Config":
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)

            labels_data = data.get("labels", [])
            label_configs = []

            for item in labels_data:
                if isinstance(item, str):
                    # Simple string label
                    label_configs.append(LabelConfig(name=item))
                else:
                    # Dict with label name as key
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

            # Support both context-files and context_files (for backwards compatibility)
            context_files = data.get("context-files", data.get("context_files", []))

            return cls(
                instructions=data.get("instructions", ""),
                labels=label_configs,
                context_files=context_files,
            )
        except FileNotFoundError:
            # If no config file exists, return default config
            return cls(
                instructions="",
                labels=[],
                context_files=[],
            )

    def load_context_files(self, repo_root_path: str = None) -> dict[str, str]:
        """Load the contents of context files"""

        repo_root_path = repo_root_path or os.getenv("GITHUB_WORKSPACE")
        if repo_root_path is None:
            raise ValueError("repo_root_path is required and could not be inferred")

        context = {}
        for file_path in self.context_files or []:
            full_path = Path(repo_root_path) / file_path
            try:
                with open(full_path) as f:
                    context[file_path] = f.read()
            except FileNotFoundError:
                print(f"Warning: Context file {file_path} not found")
        return context
