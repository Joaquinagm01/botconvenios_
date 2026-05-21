from __future__ import annotations

import re
from pathlib import Path

import cv2
import pdfplumber
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader
from io import BytesIO
import numpy as np

from backend.core.config import TESSERACT_CMD, UPLOAD_DIR
from backend.schemas import DetectedData
from backend.utils.text_utils import (
    choose_best_line,
    compact_spaces,
    first_match,
    normalize_text,
    split_full_name,
)


pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def preprocess_image(image_path: Path) -> Image.Image:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"No se pudo abrir la imagen: {image_path.name}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Escalar para mejorar OCR en fotos pequeñas
    h, w = gray.shape
    target_w = 1600
    if w < target_w:
        scale = target_w / float(w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # Denoising y ecualización de histograma
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    try:
        gray = cv2.equalizeHist(gray)
    except Exception:
        pass

    # Intentar detectar orientación (Rotate) con Tesseract OSD
    try:
        osd = pytesseract.image_to_osd(Image.fromarray(gray))
        m = re.search(r"Rotate:\s*(\d+)", osd)
        if m:
            angle = int(m.group(1))
            if angle != 0:
                # rotar la imagen en sentido contrario para corregir
                if angle == 90:
                    gray = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif angle == 180:
                    gray = cv2.rotate(gray, cv2.ROTATE_180)
                elif angle == 270:
                    gray = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
    except Exception:
        pass

    # Umbral adaptativo para mejorar contraste texto/fondo
    try:
        threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
    except Exception:
        threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return Image.fromarray(threshold)


def extract_text_from_image(image_path: Path) -> str:
    prepared = preprocess_image(image_path)

    # Intentar con varias configuraciones de Tesseract
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 3",
        "--oem 3 --psm 11",
        "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789",
    ]

    for cfg in configs:
        try:
            raw_text = pytesseract.image_to_string(prepared, lang="spa+eng", config=cfg)
            cleaned = normalize_text(raw_text)
            if cleaned and len(cleaned) > 3:
                return cleaned
        except Exception:
            continue

    # último recurso: intentar sin preprocesado usando PIL
    try:
        raw_text = pytesseract.image_to_string(Image.open(image_path), lang="spa+eng")
        return normalize_text(raw_text)
    except Exception:
        return ""


