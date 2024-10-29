import controlflow as cf
from typing import Optional, Union

from pydantic import BaseModel
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
        reasoning: str
        labels: list[str]

        def validate_labels(cls, v):
            if any(label not in [l.name for l in labels] for label in v):
                raise ValueError(
                    f"Invalid labels. Must be one of {', '.join(f"{l.name}" for l in labels)}"
                )
            return v

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions="""
        You are an expert AI that automatically labelling GitHub issues and pull
        requests. You always pay close attention to label instructions.
        """,
        model=llm_model or "openai/gpt-4o-mini",
    )

    decision = cf.run(
        """
        Consider the provided PR/issue and its context. Examine each available
        label carefully. 
        
        Each label has a name and optional description and instructions. Treat
        all three as instructions for understanding whether the label is
        relevant.
        
        For labels that seem appropriate, provide a complete rationale of
        whether you would assign them to the PR/issue, taking your instructions
        and the label's instructions into account. Some labels will have
        specific instructions about when to apply them, or whether to apply them
        at all. These instructions take precedence over the label's inherent
        relevance. Be sure to reference all relevant context and instructions in
        your reasoning.
        
        You may select any number of labels or none at all. You do not need to
        reason about labels that are obviously irrelevant.
        
        Example reasoning format:
        
        - Label <name>: 
            
            1. <are there any instructions that apply to this label's
            applicability other than explaining its meaning?> 
            
            2. <reason about the label's applicability: do any instructions
            apply that would affect your decision?> 
            
            3. Apply label to PR/issue: <decision yes / no>
          
        - Label 2: 
        
            1. ...
            
        """,
        instructions=instructions,
        result_type=Decision,
        context={
            "pr_or_issue_to_label": item,
            "available_labels": dict(enumerate(labels)),
            "additional_context": context_files,
        },
        agents=[labeler],
        completion_tools=["SUCCEED"],  # the task can not be marked as failed
        model_kwargs=dict(tool_choice="required"),  # prevent chatting
    )

    print(f"Available labels: {dict(enumerate(labels))}")
    print(f"\n\nReasoning: {decision.reasoning}")
    print(f"\n\nApplied labels: {decision.labels}")

    return decision.labels
