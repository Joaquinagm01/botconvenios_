from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import router
from backend.core.config import ensure_directories
from backend.core.logging_config import setup_logging


ensure_directories()
logger = setup_logging()
logger.info("Iniciando Bot Convenios backend")

app = FastAPI(
    title="Bot Convenios",
    description="Generación local de convenios a partir de OCR y plantillas DOCX.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
