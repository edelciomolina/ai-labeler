from enum import Enum
import controlflow as cf
from typing import Optional, Union
from .github import PullRequest, Issue, Label


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue],
    labels: list[Label],
    instructions: Optional[str] = None,
    context_files: Optional[dict[str, str]] = None,
    llm_model: Optional[str] = None,
) -> list[str]:
    # Load configuration and context files

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
        
        {instructions or 'None.'}
        """,
        model=llm_model or "openai/gpt-4o-mini",
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
            "context_files": context_files,
        },
        agents=[labeler],
        model_kwargs=dict(tool_choice="required"),
    )

    return [label.value for label in decision]
