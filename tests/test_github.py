import pytest
from unittest.mock import Mock
from github import Github
from ai_labeler.github import (
    Label,
    get_available_labels_from_config,
    _label_cache,
)
from ai_labeler.config_parser import Config, LabelConfig


@pytest.fixture(autouse=True)
def clear_label_cache():
    """Clear the label cache before each test"""
    _label_cache.clear()
    yield


@pytest.fixture
def mock_github():
    mock_gh = Mock(spec=Github)
    mock_repo = Mock()
    mock_gh.get_repo.return_value = mock_repo

    # Mock existing labels
    mock_repo.get_labels.return_value = [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
        Label(name="documentation", description="Docs update"),
    ]

    return mock_gh, mock_repo


def test_get_labels_basic_config(mock_github):
    gh_client, repo = mock_github

    config = Config(
        labels=[
            LabelConfig(name="bug", description="Updated bug description"),
            LabelConfig(
                name="security",
                description="Security-related changes",
                instructions="Apply for security fixes",
            ),
        ],
    )

    labels = get_available_labels_from_config(
        gh_client, config, include_repo_labels=True
    )

    # Should include both config and repo labels
    assert len(labels) == 4  # 3 repo labels + 1 new from config

    # Check existing label was updated
    bug_label = next(l for l in labels if l.name == "bug")
    assert bug_label.description == "Updated bug description"

    # Check new label was created
    repo.create_label.assert_called_once_with(
        name="security",
        description="Security-related changes",
        color="ededed",
    )


def test_get_labels_config_only(mock_github):
    gh_client, repo = mock_github

    config = Config(
        instructions="Use only config-defined labels",
        labels=[
            LabelConfig(name="frontend", description="Frontend changes"),
            LabelConfig(name="backend", description="Backend changes"),
        ],
    )

    labels = get_available_labels_from_config(
        gh_client, config, include_repo_labels=False
    )

    # Should only include config labels
    assert len(labels) == 2
    assert {l.name for l in labels} == {"frontend", "backend"}

    # Both labels should be created
    assert repo.create_label.call_count == 2


def test_get_labels_with_instructions(mock_github):
    gh_client, repo = mock_github

    config = Config(
        instructions="Apply labels based on their instructions",
        labels=[
            LabelConfig(
                name="bug",
                description="A bug that needs fixing",
                instructions="Only apply with clear reproduction steps",
            ),
            LabelConfig(
                name="enhancement",
                description="Config description",
                instructions="Apply for new features",
            ),
        ],
    )

    labels = get_available_labels_from_config(
        gh_client, config, include_repo_labels=True
    )

    # Check instructions were added
    bug_label = next(l for l in labels if l.name == "bug")
    assert bug_label.instructions == "Only apply with clear reproduction steps"

    enhancement_label = next(l for l in labels if l.name == "enhancement")
    assert enhancement_label.instructions == "Apply for new features"
    assert enhancement_label.description == "Config description"


def test_get_labels_empty_config(mock_github):
    gh_client, _ = mock_github

    config = Config(
        instructions="Use existing repo labels",
        labels=[],
    )

    labels = get_available_labels_from_config(
        gh_client, config, include_repo_labels=True
    )

    # Should return all repo labels unchanged
    assert len(labels) == 3
    assert {l.name for l in labels} == {"bug", "enhancement", "documentation"}


def test_get_labels_no_repo_labels(mock_github):
    gh_client, repo = mock_github

    # Mock empty repo
    repo.get_labels.return_value = []

    config = Config(
        instructions="Create new labels if needed",
        labels=[
            LabelConfig(name="test", description="Test label"),
        ],
    )

    labels = get_available_labels_from_config(
        gh_client, config, include_repo_labels=True
    )

    assert len(labels) == 1
    assert labels[0].name == "test"
    assert labels[0].description == "Test label"
