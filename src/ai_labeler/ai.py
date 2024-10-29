import controlflow as cf
from typing import Optional, Union

from pydantic import BaseModel, Field
from .github import PullRequest, Issue, Label


@cf.flow
def labeling_workflow(
    item: Union[PullRequest, Issue],
    labels: list[Label],
    instructions: Optional[str] = None,
    context_files: Optional[dict[str, str]] = None,
    llm_model: Optional[str] = None,
) -> list[str]:
    class Decision(BaseModel):
        # without reasoning, gpt-4o-mini sometimes ignores label instructions
        reasoning: str = Field(description="A few sentences explaining your decision.")
        label_indices: list[int]

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions="""
        You are an expert AI that automatically labelling GitHub issues and pull
        requests. You always pay close attention to label instructions.
        """,
        model=llm_model or "openai/gpt-4o-mini",
    )

    # Task to analyze and choose labels
    decision = cf.run(
        """
        Select labels for the provided PR/issue. Consider all available context, including description and files. Choose the index of the most
        appropriate labels; you may assign any number of labels or none at all.
        
        You MUST read label instructions carefully to see if they are appropriate for this PR/issue.
        """,
        instructions=instructions,
        result_type=Decision,
        context={
            "pr_or_issue_to_label": item,
            "available_labels": dict(enumerate(labels)),
            "additional_context": context_files,
        },
        agents=[labeler],
        model_kwargs=dict(tool_choice="required"),
        handlers=[],
    )

    selected_labels = [labels[i].name for i in decision.label_indices]

    print(f"Available labels: {dict(enumerate(labels))}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Selected labels: {selected_labels}")

    return selected_labels
