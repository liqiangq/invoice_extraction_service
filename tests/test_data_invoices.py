from pathlib import Path

import pytest


MANDARIN_INVOICE_DIR = Path("data/invoices/mandarin")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def detect_image_format(path: Path) -> str | None:
    with path.open("rb") as file:
        header = file.read(16)

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    return None


def mandarin_invoice_files() -> list[Path]:
    return sorted(
        path
        for path in MANDARIN_INVOICE_DIR.iterdir()
        if path.is_file() and path.name != ".gitkeep"
    )


def test_mandarin_invoice_folder_exists() -> None:
    assert MANDARIN_INVOICE_DIR.is_dir()


def test_mandarin_invoice_folder_contains_local_samples() -> None:
    files = mandarin_invoice_files()

    if not files:
        pytest.skip("No local Mandarin invoice samples found.")

    assert len(files) >= 1


@pytest.mark.parametrize("path", mandarin_invoice_files())
def test_mandarin_invoice_files_use_supported_extensions(path: Path) -> None:
    assert path.suffix.lower() in SUPPORTED_EXTENSIONS


@pytest.mark.parametrize("path", mandarin_invoice_files())
def test_mandarin_invoice_files_have_readable_image_headers(path: Path) -> None:
    image_format = detect_image_format(path)

    assert image_format in {"png", "jpeg", "webp"}
