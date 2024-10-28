import os
import pytest
from unittest.mock import Mock, patch
import yaml

from ai_labeler.github import PullRequest, Issue, Label
from ai_labeler.ai import Config, LabelConfig, labeling_workflow


@pytest.fixture
def mock_github():
    mock = Mock()
    # Mock repository and labels
    mock_repo = Mock()
    mock_repo.get_labels.return_value = [
        Mock(name="bug", description="Something isn't working"),
        Mock(name="enhancement", description="New feature or request"),
    ]
    mock.get_repo.return_value = mock_repo
    return mock


@pytest.fixture
def sample_config_file(tmp_path):
    """Create a sample config file for testing"""
    config_content = {
        "instructions": "Test instructions",
        "include_repo_labels": True,
        "labels": [
            "simple-label",
            {
                "complex-label": {
                    "description": "A complex label",
                    "instructions": "Apply when needed",
                }
            },
            {"null-props": None},  # Test null properties
        ],
        "context_files": ["CONTRIBUTING.md"],
    }

    config_path = tmp_path / "ai-labeler.yml"
    with open(config_path, "w") as f:
        yaml.dump(config_content, f)

    return config_path


def test_config_loading(sample_config_file):
    """Test loading configuration from YAML file"""
    with patch.dict(
        os.environ,
        {
            "GITHUB_WORKSPACE": str(sample_config_file.parent),
            "INPUT_CONFIG-PATH": sample_config_file.name,
        },
    ):
        config = Config.load()

        assert config.instructions == "Test instructions"
        assert config.include_repo_labels is True
        assert len(config.labels) == 3

        # Check simple label
        assert config.labels[0].name == "simple-label"
        assert config.labels[0].description is None

        # Check complex label
        assert config.labels[1].name == "complex-label"
        assert config.labels[1].description == "A complex label"
        assert config.labels[1].instructions == "Apply when needed"

        # Check null properties
        assert config.labels[2].name == "null-props"
        assert config.labels[2].description is None


def test_config_loading_no_file():
    """Test loading with missing config file"""
    with patch.dict(
        os.environ,
        {"GITHUB_WORKSPACE": "/nonexistent", "INPUT_CONFIG-PATH": "nonexistent.yml"},
    ):
        config = Config.load()
        assert config.instructions == ""
        assert config.include_repo_labels is True
        assert len(config.labels) == 0


def test_context_file_loading(tmp_path):
    """Test loading context files"""
    # Create a test context file
    context_file = tmp_path / "CONTRIBUTING.md"
    context_file.write_text("Test contributing guidelines")

    config = Config(
        instructions="",
        include_repo_labels=True,
        labels=[],
        context_files=["CONTRIBUTING.md"],
    )

    with patch.dict(os.environ, {"GITHUB_WORKSPACE": str(tmp_path)}):
        context = config.load_context_files()
        assert "CONTRIBUTING.md" in context
        assert context["CONTRIBUTING.md"] == "Test contributing guidelines"


def test_context_file_missing(tmp_path):
    """Test handling of missing context files"""
    config = Config(
        instructions="",
        include_repo_labels=True,
        labels=[],
        context_files=["NONEXISTENT.md"],
    )

    with patch.dict(os.environ, {"GITHUB_WORKSPACE": str(tmp_path)}):
        context = config.load_context_files()
        assert len(context) == 0


@pytest.mark.asyncio
async def test_labeling_workflow():
    """Test the complete labeling workflow"""
    # Sample PR
    pr = PullRequest(
        title="Fix database connection bug",
        body="The database connection keeps timing out",
        changed_files=[{"filename": "src/database.py", "status": "modified"}],
        author="test-user",
    )

    # Available labels
    labels = [
        Label(name="bug", description="Something isn't working"),
        Label(name="enhancement", description="New feature or request"),
    ]

    # Mock config
    mock_config = Config(
        instructions="Test instructions",
        include_repo_labels=True,
        labels=[],
        context_files=[],
    )

    with patch("ai_labeler.ai.Config.load", return_value=mock_config):
        result = await labeling_workflow(pr, labels)

        # The AI should choose 'bug' based on the PR content
        assert isinstance(result, list)
        assert all(isinstance(label, str) for label in result)
        assert "bug" in result


@pytest.mark.asyncio
async def test_labeling_workflow_issue():
    """Test labeling workflow with an issue"""
    issue = Issue(
        title="Feature request: Add dark mode",
        body="Would be great to have a dark mode option",
        author="test-user",
    )

    labels = [
        Label(name="enhancement", description="New feature or request"),
        Label(name="ui", description="User interface changes"),
    ]

    mock_config = Config(
        instructions="Test instructions",
        include_repo_labels=True,
        labels=[],
        context_files=[],
    )

    with patch("ai_labeler.ai.Config.load", return_value=mock_config):
        result = await labeling_workflow(issue, labels)

        assert isinstance(result, list)
        assert all(isinstance(label, str) for label in result)
        assert "enhancement" in result


def test_label_config_creation():
    """Test LabelConfig creation and properties"""
    # Test simple label
    simple = LabelConfig(name="test")
    assert simple.name == "test"
    assert simple.description is None
    assert simple.instructions is None

    # Test full label
    full = LabelConfig(
        name="test", description="Test label", instructions="Apply when testing"
    )
    assert full.name == "test"
    assert full.description == "Test label"
    assert full.instructions == "Apply when testing"
