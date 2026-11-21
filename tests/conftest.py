import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.pop("AI_API_KEY", None)


@pytest.fixture(autouse=True)
def force_demo_mode(monkeypatch):
    """Tests must never call the live API, even if secrets.toml has a key."""
    from services import ai_client
    monkeypatch.setattr(ai_client, "is_mock_mode", lambda: True)