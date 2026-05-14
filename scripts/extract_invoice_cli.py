"""Command-line runner for invoice extraction (text or photo).

Examples:
    # From an image file or directory
    .venv/bin/python -m scripts.extract_invoice_cli data/invoices/mandarin/mandarin-synth_0049.png
    .venv/bin/python -m scripts.extract_invoice_cli data/invoices/spanish --limit 5

    # From pasted text
    .venv/bin/python -m scripts.extract_invoice_cli --text "Acme Ltd INV-001 Total $115 NZD"

    # From text in a file
    .venv/bin/python -m scripts.extract_invoice_cli --text-file invoice.txt

Each invoice is sent to the configured LLM (see .env -> MODEL_NAME) and the
parsed InvoiceExtraction JSON is printed to stdout. A combined JSON array is
written to results.json by default; pass --output to change the path or
--no-save to skip writing the file.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path
from typing import Iterable

from app.llm_client import LLMClient
from app.models import InvoiceExtraction
from app.prompts import INVOICE_EXTRACTION_PROMPT
from app.validators import parse_llm_json


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
EXT_TO_MEDIA_TYPE = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def collect_image_paths(inputs: Iterable[str], limit: int | None) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            for child in sorted(path.iterdir()):
                if child.is_file() and child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    paths.append(child)
        elif path.is_file():
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                paths.append(path)
            else:
                print(f"[skip] unsupported extension: {path}", file=sys.stderr)
        else:
            print(f"[skip] not found: {path}", file=sys.stderr)
    if limit is not None:
        paths = paths[:limit]
    return paths


def media_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in EXT_TO_MEDIA_TYPE:
        return EXT_TO_MEDIA_TYPE[suffix]
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def extract_one_image(client: LLMClient, path: Path) -> dict:
    media_type = media_type_for(path)
    image_bytes = path.read_bytes()
    started = time.perf_counter()
    raw = client.extract_json_from_image(
        INVOICE_EXTRACTION_PROMPT,
        image_bytes,
        media_type,
    )
    parsed: InvoiceExtraction = parse_llm_json(raw, InvoiceExtraction)
    elapsed = time.perf_counter() - started
    return {
        "file": str(path),
        "media_type": media_type,
        "elapsed_seconds": round(elapsed, 2),
        "extraction": parsed.model_dump(),
    }


def extract_one_text(client: LLMClient, text: str, source: str) -> dict:
    started = time.perf_counter()
    raw = client.extract_json(INVOICE_EXTRACTION_PROMPT, text)
    parsed: InvoiceExtraction = parse_llm_json(raw, InvoiceExtraction)
    elapsed = time.perf_counter() - started
    return {
        "source": source,
        "elapsed_seconds": round(elapsed, 2),
        "extraction": parsed.model_dump(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured invoice data from text or images using the LLM.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Image files or directories of invoice images to process.",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Pasted invoice text to extract from (mutually exclusive with image inputs).",
    )
    parser.add_argument(
        "--text-file",
        default=None,
        help="Path to a text file containing invoice text.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to process (after expansion).",
    )
    parser.add_argument(
        "--output",
        default="results.json",
        help="Path to write the combined JSON results (default: results.json).",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write the combined results file.",
    )
    args = parser.parse_args()

    text_value: str | None = None
    text_source: str | None = None
    if args.text:
        text_value = args.text
        text_source = "--text"
    elif args.text_file:
        text_path = Path(args.text_file)
        if not text_path.is_file():
            print(f"text-file not found: {text_path}", file=sys.stderr)
            return 1
        text_value = text_path.read_text(encoding="utf-8")
        text_source = str(text_path)

    if text_value and args.inputs:
        print("Provide either text input or image inputs, not both.", file=sys.stderr)
        return 1
    if not text_value and not args.inputs:
        print("No inputs. Pass image paths, --text, or --text-file.", file=sys.stderr)
        return 1

    client = LLMClient()
    results: list[dict] = []

    if text_value:
        try:
            result = extract_one_text(client, text_value, text_source or "text")
        except Exception as exc:  # noqa: BLE001
            result = {"source": text_source, "error": f"{exc.__class__.__name__}: {exc}"}
            print(f"ERROR: {result['error']}", file=sys.stderr)
        else:
            print(json.dumps(result["extraction"], ensure_ascii=False, indent=2))
        results.append(result)
    else:
        paths = collect_image_paths(args.inputs, args.limit)
        if not paths:
            print("No images to process.", file=sys.stderr)
            return 1
        for index, path in enumerate(paths, start=1):
            print(f"[{index}/{len(paths)}] {path}", file=sys.stderr)
            try:
                result = extract_one_image(client, path)
            except Exception as exc:  # noqa: BLE001 - surface every failure
                result = {"file": str(path), "error": f"{exc.__class__.__name__}: {exc}"}
                print(f"  -> ERROR: {result['error']}", file=sys.stderr)
            else:
                print(json.dumps(result["extraction"], ensure_ascii=False, indent=2))
            results.append(result)

    if not args.no_save:
        Path(args.output).write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nWrote {len(results)} results to {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
