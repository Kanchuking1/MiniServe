"""
Pytest configuration and shared fixtures for MiniServe tests.
Run from repo root: pytest tests/ -v
"""

import sys
from pathlib import Path

import pytest

# Ensure repo root is on path so worker and api can be imported
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


@pytest.fixture
def sample_image():
    """A small RGB PIL image for testing (224x224)."""
    from PIL import Image
    return Image.new("RGB", (224, 224), color=(100, 150, 200))


@pytest.fixture(scope="module")
def loaded_model():
    """ResNet18 loaded once per test module (avoids repeated load in model tests)."""
    from worker.model import load_model
    return load_model("cpu")
