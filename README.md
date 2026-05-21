# Bot Convenios

Aplicación **100% LOCAL, GRATUITA y OPEN SOURCE** para generación automática de convenios y documentos legales a partir de OCR y plantillas DOCX.

## 🎯 Características

✅ **Extracción OCR de documentos**
- Procesa fotos (JPG/PNG) y PDFs scaneados
- Tesseract OCR con preprocesado inteligente (CLAHE, bilateral filter, adaptive threshold)
- Machine Readable Zone (MRZ) parsing para documentos de identidad
- OCR regional para campos específicos (ej: dirección)

✅ **Detección inteligente de datos**
- Nombre, apellido, DNI, CUIT, dirección, teléfono, email, monto, fecha
- Detección de roles: abogado, asegurado, tercero, auto, bici, hijos
- Normalización y limpieza de datos

✅ **Generación de documentos**
- Carga automática de plantillas `.docx` desde carpeta `plantillas/`
- Reemplazo de placeholders `{{nombre}}`, `{{apellido}}`, etc.
- Exportación a DOCX y PDF (via LibreOffice)

✅ **Interfaz amigable**
- Diseño simple, apto para personas mayores
- Botones grandes, colores claros, instrucciones directas
- Edición de datos antes de generar

✅ **100% Local y Seguro**
- Sin APIs externas
- Sin servicios pagos
- Sin almacenamiento en la nube
- Los uploads se procesan en memoria, sin guardar en disco

## 📋 Requisitos

- **macOS** (Intel o Apple Silicon)
- **Python 3.14+**
- **Homebrew**
- **Node.js 18+** (para frontend)

## Instalación del backend

```bash
pip3 install -r requirements.txt
```

Si Tesseract no queda en la ruta por defecto, define:

```bash
export TESSERACT_CMD=/opt/homebrew/bin/tesseract
```

## Instalar dependencias del frontend

```bash
cd frontend
npm install
```

## Ejecutar en local

Terminal 1:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

## Plantillas

Coloca archivos `.docx` dentro de `plantillas/` usando placeholders como:

- `{{nombre}}`
- `{{apellido}}`
- `{{dni}}`
- `{{cuit}}`
- `{{direccion}}`
- `{{monto}}`
- `{{fecha}}`

También se aceptan plantillas `.doc` y se convierten localmente a `.docx` usando LibreOffice antes de generar el convenio.

## Flujo de uso

1. Abrir la app local.
2. Subir fotos o PDFs.
3. Revisar los datos detectados.
4. Elegir la plantilla.
5. Corregir los campos si hace falta.
6. Generar y descargar DOCX y PDF.

## Notas

- Todo el procesamiento ocurre localmente.
- No se usan APIs pagas ni servicios externos.
- Si LibreOffice no está disponible, el DOCX se genera pero la conversión a PDF fallará hasta instalarlo.

## 📚 Registro detallado de lo realizado (resumen técnico)

Este proyecto fue desarrollado y optimizado con foco en precisión de extracción y privacidad (procesamiento 100% local). A continuación se documenta qué se hizo y por qué:

- Entorno y dependencias:
	- Instalado y configurado `tesseract` (Homebrew) y las dependencias Python listadas en `requirements.txt`.
	- `LibreOffice` se utiliza para convertir `DOCX` a `PDF` en `backend.services.document_service`.

- Procesamiento en memoria y privacidad:
	- Las subidas por el endpoint `/api/process` se procesan en memoria sin persistir los archivos recibidos.
	- Se evitó dejar imágenes de depuración en disco; cuando se generan, se eliminan inmediatamente.

- OCR y extracción de texto:
	- `pdfplumber` y `PyPDF2` se usan para extracción de texto como primera vía; si el resultado es pobre, se renderiza la página a imagen (600 DPI) y se aplica OCR con `pytesseract`.
	- Preprocesado con OpenCV: escalado, `CLAHE`, filtro bilateral, umbral adaptativo y `medianBlur` para mejorar calidad de OCR.
	- Se probaron múltiples configuraciones de Tesseract (`--oem`, `--psm`) para mejorar reconocimiento en distintas zonas.

