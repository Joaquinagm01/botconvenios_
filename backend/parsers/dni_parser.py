import re
from typing import Dict, Optional

MRZ_REGEX = re.compile(r"([A-Z0-9<]{30})")

def parse_mrz(text: str) -> Dict[str, Optional[str]]:
    """Intento simple de parseo MRZ tipo ID. Devuelve campos si encuentra.
    No es 100% robusto; usar como priorizado cuando existan coincidencias.
    """
    out = {"nombre": None, "apellido": None, "dni": None}
    if not text:
        return out
    # buscar líneas que contienen DOB, ID o patrones de MRZ
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        if '<' in l and len(l) >= 30:
            # simplificado: extraer nombres
            parts = l.split('<<')
            if parts:
                apellido = parts[0].replace('<', ' ').strip()
                names = parts[1].replace('<', ' ').strip() if len(parts) > 1 else ''
                out['apellido'] = apellido.title()
                out['nombre'] = names.title()
                # buscar DNI numérico en líneas siguientes
                for l2 in lines:
                    m = re.search(r"(\d{7,8})", l2)
                    if m:
                        out['dni'] = m.group(1)
                        return out
    # fallback: buscar dni en cualquier lado
    for l in lines:
        m = re.search(r"(\d{7,8})", l)
        if m:
            out['dni'] = m.group(1)
            return out
    return out
