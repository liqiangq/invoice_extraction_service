from app.config import Settings


def test_settings_defaults_to_openai_model() -> None:
    settings = Settings(openai_api_key="test-key", openai_base_url=None)

    assert settings.openai_base_url is None
    assert settings.model_name == "gpt-4o-mini"
    assert settings.llm_store_responses is True


def test_settings_treats_blank_openai_base_url_as_default_endpoint() -> None:
    settings = Settings(openai_api_key="test-key", openai_base_url=" ")

    assert settings.openai_base_url is None


def test_settings_supports_openai_compatible_base_url() -> None:
    settings = Settings(
        openai_api_key="test-key",
        openai_base_url="https://openrouter.ai/api/v1",
        model_name="openai/gpt-4o-mini",
    )

    assert settings.openai_base_url == "https://openrouter.ai/api/v1"
    assert settings.model_name == "openai/gpt-4o-mini"
