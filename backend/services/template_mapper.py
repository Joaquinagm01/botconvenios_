from pathlib import Path
from typing import Dict, Any
import re
import zipfile
from rapidfuzz import fuzz
from backend.services.template_inspector import extract_placeholders_from_docx
from backend.core.logging_config import setup_logging

logger = setup_logging()

KEYWORD_FIELD_MAP = {
    'monto': ['$', 'pesos', 'honorari', 'importe', 'monto', 'total'],
    'dni': ['dni', 'documento', 'nro de documento', 'nº documento'],
    'cuit': ['cuit', 'c.u.i.t', 'cuit:'],
    'direccion': ['calle', 'av.', 'av', 'domicilio', 'barrio', 'codigo postal', 'cp', 'provincia', 'ciudad'],
    'telefono': ['tel', 'telefono', 'cel', 'movil'],
    'email': ['@', 'email', 'e-mail', 'correo'],
    'fecha': ['fecha', 'día', 'dia', 'mes', 'año', 'ano'],
    'razon_social': ['razon social', 'razón social', 'empresa', 's.r.l', 'sociedad']
}

FIELDS = list(KEYWORD_FIELD_MAP.keys()) + ['nombre', 'apellido']

def _read_document_xml(path: Path) -> str:
    try:
        with zipfile.ZipFile(path, 'r') as z:
            return z.read('word/document.xml').decode('utf-8', errors='ignore')
    except Exception as e:
        logger.debug(f"No se pudo leer document.xml: {e}")
        return ''


def infer_field_from_snippet(snippet: str, placeholder: str) -> Dict[str, Any]:
    s = (snippet or '').lower()
    # direct keyword rules
    for field, kws in KEYWORD_FIELD_MAP.items():
        for kw in kws:
            if kw in s:
                return {'field': field, 'confidence': 0.95, 'reason': f'keyword:{kw}'}

    # numeric placeholder heuristics
    if re.fullmatch(r'\d+', placeholder):
        # if snippet contains $ or pesos -> monto
        if '$' in snippet or 'pesos' in s:
            return {'field': 'monto', 'confidence': 0.9, 'reason': 'numeric_with_money'}
        # otherwise unclear
        return {'field': None, 'confidence': 0.2, 'reason': 'numeric_unclear'}

    # fuzzy match placeholder name to known fields
    best_field = None
    best_score = 0
    for f in FIELDS:
        score = fuzz.ratio(placeholder.lower(), f)
        if score > best_score:
            best_score = score
            best_field = f
    if best_score >= 80:
        return {'field': best_field, 'confidence': 0.85, 'reason': f'fuzzy:{best_score}'}

    # fallback: search for digit patterns nearby
    if re.search(r'\$\s*\d', snippet) or re.search(r'\d+\.\d{3}', snippet):
        return {'field': 'monto', 'confidence': 0.7, 'reason': 'money_pattern'}

    return {'field': None, 'confidence': 0.0, 'reason': 'no_match'}


def map_template_placeholders(path: Path) -> Dict[str, Any]:
    placeholders = extract_placeholders_from_docx(path)
    xml = _read_document_xml(path)
    mapping = {}
    for ph in placeholders:
        # try to locate snippet around placeholder in xml
        idx = xml.find(str(ph))
        snippet = None
        if idx != -1:
            start = max(0, idx - 120)
            end = min(len(xml), idx + len(str(ph)) + 120)
            snippet = re.sub(r'<[^>]+>', ' ', xml[start:end])
            snippet = ' '.join(snippet.split())
        else:
            # try search for tokens containing ph
            # fallback to empty snippet
            snippet = ''

        inferred = infer_field_from_snippet(snippet, ph)
        mapping[str(ph)] = {'snippet': snippet, 'inferred': inferred}

    return {'placeholders': sorted(list(placeholders)), 'mapping': mapping}


def scan_templates_with_mapping(templates_dir: Path) -> Dict[str, Any]:
    out = {}
    for p in sorted(templates_dir.glob('*.docx')):
        out[p.name] = map_template_placeholders(p)
    return out