- Heurísticas y componentes clave implementados:
	- `backend.services.ocr_service._parse_mrz`: parsing de la MRZ para extraer `nombre`, `apellido` y `dni` de documentos argentinos con alta fiabilidad.
	- `backend.services.ocr_service._ocr_pdf_as_images` y `_ocr_pdf_as_images_bytes`: renderizado y OCR por página con preprocesado avanzado.
	- `backend.services.ocr_service._ocr_fields_from_pdf_path`: OCR regional que busca la etiqueta `DOMICILIO` y extrae el bloque de dirección siguiente.
	- `backend.services.ocr_service._clean_address`: limpieza y normalización de direcciones, eliminando tokens basura (1–2 letras) excepto abreviaturas comunes.

- Correcciones realizadas (bugs y refactors):
	- Eliminado código duplicado/erróneo que provocaba `SyntaxError` dentro de `ocr_service.py`.
	- Corregida la indentación y retorno del endpoint `/api/process` en `backend/api.py` para asegurarse de que siempre devuelve `ProcessResponse`.
	- Asegurado el CORS mediante `CORSMiddleware` en `backend/main.py` para permitir llamadas desde el frontend local.

- Flujo E2E probado y validado:
	- Backend en `http://localhost:8000`, frontend en `http://localhost:5173`.
	- Prueba completa: upload del PDF de DNI → extracción (nombre/apellido/DNI/dirección/teléfono) → corrección manual en UI → selección de plantilla → generación de `DOCX` y `PDF`.
	- Archivos generados guardados en `documentos_generados/`.

- Resultado de ejemplo (DNI de prueba):
	- `nombre`: `JOAQUINA ESPERANZA`
	- `apellido`: `GOMEZ MANNA`
	- `dni`: `43713339`
	- `cuit`: `00706686056`
	- `dirección`: `SANTA rE 1A 2468 - ROSARIO - ROSA`

- Buenas prácticas y próximos pasos recomendados:
	- Añadir pruebas unitarias para `backend/services/ocr_service.py` (pendiente).
	- Implementar limpieza automática de `uploads/` en modo test o agregar TTL para evitar acumulación en instalaciones locales.
	- Considerar agregar un modo "solo memoria" estricto que rechace guardar cualquier archivo auxiliar incluso en `uploads/`.

Si querés, genero un `CHANGELOG.md` con este mismo contenido o extraigo un resumen más corto para la página principal.

## 🧠 Integración IA local (Ollama)

Instrucciones rápidas para correr Ollama local y usar modelos off-line:

- Instalar Ollama (macOS / Apple Silicon):
	1. Descargar desde https://ollama.com y seguir instrucciones para macOS.
	2. Iniciar el daemon local: `ollama start`.
	3. Instalar un modelo compatible, por ejemplo `ollama pull phi4/phi4-mini`.

- Uso desde Python (cliente incluido):
	- `backend/ai/ollama_client.py` contiene un cliente mínimo que usa `requests` contra `http://localhost:11434/api/generate`.
	- Ejemplo rápido:

```python
from backend.ai.ollama_client import OllamaClient
client = OllamaClient()
resp = client.generate_json('phi4-mini', 'Extrae nombre y dni del siguiente texto: ...')
print(resp)
```

Nota: Si Ollama no está instalado, el pipeline fallará al intentar llamar al servicio; se debe instalar localmente según la plataforma.

## 🧩 Integración propuesta (resumen)

Se agregó un pipeline modular en `backend/integrations/pipeline.py` que combina:

- Preprocesado avanzado: `backend/utils/image_preproc.py` (CLAHE, bilateral, deskew, sharpen, adaptive threshold).
- OCR híbrido: `backend/ocr/hybrid_ocr.py` (Tesseract + EasyOCR) con fusión básica.
- Normalización fuzzy: `backend/parsers/address_normalizer.py` (rapidfuzz + unidecode).
- Validadores: `backend/validators/validators.py` (DNI, CUIT, email, teléfono, fecha).
- Cliente Ollama: `backend/ai/ollama_client.py` y `backend/ai/prompts.py` (prompts JSON-first).

Para integrar el pipeline con el endpoint `/api/process`, llama a `process_document_bytes()` con los bytes subidos y el modelo deseado.

