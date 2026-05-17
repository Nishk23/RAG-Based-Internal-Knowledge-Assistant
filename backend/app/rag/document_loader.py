from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    pass


def extract_text_from_upload(upload_file: UploadFile) -> str:
    filename = upload_file.filename or "uploaded_file"
    suffix = Path(filename).suffix.lower()

    raw_bytes = upload_file.file.read()
    if not raw_bytes:
        return ""

    if suffix in {".txt", ".md"}:
        return raw_bytes.decode("utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(BytesIO(raw_bytes))
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
        return "\n".join(pages)

    raise UnsupportedFileTypeError(
        "Unsupported file type. Only .txt, .md, and .pdf are accepted."
    )
