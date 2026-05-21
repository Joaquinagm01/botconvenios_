from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import UploadFile

from backend.core.config import ALLOWED_EXTENSIONS, UPLOAD_DIR


def validate_upload_file(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Formato no permitido: {filename}")


async def save_upload_file(upload_file: UploadFile) -> Path:
    validate_upload_file(upload_file.filename or "")
    suffix = Path(upload_file.filename).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    destination = UPLOAD_DIR / safe_name
    content = await upload_file.read()
    destination.write_bytes(content)
    return destination
