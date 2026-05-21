from __future__ import annotations

import subprocess
from pathlib import Path

from backend.core.config import TEMPLATE_CACHE_DIR, TEMPLATES_DIR


def list_templates() -> list[dict[str, str]]:
    templates: list[dict[str, str]] = []
    for path in sorted([*TEMPLATES_DIR.glob("*.docx"), *TEMPLATES_DIR.glob("*.doc")]):
        templates.append({"name": path.stem, "filename": path.name})
    return templates


def convert_doc_to_docx(source_path: Path) -> Path:
    cached_path = TEMPLATE_CACHE_DIR / f"{source_path.stem}.docx"
    if cached_path.exists() and cached_path.stat().st_mtime >= source_path.stat().st_mtime:
        return cached_path

    command = [
        "soffice",
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        str(TEMPLATE_CACHE_DIR),
        str(source_path),
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0 or not cached_path.exists():
        raise RuntimeError(
            "No se pudo convertir la plantilla .doc a .docx. Verifica que LibreOffice esté instalado y que el comando 'soffice' esté disponible."
        )

    return cached_path


def get_template_path(template_name: str) -> Path:
    candidate = TEMPLATES_DIR / template_name
    if candidate.exists():
        if candidate.suffix.lower() == ".doc":
            return convert_doc_to_docx(candidate)
        return candidate

    alternative = TEMPLATES_DIR / f"{template_name}.docx"
    if alternative.exists():
        return alternative

    legacy_alternative = TEMPLATES_DIR / f"{template_name}.doc"
    if legacy_alternative.exists():
        return convert_doc_to_docx(legacy_alternative)

    matches = list(TEMPLATES_DIR.glob(f"{Path(template_name).stem}*.docx"))
    if matches:
        return matches[0]

    legacy_matches = list(TEMPLATES_DIR.glob(f"{Path(template_name).stem}*.doc"))
    if legacy_matches:
        return convert_doc_to_docx(legacy_matches[0])

    raise FileNotFoundError(f"No se encontró la plantilla {template_name}")
