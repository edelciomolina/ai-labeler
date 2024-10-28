import pytest
from ai_labeler.ai import labeling_workflow
from ai_labeler.github import PullRequest, Issue, Label


@pytest.fixture
def sample_labels():
    return [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
        Label(name="documentation", description="Documentation updates"),
    ]


@pytest.fixture
def sample_pr():
    return PullRequest(
        title="Fix database connection timeout",
        body="This PR fixes a critical bug where database connections would timeout after 30 seconds.",
        files={"src/database.py": "content here"},
        author="marvin",
    )


@pytest.fixture
def sample_issue():
    return Issue(
        title="Add dark mode support",
        body="It would be great to have dark mode support for better accessibility.",
        author="marvin",
    )


def test_labeling_workflow_with_pr(sample_pr, sample_labels):
    result = labeling_workflow(
        item=sample_pr,
        labels=sample_labels,
    )

    assert isinstance(result, list)
    assert all(isinstance(label, str) for label in result)
    assert all(label in [l.name for l in sample_labels] for label in result)


def test_labeling_workflow_with_issue(sample_issue, sample_labels):
    result = labeling_workflow(
        item=sample_issue,
        labels=sample_labels,
    )

    assert isinstance(result, list)
    assert all(isinstance(label, str) for label in result)
    assert all(label in [l.name for l in sample_labels] for label in result)


def test_labeling_workflow_with_custom_instructions(sample_pr, sample_labels):
    custom_instructions = "Focus on security-related issues and bugs"
    result = labeling_workflow(
        item=sample_pr,
        labels=sample_labels,
        instructions=custom_instructions,
    )

    assert isinstance(result, list)
    assert all(isinstance(label, str) for label in result)


def test_labeling_workflow_with_context_files(sample_pr, sample_labels):
    context_files = {
        "README.md": "# Project Documentation\nThis is a test project.",
        "CONTRIBUTING.md": "Please follow the contribution guidelines.",
    }

    result = labeling_workflow(
        item=sample_pr,
        labels=sample_labels,
        context_files=context_files,
    )

    assert isinstance(result, list)
    assert all(isinstance(label, str) for label in result)


def test_labeling_workflow_empty_result(sample_pr, sample_labels):
    # Test case where no labels might be assigned
    result = labeling_workflow(
        item=PullRequest(
            title="Minor whitespace fix",
            body="Fixed some whitespace issues",
            files={},
            author="marvin",
        ),
        labels=sample_labels,
    )

    assert isinstance(result, list)
    # The workflow might return an empty list if no labels apply
    assert isinstance(result, list)
