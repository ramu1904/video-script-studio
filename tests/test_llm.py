from backend.config import get_settings
from backend.llm import get_groq_client


def test_settings_load_from_env():
    settings = get_settings()
    assert settings.groq_api_key.startswith("gsk_")
    assert settings.groq_model == "allam-2-7b"


def test_groq_client_can_be_created():
    client = get_groq_client()
    assert client is not None
