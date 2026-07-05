from __future__ import annotations
import os
from typing import Any

ALLOWED_EXTENSIONS: set[str] = {
    "pdf", "doc", "docx", "xls", "xlsx",
    "ppt", "pptx", "png", "jpg", "jpeg",
    "bmp", "txt",
}

MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
MAX_BATCH_SIZE: int = 500 * 1024 * 1024  # 500MB

MAGIC_NUMBERS: dict[str, bytes] = {
    "pdf": b"%PDF-",
    "doc": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    "docx": b"PK\x03\x04",
    "xls": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    "xlsx": b"PK\x03\x04",
    "ppt": b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1",
    "pptx": b"PK\x03\x04",
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "bmp": b"BM",
    "txt": b"",
}


def validate_file_extension(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_EXTENSIONS


def detect_mime_type(file_bytes: bytes) -> str:
    mime_map: dict[str, str] = {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "bmp": "image/bmp",
        "txt": "text/plain",
    }
    for ext, magic in MAGIC_NUMBERS.items():
        if magic and file_bytes[: len(magic)] == magic:
            return mime_map.get(ext, "application/octet-stream")
    return "application/octet-stream"


def validate_file_size(size: int) -> bool:
    return 0 < size <= MAX_FILE_SIZE
