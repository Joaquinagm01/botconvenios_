import pytesseract
try:
    import easyocr
    _HAS_EASYOCR = True
except Exception:
    easyocr = None
    _HAS_EASYOCR = False
from rapidfuzz import fuzz
from typing import Dict, List, Tuple
import numpy as np
import cv2
from backend.utils.image_preproc import preprocess_for_ocr, read_image_from_bytes
from backend.core.logging_config import setup_logging

logger = setup_logging()
from backend.ocr.region_extractor import detect_text_regions_from_bytes


_easy_reader = None

def get_easy_reader(lang_list=['es']):
    global _easy_reader
    if not _HAS_EASYOCR:
        raise RuntimeError('easyocr no está instalado')
    if _easy_reader is None:
        _easy_reader = easyocr.Reader(lang_list, gpu=False)
    return _easy_reader

def tesseract_ocr_image(img_np: np.ndarray, config: str = "--psm 6") -> str:
    # img_np expected grayscale or color
    return pytesseract.image_to_string(img_np, config=config, lang='spa')

def tesseract_ocr_data(img_np: np.ndarray):
    return pytesseract.image_to_data(img_np, output_type=pytesseract.Output.DICT, lang='spa')

def easyocr_read(image_np: np.ndarray) -> List[Tuple[str, float, List[int]]]:
    reader = get_easy_reader()
    # EasyOCR expects RGB
    if image_np.ndim == 2:
        img = cv2.cvtColor(image_np, cv2.COLOR_GRAY2RGB)
    else:
        img = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
    raw = reader.readtext(img)
    # raw -> list of (bbox, text, confidence)
    out = []
    for bbox, text, conf in raw:
        out.append((text, float(conf), bbox))
    return out

def fuse_texts(t1: str, t2: str) -> str:
    # Token-level fusion: choose token with higher average similarity
    a = t1.split()
    b = t2.split()
    if not a:
        return t2
    if not b:
        return t1
    # If strings are very similar return longer
    if fuzz.ratio(t1, t2) > 85:
        return t1 if len(t1) >= len(t2) else t2
    # Otherwise merge tokens preferring longer token
    merged = []
    for i in range(max(len(a), len(b))):
        ta = a[i] if i < len(a) else ''
        tb = b[i] if i < len(b) else ''
        if not ta:
            merged.append(tb)
            continue
        if not tb:
            merged.append(ta)
            continue
        if fuzz.ratio(ta, tb) > 80:
            merged.append(ta if len(ta) >= len(tb) else tb)
        else:
            # choose token with more letters/digits
            merged.append(ta if sum(c.isalnum() for c in ta) >= sum(c.isalnum() for c in tb) else tb)
    return ' '.join([m for m in merged if m])

def ocr_hybrid_from_bytes(data: bytes) -> Dict[str, str]:
    """Pipeline simple: preproc -> tesseract -> easyocr -> fusion.

    Devuelve dict {'raw_text':..., 'fused_text': ...}
    """
    try:
        orig, pre = preprocess_for_ocr(data)
    except Exception as e:
        logger.exception("Error en preprocesado de imagen")
        raise
    # Tesseract on preprocessed
    try:
        t1 = tesseract_ocr_image(pre, config='--oem 1 --psm 3')
    except Exception:
        logger.exception("Tesseract falló")
        t1 = ""
    # EasyOCR on original color
    if _HAS_EASYOCR:
        try:
            reader = get_easy_reader(['es'])
            raw_easy = reader.readtext(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
            t2 = ' '.join([t[1] for t in raw_easy])
        except Exception:
            logger.exception("EasyOCR falló")
            t2 = ""
    else:
        t2 = ""
    fused = fuse_texts(t1, t2)
    return {"tesseract": t1.strip(), "easyocr": t2.strip(), "fused": fused.strip()}


def ocr_regions_from_bytes(data: bytes) -> List[Dict]:
    """Detecta regiones y ejecuta OCR híbrido por cada una.

    Devuelve lista de {"bbox":(x,y,w,h), "tesseract": ..., "easyocr": ..., "fused": ...}
    """
    regions = detect_text_regions_from_bytes(data)
    outputs = []
    for r in regions:
        crop = r['crop']
        # run tesseract on grayscale crop
        try:
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        except Exception:
            gray = crop
        t = tesseract_ocr_image(gray, config='--oem 1 --psm 6')
        if _HAS_EASYOCR:
            try:
                reader = get_easy_reader(['es'])
                easy_raw = reader.readtext(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                e = ' '.join([it[1] for it in easy_raw])
            except Exception:
                logger.exception("EasyOCR fallo en region")
                e = ''
        else:
            e = ''
        fused = fuse_texts(t, e)
        outputs.append({"bbox": r['bbox'], "tesseract": t.strip(), "easyocr": e.strip(), "fused": fused.strip()})
    return outputs
