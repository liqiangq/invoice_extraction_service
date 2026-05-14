# ai-extraction-api

FastAPI service for extracting structured invoice and job-description data with OpenAI.

## Setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Set `OPENAI_API_KEY` in `.env`. Leave `OPENAI_BASE_URL` blank to use OpenAI directly.

```env
OPENAI_API_KEY=sk-your-api-key
OPENAI_BASE_URL=
MODEL_NAME=gpt-4o-mini
OPENAI_STORE_RESPONSES=true
PYTHON_VERSION=3.11
```

For OpenRouter, use:

```env
OPENAI_API_KEY=your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=openai/gpt-4o-mini
PYTHON_VERSION=3.11
```

The service uses the OpenAI Responses API:

```bash
curl https://api.openai.com/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "input": "write a haiku about ai",
    "store": true
  }'
```

## Run

```bash
.venv/bin/python -m uvicorn app.main:app --reload
```

Open the upload page:

```text
http://127.0.0.1:8000/
```

If port `8000` is busy, use another port:

```bash
.venv/bin/python -m uvicorn app.main:app --reload --port 8001
```

Then open:

```text
http://127.0.0.1:8001/
```

## Test

```bash
.venv/bin/python -m pytest
```

## Data

Use `data/invoices/<language>/` for local invoice samples in different languages, for example `data/invoices/es/`, `data/invoices/zh/`, or `data/invoices/mandarin/`.

Real invoices are ignored by git by default. Commit only anonymized fixtures under `tests/fixtures/` if you need repeatable test data.

## Extract Invoice (text or photo)

`POST /extract/invoice` accepts a `multipart/form-data` request with **exactly one** of:

- `text` — invoice text pasted as a form field, or
- `file` — an invoice photo (PNG, JPEG, or WebP).

```bash
# From pasted text
curl -X POST http://127.0.0.1:8000/extract/invoice \
  -F 'text=Acme Ltd Invoice #INV-001 Total $115.00 NZD ...'

# From a photo
curl -X POST http://127.0.0.1:8000/extract/invoice \
  -F 'file=@data/invoices/mandarin/mandarin-synth_0049.png;type=image/png'
```

Sending both fields, or neither, returns HTTP 422.

### Legacy / alias endpoints

These remain available for backwards compatibility:

- `POST /extract/invoice/text` — JSON body `{"text": "..."}`.
- `POST /extract/invoice-image` — multipart upload with `file=` only.

Both delegate to the same extraction code as `/extract/invoice`.

## Batch CLI

You can also extract directly from the command line without starting the server. Pass image files/directories, or use `--text` / `--text-file` for raw invoice text:

```bash
# Photos
.venv/bin/python -m scripts.extract_invoice_cli data/invoices/mandarin/mandarin-synth_0049.png
.venv/bin/python -m scripts.extract_invoice_cli data/invoices/spanish --limit 5
.venv/bin/python -m scripts.extract_invoice_cli data/invoices/arabic data/invoices/german --output out/results.json

# Text
.venv/bin/python -m scripts.extract_invoice_cli --text "Acme Ltd Invoice INV-001 Total NZD 115.00"
.venv/bin/python -m scripts.extract_invoice_cli --text-file invoice.txt
```

Each invoice is sent to the configured `MODEL_NAME`, and the parsed JSON for every invoice is printed to stdout. A combined JSON array is written to `results.json` by default; use `--output` to change the path or `--no-save` to skip writing the file.
