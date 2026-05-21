from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATES_DIR = BASE_DIR / "plantillas"
GENERATED_DIR = BASE_DIR / "documentos_generados"
TEMPLATE_CACHE_DIR = TEMPLATES_DIR / ".cache"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def ensure_directories() -> None:
    from backend.core.logging_config import setup_logging
    logger = setup_logging()
    for directory in (UPLOAD_DIR, TEMPLATES_DIR, GENERATED_DIR, TEMPLATE_CACHE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Asegurado directorio: {directory}")
