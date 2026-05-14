from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse

from app.llm_client import LLMClient
from app.models import ExtractionRequest, InvoiceExtraction, JobDescriptionExtraction
from app.prompts import INVOICE_EXTRACTION_PROMPT, JOB_DESCRIPTION_EXTRACTION_PROMPT
from app.validators import parse_llm_json


app = FastAPI(title="AI Extraction API")

SUPPORTED_INVOICE_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


async def _extract_invoice_from_text_or_image(
    text: str | None,
    file: UploadFile | None,
) -> InvoiceExtraction:
    text_value = (text or "").strip()
    has_text = bool(text_value)
    has_file = file is not None and (file.filename or "").strip() != ""

    if has_text and has_file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide either text or an invoice image, not both.",
        )
    if not has_text and not has_file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Provide invoice text or an invoice image.",
        )

    client = LLMClient()
    if has_text:
        raw_content = client.extract_json(INVOICE_EXTRACTION_PROMPT, text_value)
    else:
        assert file is not None  # narrow for type-checkers
        if file.content_type not in SUPPORTED_INVOICE_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invoice image must be PNG, JPEG, or WebP.",
            )
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invoice image is empty.",
            )
        raw_content = client.extract_json_from_image(
            INVOICE_EXTRACTION_PROMPT,
            image_bytes,
            file.content_type,
        )

    return parse_llm_json(raw_content, InvoiceExtraction)


