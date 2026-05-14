from types import SimpleNamespace

from app.config import Settings
from app.llm_client import LLMClient


class FakeResponses:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_text='{"confidence":1,"missing_fields":[]}')


class FakeOpenAI:
    instances: list["FakeOpenAI"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.responses = FakeResponses()
        self.instances.append(self)


def test_extract_json_uses_responses_api(monkeypatch) -> None:
    FakeOpenAI.instances = []
    monkeypatch.setattr("app.llm_client.OpenAI", FakeOpenAI)

    client = LLMClient(
        Settings(
            openai_api_key="test-key",
            openai_base_url=None,
            model_name="gpt-4o-mini",
        )
    )
    result = client.extract_json("Extract JSON.", "Invoice text")

    fake_client = FakeOpenAI.instances[0]
    call = fake_client.responses.calls[0]
    assert result == '{"confidence":1,"missing_fields":[]}'
    assert fake_client.kwargs == {"api_key": "test-key", "timeout": 20.0}
    assert call["model"] == "gpt-4o-mini"
    assert call["instructions"] == "Extract JSON."
    assert call["input"][0]["content"][0] == {
        "type": "input_text",
        "text": "Extract the requested data and return one JSON object only.\n\nInvoice text",
    }
    assert call["store"] is True
    assert call["text"] == {"format": {"type": "json_object"}}


def test_extract_json_from_image_uses_responses_image_input(monkeypatch) -> None:
    FakeOpenAI.instances = []
    monkeypatch.setattr("app.llm_client.OpenAI", FakeOpenAI)

    client = LLMClient(Settings(openai_api_key="test-key", openai_base_url=None))
    client.extract_json_from_image("Extract invoice JSON.", b"image-bytes", "image/png")

    fake_client = FakeOpenAI.instances[0]
    content = fake_client.responses.calls[0]["input"][0]["content"]
    assert content[0] == {
        "type": "input_text",
        "text": "Extract the invoice data from this invoice image and return one JSON object only.",
    }
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")


def test_client_passes_base_url_only_when_configured(monkeypatch) -> None:
    FakeOpenAI.instances = []
    monkeypatch.setattr("app.llm_client.OpenAI", FakeOpenAI)

    LLMClient(
        Settings(
            openai_api_key="test-key",
            openai_base_url="https://api.openai.com/v1",
        )
    )

    assert FakeOpenAI.instances[0].kwargs == {
        "api_key": "test-key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 20.0,
    }
