from rapidfuzz import process, fuzz
from unidecode import unidecode
from typing import Tuple, Optional

# Lista acotada de provincias y ciudades ejemplo (extender según DB local)
PROVINCES = [
    "Buenos Aires", "Santa Fe", "Córdoba", "Mendoza", "Salta",
    "Tucumán", "Chaco", "Neuquén", "Río Negro", "Misiones"
]

COMMON_CITIES = [
    "Rosario", "Santa Fe", "Córdoba", "Mendoza", "San Miguel de Tucumán",
    "Mar del Plata", "Bahía Blanca", "Salta", "Posadas"
]

def normalize_address(raw: str) -> Tuple[str, float]:
    """Intenta normalizar dirección: corrige provincia/ciudad usando fuzzy.

    Devuelve (normalized_address, confidence)
    """
    if not raw:
        return "", 0.0
    txt = unidecode(raw).strip()
    # buscar provincia
    prov, prov_score, _ = process.extractOne(txt, PROVINCES, scorer=fuzz.WRatio)
    city, city_score, _ = process.extractOne(txt, COMMON_CITIES, scorer=fuzz.WRatio)
    # heurística simple: reemplazar tokens coincidentes
    conf = min(1.0, (prov_score + city_score) / 200.0 + 0.2)
    normalized = txt
    if prov_score > 60:
        normalized = normalized.replace(prov.upper(), prov).replace(prov.lower(), prov)
    if city_score > 60:
        normalized = normalized.replace(city.upper(), city).replace(city.lower(), city)
    return normalized, conf
