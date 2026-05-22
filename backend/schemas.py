from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DetectedData(BaseModel):
    model_config = ConfigDict(extra="allow")

    nombre: str = ""
    apellido: str = ""
    dni: str = ""
    cuit: str = ""
    direccion: str = ""
    monto: str = ""
    fecha: str = ""
    telefono: str = ""
    email: str = ""
    razon_social: str = ""
    raw_text: str = ""
    roles: dict[str, str] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    files: List[Dict[str, Any]]


class TemplateInfo(BaseModel):
    name: str
    filename: str


class ProcessResponse(BaseModel):
    detected: DetectedData
    extracted_text: str
    debug_images: Optional[list[str]] = None


class GenerateRequest(BaseModel):
    template_name: str = Field(min_length=1)
    data: DetectedData


class GenerateResponse(BaseModel):
    docx_name: str
    pdf_name: str
    docx_url: str
    pdf_url: str
    preview_text: Optional[str] = None
