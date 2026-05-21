import cv2
import numpy as np
from typing import Tuple

def read_image_from_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img

def to_grayscale(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

def resize_smart(img: np.ndarray, max_dim: int = 2000) -> np.ndarray:
    h, w = img.shape[:2]
    scale = 1.0
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
    if scale != 1.0:
        img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_LINEAR)
    return img

def apply_clahe(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    return clahe.apply(gray)

def denoise(img: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(img, None, 10, 7, 21)

def bilateral(img: np.ndarray) -> np.ndarray:
    return cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)

def sharpen(img: np.ndarray) -> np.ndarray:
    kernel = np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
    return cv2.filter2D(img, -1, kernel)

def adaptive_thresh(img: np.ndarray) -> np.ndarray:
    return cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 2)

def deskew(gray: np.ndarray) -> np.ndarray:
    coords = np.column_stack(np.where(gray < 255))
    if coords.shape[0] == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def preprocess_for_ocr(data: bytes) -> Tuple[np.ndarray, np.ndarray]:
    """Devuelve (original_color, preprocessed_gray) lista para OCR."""
    img = read_image_from_bytes(data)
    img = resize_smart(img, max_dim=1800)
    gray = to_grayscale(img)
    gray = denoise(gray)
    gray = apply_clahe(gray)
    gray = bilateral(gray)
    gray = sharpen(gray)
    gray = deskew(gray)
    th = adaptive_thresh(gray)
    return img, th
