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
    def validate_labels(result: list[str]):
        if any(label not in [l.name for l in labels] for label in result):
            raise ValueError(
                f"Invalid labels. Must be one of {', '.join(f"{l.name}" for l in labels)}"
            )
        return result

    # Create an agent specialized in GitHub labeling
    labeler = cf.Agent(
        name="GitHub Labeler",
        instructions="""
        You are an expert AI that automatically labelling GitHub issues and pull
        requests. You always pay close attention to label instructions.
        """,
        model=llm_model or "openai/gpt-4o-mini",
    )

    class Reasoning(BaseModel):
        label_name: str
        # reasoning: str
        should_apply: bool

    reasoning = cf.run(
        """
        Consider the provided PR/issue, its context, and any provided
        instructions. Examine each available label carefully. Your job is to
        choose which labels to apply to the PR/issue.

        Each label has a name, optional description, and optional instructions.
        Treat all three as inputs for understanding whether the label is
        relevant. Evaluate each label independently.

        For labels that may be appropriate, provide a complete rationale of
        whether you would assign them to the PR/issue, taking your instructions
        and the label's instructions into account. Some labels will have
        specific instructions about when to apply them, or whether to apply them
        at all. Be sure to reference all relevant context and instructions in
        your reasoning. 
        
        You do not need to return reasoning about labels that are obviously
        irrelevant.
        """,
        instructions=instructions,
        result_type=list[Reasoning],
        context={
            "pr_or_issue_to_label": item,
            "available_labels": dict(enumerate(labels)),
            "additional_context": context_files,
            "labeling_instructions": instructions,
        },
        agents=[labeler],
        completion_tools=["SUCCEED"],  # the task can not be marked as failed
        model_kwargs=dict(tool_choice="required"),  # prevent chatting
    )

    decision = [r.label_name for r in reasoning if r.should_apply]

    # --- old two-step approach. Adding `should_apply` to the reasoning model
    # appears to match performance in a single step.
    #
    # decision = cf.run(
    #     """
    #     Based on the reasoning for each label, return the list of labels that
    #     should be applied. If no labels apply, return an empty list.
    #     """,
    #     result_type=list[str],
    #     result_validator=validate_labels,
    #     context={"reasoning": reasoning, "available_labels": labels},
    #     agents=[labeler],
    #     completion_tools=["SUCCEED"],  # the task can not be marked as failed
    #     model_kwargs=dict(tool_choice="required"),  # prevent chatting
    # )

    print(f"Available labels: {dict(enumerate(labels))}")
    print(f"\n\nReasoning: {reasoning}")
    print(f"\n\nApplied labels: {decision}")

    return decision
