"""Ejemplo de pipeline que integra preprocesado, OCR híbrido, normalización y llamada a Ollama."""
from typing import Dict, Any
from backend.ocr.hybrid_ocr import ocr_hybrid_from_bytes
from backend.ai.ollama_client import OllamaClient
from backend.ai.prompts import PROMPT_DOCUMENT, PROMPT_ADDRESS, PROMPT_DNI
from backend.parsers.address_normalizer import normalize_address
from backend.parsers.dni_parser import parse_mrz
from backend.validators.validators import validate_dni, validate_cuit, validate_email, normalize_phone, parse_date
from backend.ocr.hybrid_ocr import ocr_regions_from_bytes
import re
import json
from backend.core.logging_config import setup_logging

logger = setup_logging()

ollama = OllamaClient()

def process_document_bytes(data: bytes, filename: str = "file.pdf", model: str = "phi4-mini") -> Dict[str, Any]:
    # 1) OCR híbrido
    texts = ocr_hybrid_from_bytes(data)

    # 1.5) OCR por regiones para priorizar bloques (nombre, dni, direccion)
    try:
        region_outputs = ocr_regions_from_bytes(data)
    except Exception as e:
        logger.warning(f"No se pudo extraer regiones: {e}")
        region_outputs = []

    # heurísticas simples para elegir candidatas
    region_candidates: Dict[str, Dict] = {"dni": {"text": None, "score": 0.0},
                                         "direccion": {"text": None, "score": 0.0},
                                         "nombre": {"text": None, "score": 0.0}}
    for r in region_outputs:
        fused = (r.get('fused') or '').upper()
        # buscar dni (7-8 dígitos)
        m = re.search(r"\b(\d{7,8})\b", fused)
        if m:
            region_candidates['dni'] = {"text": m.group(1), "score": 0.95}
        # direccion heurística: contiene palabras tipo CALLE/AV/DOMICILIO o números + calle
        if any(tok in fused for tok in ('DOMICILIO','CALLE','AV','AV.', 'ST', 'B°', 'BARRIO')) or re.search(r"\d+\s*-?\s*\d+", fused):
            # preferir si contiene provincia/city cues
            region_candidates['direccion'] = {"text": r.get('fused'), "score": 0.85}
        # nombre heurística: texto largo sin muchos dígitos y varias palabras en mayúscula
        words = [w for w in fused.split() if w.isalpha()]
        if len(words) >= 2 and sum(any(c.isalpha() for c in w) for w in words) >= 2 and not re.search(r"\d", fused):
            # puntuar si parece nombre (mayúsculas y tokens comunes de nombres)
            region_candidates['nombre'] = {"text": r.get('fused'), "score": 0.7}


    # 2) MRZ parse heuristic
    mrz = parse_mrz(texts.get('tesseract', '') + '\n' + texts.get('easyocr', ''))

    # 3) Ask Ollama for structured extraction (document-level)
    # Enviamos además las mejores candidatas de regiones para que el modelo priorice
    region_hint = {k: v for k, v in region_candidates.items() if v.get('text')}
    region_hint_text = json.dumps(region_hint, ensure_ascii=False)
    prompt = PROMPT_DOCUMENT + "\n\nREGION_CANDIDATES:\n" + region_hint_text + "\n\nOCR_TEXT:\n" + texts.get('fused', '')
    try:
        ai_out = ollama.generate_json(model=model, prompt=prompt)
    except Exception as e:
        logger.warning(f"Ollama fallo para {filename}: {e}")
        ai_out = {"error": str(e)}

    # 4) Normalize address example
    addr_raw = ai_out.get('direccion_texto') if isinstance(ai_out, dict) else None
    addr_norm, addr_conf = ("", 0.0)
    if addr_raw:
        addr_norm, addr_conf = normalize_address(addr_raw.get('valor') if isinstance(addr_raw, dict) else addr_raw)

    # 5) post-validate and assemble fields with confidences
    def field(v, conf):
        return {"valor": v, "confidence": conf}

    out = {
        "ocr": texts,
        "mrz": mrz,
        "ai_raw": ai_out,
        "fields": {}
    }

    # Example: populate some fields
    if isinstance(ai_out, dict):
        for k in ['nombre','apellido','dni','cuit','telefono','email','fecha','monto','direccion_texto']:
            v = ai_out.get(k)
            if isinstance(v, dict):
                val = v.get('valor')
                conf = float(v.get('confidence', 0.0))
            else:
                val = v
                conf = 0.5
            # basic validators
            if k == 'dni' and val:
                conf = conf if validate_dni(str(val)) else min(0.6, conf)
            if k == 'cuit' and val:
                conf = conf if validate_cuit(str(val)) else min(0.6, conf)
            if k == 'email' and val:
                conf = conf if validate_email(str(val)) else min(0.6, conf)
            if k == 'telefono' and val:
                val = normalize_phone(str(val))
            if k == 'fecha' and val:
                val = parse_date(str(val))
            if k == 'direccion_texto' and val:
                val = addr_norm
                conf = max(conf, addr_conf)
            out['fields'][k] = field(val, float(conf or 0.0))

    # Aplicar candidatas por región como refuerzo/fallback
    if region_candidates.get('dni', {}).get('text'):
        if not out['fields'].get('dni') or (out['fields']['dni']['confidence'] < 0.9):
            out['fields']['dni'] = field(region_candidates['dni']['text'], float(region_candidates['dni']['score']))
    if region_candidates.get('nombre', {}).get('text'):
        if not out['fields'].get('nombre') or (out['fields']['nombre']['confidence'] < 0.8):
            out['fields']['nombre'] = field(region_candidates['nombre']['text'], float(region_candidates['nombre']['score']))
    if region_candidates.get('direccion', {}).get('text'):
        if not out['fields'].get('direccion_texto') or (out['fields']['direccion_texto']['confidence'] < 0.8):
            out['fields']['direccion_texto'] = field(region_candidates['direccion']['text'], float(region_candidates['direccion']['score']))

    return out
