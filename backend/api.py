from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
import logging
from fastapi.responses import FileResponse

from backend.core.config import BACKEND_URL, GENERATED_DIR
from backend.schemas import GenerateRequest, GenerateResponse, ProcessResponse, TemplateInfo, UploadResponse
from backend.services.document_service import generate_document
from backend.services.file_service import save_upload_file, validate_upload_file
from backend.services.ocr_service import extract_detected_data, extract_text_from_file
from backend.services.template_service import get_template_path, list_templates


router = APIRouter(prefix="/api", tags=["convenios"])

logger = logging.getLogger("botconvenios")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/templates", response_model=list[TemplateInfo])
def available_templates() -> list[TemplateInfo]:
    return [TemplateInfo(**template) for template in list_templates()]


@router.post("/upload", response_model=UploadResponse)
async def upload_files(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Debes subir al menos un archivo.")

    saved_files: list[dict[str, str]] = []
    for uploaded_file in files:
        try:
            validate_upload_file(uploaded_file.filename or "")
            saved_path = await save_upload_file(uploaded_file)
            saved_files.append({
                "original_name": uploaded_file.filename or "",
                "saved_name": saved_path.name,
                "path": str(saved_path),
            })
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return UploadResponse(files=saved_files)


@router.post("/process", response_model=ProcessResponse)
async def process_file(files: list[UploadFile] = File(...)) -> ProcessResponse:
    if not files:
        raise HTTPException(status_code=400, detail="Debes enviar archivos para procesar.")

    # Procesar archivos en memoria sin guardarlos en disco
    aggregated_texts: list[str] = []
    merged: dict = {}

    # Preferir pipeline nuevo; fallback a detect_from_bytes si falla
    from backend.integrations.pipeline import process_document_bytes
    from backend.services.ocr_service import detect_from_bytes

    pipeline_results = None

    for uploaded_file in files:
        try:
            validate_upload_file(uploaded_file.filename or "")
            contents = await uploaded_file.read()
            try:
                res = process_document_bytes(contents, filename=uploaded_file.filename or "uploaded")
                logger.info(f"Pipeline procesó archivo {uploaded_file.filename}")
            except Exception as e:
                logger.warning(f"Pipeline falló para {uploaded_file.filename}: {e}; usando detect_from_bytes fallback")
                det = detect_from_bytes(contents, uploaded_file.filename or "uploaded")
                # construir resultado minimal
                res = {"ocr": {"fused": det.raw_text or ""}, "fields": {k: {"valor": getattr(det, k, None), "confidence": 0.6} for k in ['nombre','apellido','dni','cuit','telefono','email','fecha','monto','direccion']}}

            # combinar campos: preferir valores existentes
            fields = res.get('fields', {}) if isinstance(res, dict) else {}
            for k, v in fields.items():
                val = v.get('valor') if isinstance(v, dict) else v
                if val and not merged.get(k):
                    merged[k] = v

            # conservar texto bruto para referencia
            ocr_text = res.get('ocr', {}).get('fused') if isinstance(res, dict) else None
            if ocr_text:
                aggregated_texts.append(ocr_text)
            pipeline_results = res
        except Exception as exc:
            logger.exception("Error procesando archivo")
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    combined_text = "\n".join(t for t in aggregated_texts if t).strip()

    # construir DetectedData final
    final = extract_detected_data(combined_text)
    # sobreescribir con valores detectados por pipeline (merged)
    for k, v in merged.items():
        if v:
            val = v.get('valor') if isinstance(v, dict) else v
            try:
                setattr(final, k if k != 'direccion_texto' else 'direccion', val)
            except Exception:
                logger.warning(f"No se pudo setear campo {k} en objeto final")

    return ProcessResponse(detected=final, extracted_text=combined_text or "", debug_images=None)


@router.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        template_path = get_template_path(request.template_name)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not template_path.exists():
        raise HTTPException(status_code=404, detail="La plantilla seleccionada no existe.")

    data = request.data.model_dump()
    output_prefix = template_path.stem.replace(" ", "_")

    try:
        docx_path, pdf_path = generate_document(template_path, data, output_prefix)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateResponse(
        docx_name=docx_path.name,
        pdf_name=pdf_path.name,
        docx_url=f"{BACKEND_URL}/api/download/docx/{docx_path.name}",
        pdf_url=f"{BACKEND_URL}/api/download/pdf/{pdf_path.name}",
        preview_text=f"Generado desde {template_path.name}",
    )


@router.get("/download/docx/{filename}")
def download_docx(filename: str):
    file_path = GENERATED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="DOCX no encontrado.")
    return FileResponse(file_path, filename=filename)


@router.get("/download/pdf/{filename}")
def download_pdf(filename: str):
    file_path = GENERATED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="PDF no encontrado.")
    return FileResponse(file_path, filename=filename)


@router.get("/debug/{filename}")
def debug_image(filename: str):
    from backend.core.config import UPLOAD_DIR

    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Imagen de depuración no encontrada.")
    return FileResponse(file_path, filename=filename)
