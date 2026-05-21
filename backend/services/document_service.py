from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from docxtpl import DocxTemplate

from backend.core.config import GENERATED_DIR


def render_docx(template_path: Path, data: dict, output_prefix: str) -> Path:
    output_docx = GENERATED_DIR / f"{output_prefix}_{uuid.uuid4().hex}.docx"
    document = DocxTemplate(str(template_path))
    document.render(data)
    document.save(str(output_docx))
    return output_docx


def convert_docx_to_pdf(docx_path: Path) -> Path:
    output_dir = docx_path.parent
    command = [
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(docx_path),
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "No fue posible convertir a PDF. Verifica que LibreOffice esté instalado y que el comando 'soffice' esté disponible."
        )

    pdf_path = output_dir / f"{docx_path.stem}.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError("LibreOffice terminó sin error, pero no se generó el PDF esperado.")
    return pdf_path


def generate_document(template_path: Path, data: dict, output_prefix: str) -> tuple[Path, Path]:
    docx_path = render_docx(template_path, data, output_prefix)
    pdf_path = convert_docx_to_pdf(docx_path)
    return docx_path, pdf_path
