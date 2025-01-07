import pytest
from macroeconomic_data.config import settings

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "FRED_SECRET_NAME", "test_fred_key")
    monkeypatch.setattr(settings, "AWS_REGION", "us-east-1") 