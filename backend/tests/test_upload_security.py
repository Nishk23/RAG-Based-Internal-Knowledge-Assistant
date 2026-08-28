import pytest

from app.rag.document_loader import (
    UnsafeUploadError,
    UnsupportedFileTypeError,
    extract_text,
    sanitize_filename,
    validate_upload,
)


def test_filename_is_reduced_to_safe_basename() -> None:
    assert sanitize_filename("../../secret/policy.md") == "policy.md"
    assert "\x00" not in sanitize_filename("bad\x00name.txt")


def test_upload_rejects_mismatched_type_and_signature() -> None:
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("policy.exe", "application/octet-stream", b"MZ")
    with pytest.raises(UnsupportedFileTypeError):
        validate_upload("policy.pdf", "text/plain", b"%PDF-1.7")
    with pytest.raises(UnsafeUploadError):
        validate_upload("policy.pdf", "application/pdf", b"not a pdf")


def test_text_upload_rejects_null_bytes() -> None:
    with pytest.raises(UnsafeUploadError):
        validate_upload("policy.txt", "text/plain", b"hello\x00world")
    assert extract_text(b"valid text", ".txt") == "valid text"
