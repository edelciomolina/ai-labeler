import yaml


from dataclasses import dataclass
from pathlib import Path


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

    def load_context_files(self, repo_root_path: str) -> dict[str, str]:
        """Load the contents of context files"""
        context = {}
        for file_path in self.context_files or []:
            full_path = Path(repo_root_path) / file_path
            try:
                with open(full_path) as f:
                    context[file_path] = f.read()
            except FileNotFoundError:
                print(f"Warning: Context file {file_path} not found")
        return context
