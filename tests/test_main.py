from unittest.mock import Mock, patch
import pytest
from ai_labeler.github import (
    PullRequest,
    Label,
    get_available_labels,
    apply_labels,
)
from ai_labeler.ai import labeling_workflow


@pytest.fixture
def mock_github():
    mock = Mock()
    # Mock repository and labels
    mock_repo = Mock()
    mock_repo.get_labels.return_value = [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
    ]
    mock.get_repo.return_value = mock_repo
    return mock


def test_get_available_labels(mock_github):
    with patch.dict("os.environ", {"GITHUB_REPOSITORY": "owner/repo"}):
        labels = get_available_labels(mock_github)
        assert len(labels) == 2
        assert labels[0].name == "bug"
        assert labels[0].description == "Something isn't working"


def test_labeling_workflow():
    # Sample PR
    pr = PullRequest(
        title="Fix database connection bug",
        body="The database connection keeps timing out",
        changed_files=["src/database.py"],
    )

    # Available labels
    labels = [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
    ]

    # Run workflow
    result = labeling_workflow(pr, labels)

    # The AI should choose 'bug' based on the PR content
    assert "bug" in result


def test_apply_labels_dry_run(mock_github, capsys):
    with patch.dict(
        "os.environ",
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_EVENT_NUMBER": "123",
            "INPUT_DRY-RUN": "true",
        },
    ):
        apply_labels(mock_github, ["bug", "enhancement"])
        captured = capsys.readouterr()
        assert "Dry run: Would apply labels" in captured.out


def test_apply_labels_real(mock_github):
    with patch.dict(
        "os.environ",
        {
            "GITHUB_REPOSITORY": "owner/repo",
            "GITHUB_EVENT_NUMBER": "123",
            "INPUT_DRY-RUN": "false",
        },
    ):
        mock_issue = Mock()
        mock_github.get_repo().get_issue.return_value = mock_issue

        apply_labels(mock_github, ["bug", "enhancement"])

        mock_issue.add_to_labels.assert_called_once_with("bug", "enhancement")
