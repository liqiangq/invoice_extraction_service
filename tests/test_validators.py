from fastapi import HTTPException

from app.models import InvoiceExtraction
from app.validators import parse_llm_json


def test_parse_llm_json_returns_model_for_valid_invoice() -> None:
    result = parse_llm_json(
        """
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
        """,
        InvoiceExtraction,
    )

    assert result.invoice_number == "INV-001"
    assert result.total == 115.0


def test_parse_llm_json_raises_422_for_invalid_json() -> None:
    try:
        parse_llm_json("not json", InvoiceExtraction)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert "invalid JSON" in exc.detail
    else:
        raise AssertionError("Expected HTTPException")


def test_parse_llm_json_raises_422_for_schema_mismatch() -> None:
    try:
        parse_llm_json('{"confidence": 2}', InvoiceExtraction)
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["message"] == "LLM returned JSON that does not match the expected schema."
    else:
        raise AssertionError("Expected HTTPException")