def _ocr_pdf_as_images(pdf_path: Path) -> str:
    """Renderiza cada página del PDF a imagen a alta resolución, aplica
    preprocesado robusto (CLAHE, bilateral, umbral adaptativo) y ejecuta
    Tesseract con varios `psm` como último recurso."""
    text_parts: list[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                try:
                    # Renderizar a mayor resolución
                    img = page.to_image(resolution=600)
                    pil = img.original.convert("RGB")
                    # Primero intentar OCR directo sobre la imagen renderizada
                    try:
                        direct = pytesseract.image_to_string(pil, lang="spa+eng")
                    except Exception:
                        direct = ""

                    def _is_good(s: str) -> bool:
                        if not s or len(s) < 30:
                            return False
                        letters = sum(1 for c in s if c.isalpha())
                        return (letters / max(1, len(s))) > 0.2

                    page_text = ""
                    if _is_good(direct):
                        page_text = direct
                    else:
                        # convertir a cv2 y aplicar preprocesado robusto si el OCR directo falla
                        import numpy as np

                        cv_img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
                        h, w = cv_img.shape[:2]
                        scale = 3000.0 / max(w, h)
                        if scale > 1:
                            cv_img = cv2.resize(cv_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

                        gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                        cl = clahe.apply(gray)
                        bil = cv2.bilateralFilter(cl, 9, 75, 75)
                        try:
                            th = cv2.adaptiveThreshold(bil, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
                        except Exception:
                            th = cv2.threshold(bil, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                        med = cv2.medianBlur(th, 3)

                        configs = ["--oem 3 --psm 3", "--oem 3 --psm 6", "--oem 3 --psm 1"]
                        for cfg in configs:
                            try:
                                txt = pytesseract.image_to_string(med, lang="spa+eng", config=cfg)
                                if txt and txt.strip():
                                    page_text = txt
                                    break
                            except Exception:
                                continue

                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                except Exception:
                    continue
    except Exception:
        return ""

    return normalize_text("\n".join(text_parts))


def extract_text_from_pdf(pdf_path: Path) -> str:
    collected_text: list[str] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    collected_text.append(page_text)
    except Exception:
        collected_text = []

    if collected_text:
        joined = normalize_text("\n".join(collected_text))
        letters = len([c for c in joined if c.isalpha()])
        total = len(joined)
        if total < 40 or (total > 0 and (letters / total) < 0.25):
            return ""
        return joined

    # fallback a PyPDF2
    try:
        reader = PdfReader(str(pdf_path))
        fallback_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                fallback_parts.append(text)
        return normalize_text("\n".join(fallback_parts))
    except Exception:
        return ""


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png"}:
        return extract_text_from_image(file_path)
    if suffix == ".pdf":
        text = extract_text_from_pdf(file_path)
        if text and text.strip():
            return text
        # fallback a renderizado + preprocesado
        return _ocr_pdf_as_images(file_path)
    raise ValueError(f"Formato no soportado: {file_path.name}")


def _preprocess_cv_image(cv_img: np.ndarray) -> Image.Image:
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    h, w = gray.shape
    target_w = 1600
    if w < target_w:
        scale = target_w / float(w)
        gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    try:
        gray = cv2.equalizeHist(gray)
    except Exception:
        pass

    try:
        threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
    except Exception:
        threshold = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    return Image.fromarray(threshold)


def _ocr_pdf_as_images_bytes(pdf, dpi: int = 300) -> str:
    text_parts: list[str] = []
    try:
        for page in pdf.pages:
            try:
                img = page.to_image(resolution=600)
                pil = img.original.convert("RGB")
                cv_img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
                h, w = cv_img.shape[:2]
                scale = 3000.0 / max(w, h)
                if scale > 1:
                    cv_img = cv2.resize(cv_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                cl = clahe.apply(gray)
                bil = cv2.bilateralFilter(cl, 9, 75, 75)
                try:
                    th = cv2.adaptiveThreshold(bil, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
                except Exception:
                    th = cv2.threshold(bil, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                med = cv2.medianBlur(th, 3)

                configs = ["--oem 3 --psm 3", "--oem 3 --psm 6", "--oem 3 --psm 1"]
                page_text = ""
                for cfg in configs:
                    try:
                        txt = pytesseract.image_to_string(med, lang="spa+eng", config=cfg)
                        if txt and txt.strip():
                            page_text = txt
                            break
                    except Exception:
                        continue

                if page_text and page_text.strip():
                    text_parts.append(page_text)
            except Exception:
                continue
    except Exception:
        return ""

    return normalize_text("\n".join(text_parts))


def extract_text_from_bytes(data: bytes, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png"}:
        arr = np.frombuffer(data, np.uint8)
        cv_img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if cv_img is None:
            # fallback to PIL
            try:
                pil = Image.open(BytesIO(data)).convert("RGB")
                return normalize_text(pytesseract.image_to_string(pil, lang="spa+eng"))
            except Exception:
                return ""
        prepared = _preprocess_cv_image(cv_img)
        try:
            raw = pytesseract.image_to_string(prepared, lang="spa+eng", config="--oem 3 --psm 6")
            cleaned = normalize_text(raw)
            if cleaned:
                return cleaned
        except Exception:
            pass
        try:
            raw = pytesseract.image_to_string(Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)), lang="spa+eng")
            return normalize_text(raw)
        except Exception:
            return ""

    if suffix == ".pdf":
        # Para PDFs usamos un archivo temporal para aprovechar el pipeline probado
        import tempfile, os

        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(data)
            tmp.flush()
            tmp.close()
            return extract_text_from_file(Path(tmp.name))
        except Exception:
            try:
                if tmp:
                    os.unlink(tmp.name)
            except Exception:
                pass
            return ""
        finally:
            try:
                if tmp and Path(tmp.name).exists():
                    os.unlink(tmp.name)
            except Exception:
                pass

    raise ValueError(f"Formato no soportado: {filename}")


def _extract_name_candidates(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    label_line = choose_best_line(lines, ("nombre", "titular", "cliente", "apellido"))
    if label_line:
        cleaned = re.sub(r"(?i)nombre(?: y apellido)?[:\-]?", "", label_line)
        cleaned = re.sub(r"(?i)titular[:\-]?", "", cleaned)
        cleaned = compact_spaces(cleaned)
        if cleaned:
            return split_full_name(cleaned)

    for line in lines[:12]:
        candidate = compact_spaces(line)
        if 2 <= len(candidate.split()) <= 5 and not re.search(r"\d", candidate):
            if not any(keyword in candidate.lower() for keyword in ("cuit", "dni", "domicilio", "dirección", "direccion", "factura", "contrato")):
                return split_full_name(candidate)

    return "", ""


def _parse_mrz(text: str) -> tuple[str, str, str] | None:
    """Intentar parsear una zona MRZ (machine-readable zone) simple.
    Retorna (nombre, apellido, dni) si se detecta, sino None.
    Esta implementación es tolerante y busca líneas con '<<' típicas de MRZ.
    """
    lines = [l for l in (s.strip() for s in text.splitlines()) if l]
    # buscar líneas que contengan '<<' (separador de apellidos/nombres)
    for i, line in enumerate(lines):
        if '<<' in line and any(c.isalpha() for c in line):
            # intentar extraer la parte de nombres
            try:
                parts = line.split('<<', 1)
                surname_block = parts[0]
                given_block = parts[1]
                # si la parte izquierda tiene más dígitos que letras (prefijos tipo IDARG123...), ignorar
                letters = len(re.findall(r"[A-ZÑÁÉÍÓÚ]", surname_block))
                digits = len(re.findall(r"\d", surname_block))
                if digits > letters:
                    continue
                # limpiar '<' a espacios y compactar
                surname = re.sub(r'<+', ' ', surname_block).strip()
                given = re.sub(r'<+', ' ', given_block).strip()
                # buscar DNI de 8 dígitos cercano (preferir líneas previas/siguientes)
                dni = ''
                # en la misma línea buscar 8 dígitos exactos
                m = re.search(r'(\d{8})', line)
                if m:
                    dni = m.group(1)
                else:
                    # buscar en líneas cercanas (ampliar ventana)
                    window = lines[max(0, i - 5) : min(len(lines), i + 5)]
                    for w in window:
                        m2 = re.search(r'(\d{8})', w)
                        if m2:
                            dni = m2.group(1)
                            break
                    # si no encontró 8 dígitos, buscar 7 como fallback
                    if not dni:
                        window = lines[max(0, i - 5) : min(len(lines), i + 5)]
                        for w in window:
                            m3 = re.search(r'(\d{7})', w)
                            if m3:
                                dni = m3.group(1)
                                break

                if surname or given or dni:
                    # normalizar: given puede contener apellido residual, quedarnos con nombre(s)
                    # devolver nombre, apellido, dni
                    return (given, surname, dni)
            except Exception:
                continue
    return None


def extract_detected_data(text: str) -> DetectedData:
    normalized = normalize_text(text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    # Intentar extraer desde etiquetas visibles (Nombre / Apellido) primero
    nombre, apellido = "", ""
    for i, line in enumerate(lines):
        low = line.lower()
        if 'nombre' in low or 'name' in low:
            # siguiente línea probable contiene el nombre
            if i + 1 < len(lines):
                cand = lines[i + 1].strip()
                # ignorar si la siguiente línea es basura o etiqueta
                if not any(k in cand.lower() for k in ('documento', 'apellido', 'cuit', 'dni', 'telefono')):
                    nombre = cand
        if 'apellido' in low or 'surname' in low:
            if i + 1 < len(lines):
                cand = lines[i + 1].strip()
                # ignorar si es basura
                if not any(k in cand.lower() for k in ('documento', 'nombre', 'cuit', 'dni', 'telefono', 'sexo')):
                    apellido = cand

    # Si no hay nombre/apellido detectados (o incompletos), intentar MRZ
    mrz = None
    mrz_given = ""
    mrz_surname = ""
    mrz_dni = ""
    if not nombre or not apellido:
        mrz = _parse_mrz(normalized)
        if mrz:
            mrz_given, mrz_surname, mrz_dni = mrz
            if not nombre:
                nombre = mrz_given
            if not apellido:
                apellido = mrz_surname

    # Priorizar DNI desde MRZ si existe, sino buscar en texto
    if mrz_dni:
        dni = mrz_dni
    else:
        dni = first_match(
            [
                r"(?:DNI|D\.N\.I\.?|Documento)\D*(\d{7,8})",
                r"\b(\d{7,8})\b",
            ],
            normalized,
        )
    cuit = first_match(
        [
            r"(?:CUIT|C\.U\.I\.T\.?|Cuit)\D*(\d{2}-?\d{8}-?\d)",
            r"\b(\d{2}-?\d{8}-?\d)\b",
        ],
        normalized,
    )
    email = first_match([r"([\w\.-]+@[\w\.-]+\.[A-Za-z]{2,})"], normalized)
    telefono = first_match(
        [
            r"(?:tel[eé]fono|celular|whatsapp|telefono)\D*(\+?\d[\d\s\-()]{7,})",
            r"(\+?\d[\d\s\-()]{7,})",
        ],
        normalized,
    )
    monto = first_match(
        [
            r"(?:monto|importe|total|valor)\D*(\$?\s?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?)",
            r"(\$?\s?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})?)",
        ],
        normalized,
    )
    fecha = first_match(
        [
            r"(?:fecha)\D*((?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{1,2}\s+de\s+\w+\s+de\s+\d{4}))",
            r"\b((?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(?:\d{1,2}\s+de\s+\w+\s+de\s+\d{4}))\b",
        ],
        normalized,
    )
    direccion = first_match(
        [
            r"(?:domicilio|direcci[oó]n|direccion)[:\-]?\s*(.+)",
        ],
        normalized,
    )

    # Buscar bloque tras la etiqueta 'domicilio' si no se obtuvo con first_match
    # o si el resultado inicial es muy corto/poco fiable
    def _find_block_after_label() -> str:
        for i, line in enumerate(lines):
            if re.search(r"\bdomicilio\b|\bdom\b|direcci[oó]n", line, re.IGNORECASE):
                parts: list[str] = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    nxt = lines[j]
                    if re.search(r"\b(cuil|cuit|huella|firma|fecha|documento|dni|tel[eé]fono)\b", nxt, re.IGNORECASE):
                        break
                    # no ignorar líneas que parecen parte de dirección
                    if nxt.strip():
                        parts.append(nxt)
                cand = " ".join(parts).strip()
                if cand:
                    return cand
        return ""

    if not direccion or (len(direccion) < 8 or not re.search(r"\d", direccion)):
        cand = _find_block_after_label()
        if cand:
            # preferir si contiene números o es claramente más larga
            if re.search(r"\d", cand) or len(cand) > len(direccion or ""):
                direccion = cand

    # Si aún no hay dirección, buscar una línea que parezca contener calle + número
    if not direccion:
        for line in lines:
            if re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ].*\d{1,5}", line):
                direccion = line
                break

    # Normalizar y limpiar basura común en OCR (tokens sueltos, caracteres extraños)
    def _clean_address(s: str) -> str:
        if not s:
            return s
        s = re.sub(r"[\r\n]+", " ", s)
        # reemplazar caracteres no alfanuméricos salvo puntuación permitida
        s = re.sub(r"[^\w\s\-\.,º°#/]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        # eliminar tokens de 1-2 letras que suelen ser ruido (ej. 'de', 'rE', 'JE')
        tokens = [t for t in s.split() if not (len(t) <= 2 and t.isalpha() and t.lower() not in ('san', 'sra', 'st.'))]
        s = " ".join(tokens)
        return s.strip()

    direccion = _clean_address(direccion)

    razon_social = first_match(
        [
            r"(?:raz[oó]n social|empresa|sociedad)[:\-]?\s*(.+)",
        ],
        normalized,
    )

    # Detección simple de roles/entidades por palabras clave y contexto
    def detect_role(keywords: tuple[str, ...]) -> str:
        # Busca una línea que contenga cualquiera de las palabras clave y retorna el resto de la línea
        pattern = r"|".join(re.escape(k) for k in keywords)
        for i, line in enumerate(lines):
            lowered = line.lower()
            if any(k in lowered for k in keywords):
                # quitar la palabra clave y separadores comunes
                cleaned = re.sub(rf"(?i)\b(?:{pattern})\b", "", line)
                cleaned = re.sub(r"[:\-\|]+", "", cleaned)
                cleaned = compact_spaces(cleaned)
                if cleaned:
                    return cleaned
                # si la línea es únicamente el rol, revisar la siguiente línea como candidato
                if i + 1 < len(lines):
                    return compact_spaces(lines[i + 1])
        return ""

    roles: dict[str, str] = {}
    roles['abogado'] = detect_role(("abogado", "letrado"))
    roles['asegurado'] = detect_role(("asegurado", "titular", "cliente"))
    roles['tercero'] = detect_role(("tercero", "contraparte", "otro"))
    roles['auto'] = detect_role(("auto", "automovil", "automóvil", "vehiculo", "vehículo", "patente", "dominio"))
    roles['bici'] = detect_role(("bici", "bicicleta"))
    roles['hijos'] = detect_role(("hijo", "hija", "hijos"))

    return DetectedData(
        nombre=nombre,
        apellido=apellido,
        dni=dni,
        cuit=cuit,
        direccion=compact_spaces(direccion),
        monto=compact_spaces(monto),
        fecha=compact_spaces(fecha),
        telefono=compact_spaces(telefono),
        email=compact_spaces(email),
        razon_social=compact_spaces(razon_social),
        raw_text=normalized,
        roles=roles,
    )


def _ocr_fields_from_pdf_path(pdf_path: Path) -> dict[str, str]:
    """OCRa regiones específicas buscando labels (Domicilio) y extrae bloques post-label."""
    results: dict[str, str] = {"nombre": "", "apellido": "", "direccion": ""}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    # OCR la página completa para obtener texto y posiciones
                    img = page.to_image(resolution=300).original.convert("RGB")
                    full_text = pytesseract.image_to_string(img, lang="spa+eng")
                    full_lines = [l.strip() for l in full_text.splitlines() if l.strip()]
                    
                    # Buscar DOMICILIO y extraer bloque post-label
                    if not results["direccion"]:
                        for i, line in enumerate(full_lines):
                            if re.search(r"\bdomicilio\b|\bdom\b|direcci[oó]n", line, re.IGNORECASE):
                                # recopilar líneas siguientes hasta encontrar otra etiqueta
                                addr_parts = []
                                for j in range(i + 1, min(i + 8, len(full_lines))):
                                    next_line = full_lines[j]
                                    if re.search(r"\b(cuil|cuit|huella|firma|fecha|documento|dni|tel[eé]fono)\b", next_line, re.IGNORECASE):
                                        break
                                    if next_line.strip():
                                        addr_parts.append(next_line)
                                addr_candidate = " ".join(addr_parts).strip()
                                if addr_candidate and len(addr_candidate) > 5:
                                    results["direccion"] = addr_candidate
                                    break
                except Exception:
                    continue
    except Exception:
        return results

    return results


def _ocr_image_region(pil_img: Image.Image) -> str:
    try:
        # convertir a cv2, preprocesar y OCR
        import numpy as np

        cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        prep = _preprocess_cv_image(cv_img)
        txt = pytesseract.image_to_string(prep, lang="spa+eng", config="--oem 3 --psm 6")
        return normalize_text(txt)
    except Exception:
        try:
            return normalize_text(pytesseract.image_to_string(pil_img, lang="spa+eng"))
        except Exception:
            return ""


def detect_from_bytes(data: bytes, filename: str) -> DetectedData:
    """Extrae datos usando texto completo; para PDFs, prioriza OCR regional para dirección."""
    text = extract_text_from_bytes(data, filename)
    detected = extract_detected_data(text)

    # Para PDFs, usar OCR regional para dirección (más limpio y confiable)
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import tempfile, os

        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.write(data)
            tmp.flush()
            tmp.close()
            fields = _ocr_fields_from_pdf_path(Path(tmp.name))
            # si OCR regional encontró dirección, usar esa
            if fields.get("direccion") and len(fields.get("direccion", "")) >= 5:
                detected.direccion = fields.get("direccion")
        finally:
            try:
                if tmp and Path(tmp.name).exists():
                    os.unlink(tmp.name)
            except Exception:
                pass

    return detected
