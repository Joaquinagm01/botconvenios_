import cv2
import numpy as np
from typing import List, Dict, Tuple
from backend.utils.image_preproc import read_image_from_bytes, to_grayscale, resize_smart, adaptive_thresh

def detect_text_regions_from_bytes(data: bytes, min_area: int = 1000) -> List[Dict]:
    """Detecta regiones candidatas a contener texto usando contornos sobre la imagen umbralizada.

    Devuelve lista de dicts: {"bbox": (x,y,w,h), "crop": image_np}
    """
    img = read_image_from_bytes(data)
    img = resize_smart(img, max_dim=1800)
    gray = to_grayscale(img)
    th = adaptive_thresh(gray)

    # Morphology to join text regions
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 5))
    morph = cv2.morphologyEx(th, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    h_img, w_img = gray.shape[:2]
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < min_area:
            continue
        # ignore very tall or very thin
        if h < 10 or w < 30:
            continue
        # crop with small padding
        pad_x = int(w * 0.03)
        pad_y = int(h * 0.03)
        x0 = max(0, x - pad_x)
        y0 = max(0, y - pad_y)
        x1 = min(w_img, x + w + pad_x)
        y1 = min(h_img, y + h + pad_y)
        crop = img[y0:y1, x0:x1]
        regions.append({"bbox": (x0, y0, x1 - x0, y1 - y0), "crop": crop})

    # sort regions top-to-bottom
    regions = sorted(regions, key=lambda r: r['bbox'][1])
    return regions
