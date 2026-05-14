from pydantic import BaseModel, Field


class ExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw document text to extract from.")


class InvoiceExtraction(BaseModel):
    supplier_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    gst: float | None = None
    total: float | None = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    missing_fields: list[str] = Field(default_factory=list)


class JobDescriptionExtraction(BaseModel):
    title: str | None = None
    company: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    salary_range: str | None = None
