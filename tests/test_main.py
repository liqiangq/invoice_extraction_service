from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


VALID_INVOICE_JSON = """
{
  "supplier_name": "Acme Ltd",
  "invoice_number": "INV-001",
  "invoice_date": "2026-05-01",
  "due_date": "2026-05-15",
  "currency": "NZD",
  "subtotal": 100.0,
  "gst": 15.0,
  "total": 115.0,
  "confidence": 0.98,
  "missing_fields": []
}
"""


class ValidInvoiceLLMClient:
    def extract_json(self, system_prompt: str, document_text: str) -> str:
        return VALID_INVOICE_JSON

    def extract_json_from_image(self, system_prompt: str, image_bytes: bytes, media_type: str) -> str:
        assert image_bytes
        assert media_type == "image/png"
        return VALID_INVOICE_JSON


class InvalidJsonLLMClient:
    def extract_json(self, system_prompt: str, document_text: str) -> str:
        return "not json"

    def extract_json_from_image(self, system_prompt: str, image_bytes: bytes, media_type: str) -> str:
        return "not json"


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_serves_upload_page() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Invoice Extraction" in response.text
    assert "/extract/invoice" in response.text


def test_extract_invoice_accepts_text_form_field(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", ValidInvoiceLLMClient)

    response = client.post("/extract/invoice", data={"text": "Invoice text"})

    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-001"


def test_extract_invoice_accepts_image_upload(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", ValidInvoiceLLMClient)

    invoice_path = "data/invoices/mandarin/mandarin_synth_0049.png"
    with open(invoice_path, "rb") as invoice_file:
        response = client.post(
            "/extract/invoice",
            files={"file": ("mandarin_synth_0049.png", invoice_file, "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-001"


def test_extract_invoice_rejects_both_text_and_image(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", ValidInvoiceLLMClient)

    invoice_path = "data/invoices/mandarin/mandarin_synth_0049.png"
    with open(invoice_path, "rb") as invoice_file:
        response = client.post(
            "/extract/invoice",
            data={"text": "Invoice text"},
            files={"file": ("mandarin_synth_0049.png", invoice_file, "image/png")},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "Provide either text or an invoice image, not both."


def test_extract_invoice_rejects_neither_text_nor_image() -> None:
    response = client.post("/extract/invoice", data={})

    assert response.status_code == 422
    assert response.json()["detail"] == "Provide invoice text or an invoice image."


def test_extract_invoice_rejects_non_image_upload() -> None:
    response = client.post(
        "/extract/invoice",
        files={"file": ("invoice.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invoice image must be PNG, JPEG, or WebP."


def test_extract_invoice_returns_422_for_invalid_llm_json(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", InvalidJsonLLMClient)

    response = client.post("/extract/invoice", data={"text": "Invoice text"})

    assert response.status_code == 422
    assert "LLM returned invalid JSON" in response.json()["detail"]


def test_extract_invoice_text_json_endpoint_still_works(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", ValidInvoiceLLMClient)

    response = client.post("/extract/invoice/text", json={"text": "Invoice text"})

    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-001"


def test_extract_invoice_text_endpoint_requires_text_payload() -> None:
    response = client.post(
        "/extract/invoice/text",
        json={"file_path": "data/invoices/mandarin/mandarin_synth_0049.png"},
    )

    assert response.status_code == 422


def test_extract_invoice_image_alias_still_works(monkeypatch) -> None:
    monkeypatch.setattr("app.main.LLMClient", ValidInvoiceLLMClient)

    invoice_path = "data/invoices/mandarin/mandarin_synth_0049.png"
    with open(invoice_path, "rb") as invoice_file:
        response = client.post(
            "/extract/invoice-image",
            files={"file": ("mandarin_synth_0049.png", invoice_file, "image/png")},
        )

    assert response.status_code == 200
    assert response.json()["invoice_number"] == "INV-001"


def test_extract_invoice_image_alias_rejects_non_image_upload() -> None:
    response = client.post(
        "/extract/invoice-image",
        files={"file": ("invoice.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invoice image must be PNG, JPEG, or WebP."
