from __future__ import annotations

import re
import socket
import struct
from io import BytesIO
from pathlib import Path

from fastapi import UploadFile
from pypdf import PdfReader

from app.config import settings

ALLOWED_CONTENT_TYPES = {
    ".txt": {"text/plain", "application/octet-stream"},
    ".md": {"text/markdown", "text/plain", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
}


class UnsupportedFileTypeError(ValueError):
    pass


class UnsafeUploadError(ValueError):
    pass


class MalwareDetectedError(ValueError):
    pass


def sanitize_filename(filename: str | None) -> str:
    candidate = Path(filename or "uploaded_file").name
    candidate = re.sub(r"[\x00-\x1f\x7f]", "", candidate).strip()
    return candidate[:255] or "uploaded_file"


async def read_upload_bytes(upload_file: UploadFile) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while block := await upload_file.read(64 * 1024):
        total += len(block)
        if total > settings.max_upload_bytes:
            raise UnsafeUploadError(f"Upload exceeds the {settings.max_upload_bytes} byte limit.")
        chunks.append(block)
    return b"".join(chunks)


def validate_upload(filename: str, content_type: str, raw_bytes: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError("Only .txt, .md, and .pdf files are accepted.")
    if content_type not in ALLOWED_CONTENT_TYPES[suffix]:
        raise UnsupportedFileTypeError(
            "The declared content type does not match the file extension."
        )
    if suffix == ".pdf" and not raw_bytes.startswith(b"%PDF-"):
        raise UnsafeUploadError("Invalid PDF file signature.")
    if suffix in {".txt", ".md"} and b"\x00" in raw_bytes:
        raise UnsafeUploadError("Text uploads may not contain null bytes.")
    return suffix


def scan_for_malware(raw_bytes: bytes) -> None:
    if not settings.clamav_host:
        if settings.require_malware_scan:
            raise UnsafeUploadError("Malware scanning is required but unavailable.")
        return

    try:
        with socket.create_connection(
            (settings.clamav_host, settings.clamav_port), timeout=10
        ) as client:
            client.sendall(b"zINSTREAM\0")
            for offset in range(0, len(raw_bytes), 64 * 1024):
                block = raw_bytes[offset : offset + 64 * 1024]
                client.sendall(struct.pack("!I", len(block)) + block)
            client.sendall(struct.pack("!I", 0))
            response = client.recv(4096).decode("utf-8", errors="replace")
    except OSError as exc:
        if settings.require_malware_scan or settings.environment == "production":
            raise UnsafeUploadError("Malware scanner is unavailable.") from exc
        return

    if "FOUND" in response:
        raise MalwareDetectedError("The upload was rejected by malware scanning.")
    if "OK" not in response:
        raise UnsafeUploadError("Malware scanner returned an indeterminate result.")


def extract_text(raw_bytes: bytes, suffix: str) -> str:
    if not raw_bytes:
        return ""
    if suffix in {".txt", ".md"}:
        text = raw_bytes.decode("utf-8", errors="strict")
    else:
        try:
            reader = PdfReader(BytesIO(raw_bytes), strict=True)
        except Exception as exc:
            raise UnsafeUploadError("The PDF could not be parsed safely.") from exc
        if len(reader.pages) > settings.max_pdf_pages:
            raise UnsafeUploadError(f"PDF exceeds the {settings.max_pdf_pages} page limit.")
        pages: list[str] = []
        total_characters = 0
        for page in reader.pages:
            page_text = page.extract_text() or ""
            total_characters += len(page_text)
            if total_characters > settings.max_extracted_characters:
                raise UnsafeUploadError("Extracted document text exceeds the configured limit.")
            pages.append(page_text)
        text = "\n".join(pages)

    if len(text) > settings.max_extracted_characters:
        raise UnsafeUploadError("Extracted document text exceeds the configured limit.")
    return text


async def extract_text_from_upload(upload_file: UploadFile) -> tuple[str, str, bytes]:
    filename = sanitize_filename(upload_file.filename)
    raw_bytes = await read_upload_bytes(upload_file)
    content_type = upload_file.content_type or "application/octet-stream"
    suffix = validate_upload(filename, content_type, raw_bytes)
    scan_for_malware(raw_bytes)
    return filename, extract_text(raw_bytes, suffix), raw_bytes
