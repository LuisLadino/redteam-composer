"""Shared pytest fixtures for redteam-composer tests."""

import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_root(project_root):
    """Return the src directory."""
    return project_root / "src"


@pytest.fixture
def taxonomy_root(src_root):
    """Return the taxonomy directory."""
    return src_root / "redteam_composer" / "taxonomy"


@pytest.fixture
def strategies_root(taxonomy_root):
    """Return the strategies directory."""
    return taxonomy_root / "strategies"
