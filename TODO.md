# TODO — Bot Convenios

Listado de tareas priorizadas para completar el proyecto y dejarlo operativo.

## Prioridad Alta

- [x] Instalar Homebrew y `tesseract` en macOS (global).
- [x] Verificar e instalar idioma `spa` para Tesseract.
- [x] Re-ejecutar OCR sobre `uploads/8917507cff37458fa9936081bdebb673.pdf` y comprobar salida.
- [x] Reiniciar backend (`uvicorn`) y validar endpoints `/api/process` y `/api/generate`.
- [ ] Añadir mensaje/descarga de imágenes de debug cuando OCR falle (frontend).

## Prioridad Media

- [ ] Mejorar renderizado de PDF a imagen: probar `pdf2image` o `pypdfium2` a 300–600 DPI.
- [x] Optimizar preprocesado de imágenes: CLAHE, umbral adaptativo, denoise y recorte de zonas de texto.
- [ ] Extraer regiones por contornos/heurísticas y ejecutar OCR por región.
- [ ] Añadir pruebas unitarias para `backend/services/ocr_service.py` con archivos de ejemplo.
 - [x] Extraer regiones por contornos/heurísticas y ejecutar OCR por región.
 - [x] Añadir pruebas unitarias para `backend/services/ocr_service.py` con archivos de ejemplo.

## Prioridad Baja

- [ ] Añadir comprobación automática de dependencias al arranque (tesseract, soffice).
- [ ] Documentar instalación en `README.md` (Homebrew, Tesseract, LibreOffice, Python deps).
- [x] Añadir E2E mínima: upload → process → edit → generate → download.
- [ ] Mejorar UI para roles detectados (abogado, asegurado, tercero, auto, bici, hijos).

## Tareas en curso

- [~] Integrar frontend: mostrar y editar mapping de plantillas (UI para confirmar/reasignar placeholders).
- [ ] Arreglar `tsconfig` para permitir `npm run build` (error `ignoreDeprecations`).
- [ ] Health checks / auto-arranque para Ollama y `soffice`.

## Notas y comandos útiles

- Instalar Homebrew (si falta):

```bash
 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- Instalar Tesseract:

```bash
brew install tesseract
tesseract --list-langs
```

- Descargar `spa` manualmente si falta:

```bash
mkdir -p "$(brew --prefix)/share/tessdata"
curl -L -o "$(brew --prefix)/share/tessdata/spa.traineddata" \
  https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata
```

---
Actualizá este archivo a medida que completas tareas.