INDEX_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Invoice Extraction</title>
    <style>
      :root {
        color-scheme: light;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #16202a;
        background: #f6f7fb;
      }
      body {
        margin: 0;
        min-height: 100vh;
        background:
          linear-gradient(180deg, rgba(31, 95, 127, 0.12), rgba(246, 247, 251, 0) 320px),
          #f6f7fb;
      }
      main {
        max-width: 1120px;
        margin: 0 auto;
        padding: 40px 24px;
      }
      h1 {
        font-size: 42px;
        line-height: 1.05;
        margin: 0;
        max-width: 760px;
      }
      h2 {
        font-size: 18px;
        margin: 0 0 12px;
      }
      p {
        margin: 0;
      }
      .intro {
        margin-bottom: 28px;
      }
      .eyebrow {
        color: #0f766e;
        font-size: 13px;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-bottom: 10px;
        text-transform: uppercase;
      }
      .summary {
        color: #405366;
        font-size: 17px;
        line-height: 1.55;
        margin-top: 14px;
        max-width: 860px;
      }
      .goal {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        border-left: 5px solid #ea580c;
        border-radius: 8px;
        color: #7c2d12;
        font-size: 15px;
        line-height: 1.5;
        margin-top: 18px;
        padding: 14px 16px;
      }
      .popular {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 18px;
      }
      .popular span {
        background: #e6f4f1;
        border: 1px solid #b7dfd8;
        border-radius: 999px;
        color: #115e59;
        font-size: 13px;
        font-weight: 700;
        padding: 7px 10px;
      }
      .frames {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 20px;
      }
      @media (max-width: 720px) {
        .frames {
          grid-template-columns: 1fr;
        }
      }
      .card,
      pre {
        background: #ffffff;
        border: 1px solid #d8e0ea;
        border-radius: 8px;
        box-shadow: 0 12px 36px rgba(22, 32, 42, 0.08);
        padding: 22px;
      }
      .card form {
        display: flex;
        flex-direction: column;
      }
      .hint {
        color: #5d6f82;
        font-size: 13px;
        line-height: 1.45;
        margin: 0 0 14px;
      }
      label {
        display: block;
        font-weight: 700;
        margin-bottom: 8px;
      }
      input,
      textarea {
        width: 100%;
        box-sizing: border-box;
        border: 1px solid #c9d1dc;
        border-radius: 6px;
        padding: 12px;
        background: #ffffff;
        font-family: inherit;
        font-size: 14px;
      }
      input:focus,
      textarea:focus {
        border-color: #0f766e;
        box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.14);
        outline: 0;
      }
      textarea {
        min-height: 200px;
        resize: vertical;
      }
      .formats {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin: 10px 0 0;
      }
      .format-chip {
        background: #eef2f7;
        border: 1px solid #d9dee5;
        color: #17202a;
        font-size: 12px;
        font-weight: 700;
        padding: 4px 8px;
        border-radius: 999px;
      }
      button {
        margin-top: 16px;
        border: 0;
        border-radius: 6px;
        padding: 11px 15px;
        background: #0f766e;
        color: #ffffff;
        font-weight: 700;
        cursor: pointer;
        align-self: flex-start;
      }
      button:hover {
        background: #115e59;
      }
      button:disabled {
        background: #6b7280;
        cursor: wait;
      }
      .result-section {
        margin-top: 24px;
      }
      pre {
        color: #10202f;
        font-size: 14px;
        line-height: 1.45;
        min-height: 180px;
        overflow: auto;
        white-space: pre-wrap;
      }
    </style>
  </head>
  <body>
    <main>
      <section class="intro">
        <p class="eyebrow">AI Extraction API</p>
        <h1>Invoice Extraction</h1>
        <p class="summary">FastAPI service for extracting structured invoice and job-description data with OpenAI.</p>
        <p class="goal"><strong>Goal:</strong> The project should accept unstructured text, call an LLM, and return structured JSON.</p>
        <div class="popular" aria-label="Popular extraction use cases">
          <span>Invoice photos</span>
          <span>Raw invoice text</span>
          <span>Supplier details</span>
          <span>Totals and tax</span>
          <span>Structured JSON</span>
        </div>
      </section>
      <div class="frames">
        <section class="card">
          <h2>Invoice text</h2>
          <p class="hint">Paste unstructured invoice text and return clean JSON fields.</p>
          <form id="text-form">
            <label for="invoice-text">Text</label>
            <textarea id="invoice-text" name="text" placeholder="Paste invoice text here..."></textarea>
            <button id="text-button" type="submit">Extract from text</button>
          </form>
        </section>
        <section class="card">
          <h2>Invoice photo</h2>
          <p class="hint">Upload a photo or scan and extract supplier, invoice number, dates, currency, totals, and confidence.</p>
          <div class="formats">
            <span class="format-chip">PNG</span>
            <span class="format-chip">JPEG / JPG</span>
            <span class="format-chip">WebP</span>
          </div>
          <form id="image-form" style="margin-top: 16px;">
            <label for="invoice-file">File</label>
            <input id="invoice-file" name="file" type="file" accept="image/png,image/jpeg,image/webp">
            <button id="image-button" type="submit">Extract from photo</button>
          </form>
        </section>
      </div>
      <section class="result-section">
        <h2>Structured JSON result</h2>
        <pre id="result">No result yet. Submit text or a photo to extract invoice data.</pre>
      </section>
    </main>
    <script>
      const result = document.getElementById("result");

      const textForm = document.getElementById("text-form");
      const textButton = document.getElementById("text-button");
      const textInput = document.getElementById("invoice-text");

      const imageForm = document.getElementById("image-form");
      const imageButton = document.getElementById("image-button");
      const fileInput = document.getElementById("invoice-file");

      async function postExtraction(formData, button) {
        button.disabled = true;
        result.textContent = "Extracting...";
        try {
          const response = await fetch("/extract/invoice", {
            method: "POST",
            body: formData,
          });
          const payload = await response.json();
          result.textContent = JSON.stringify(payload, null, 2);
        } catch (error) {
          result.textContent = String(error);
        } finally {
          button.disabled = false;
        }
      }

      textForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = textInput.value.trim();
        if (!text) {
          result.textContent = "Please paste invoice text.";
          return;
        }
        const formData = new FormData();
        formData.append("text", text);
        await postExtraction(formData, textButton);
      });

      imageForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (fileInput.files.length === 0) {
          result.textContent = "Please choose an invoice image.";
          return;
        }
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        await postExtraction(formData, imageButton);
      });
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract/invoice", response_model=InvoiceExtraction)
async def extract_invoice(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
) -> InvoiceExtraction:
    """Extract invoice data from either pasted text or an uploaded image.

    Send a multipart/form-data request with exactly one of:
      - ``text`` form field containing the invoice text, or
      - ``file`` upload containing a PNG, JPEG, or WebP photo.
    """
    return await _extract_invoice_from_text_or_image(text, file)


@app.post("/extract/invoice/text", response_model=InvoiceExtraction)
def extract_invoice_text(payload: ExtractionRequest) -> InvoiceExtraction:
    """JSON variant: ``{"text": "..."}``. Kept for clients that prefer JSON bodies."""
    raw_content = LLMClient().extract_json(INVOICE_EXTRACTION_PROMPT, payload.text)
    return parse_llm_json(raw_content, InvoiceExtraction)


@app.post("/extract/invoice-image", response_model=InvoiceExtraction)
async def extract_invoice_image(file: UploadFile = File(...)) -> InvoiceExtraction:
    """Backwards-compatible alias that only accepts an image upload."""
    return await _extract_invoice_from_text_or_image(text=None, file=file)


@app.post("/extract/job-description", response_model=JobDescriptionExtraction)
def extract_job_description(payload: ExtractionRequest) -> JobDescriptionExtraction:
    raw_content = LLMClient().extract_json(JOB_DESCRIPTION_EXTRACTION_PROMPT, payload.text)
    return parse_llm_json(raw_content, JobDescriptionExtraction)
