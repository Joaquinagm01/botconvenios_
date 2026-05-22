PROMPT_JSON_HEADER = (
    "Eres un asistente local que recibe texto extraído por OCR de documentos argentinos. "
    "Devuelve SOLO JSON válido con campos y confianza entre 0 y 1."
)

PROMPT_DNI = (
    PROMPT_JSON_HEADER +
    "\nTarea: extrae 'nombre', 'apellido', 'dni' y 'sexo' si están, corrige errores tipográficos y normaliza mayúsculas. "
    "Si hay dudas, intenta inferir el valor y asigna 'confidence' adecuado. Responde exclusivamente con JSON: {\"nombre\":{\"valor\":...,\"confidence\":...}, ...}."
)

PROMPT_ADDRESS = (
    PROMPT_JSON_HEADER +
    "\nTarea: normaliza la dirección postal del fragmento de texto OCR. Extrae 'calle', 'numero', 'piso', 'departamento', 'ciudad', 'provincia', 'codigo_postal'. "
    "Corrige errores comunes (e.j. 'rE' -> 'FE'). Responde exclusivamente con JSON y las claves indicadas, completando con null cuando no aplique. Añade 'confidence' por campo."
)

PROMPT_DOCUMENT = (
    PROMPT_JSON_HEADER +
    "\nTarea: a partir del texto OCR extraído del documento, devuelve un JSON con los campos: nombre, apellido, dni, cuit, direccion_texto, telefono, email, fecha, monto. "
    "Por cada campo devuelve {\"valor\":..., \"confidence\":0.00}. No agregues texto fuera del JSON."
)


PROMPT_DOCUMENT_V2 = (
    PROMPT_JSON_HEADER
    + "\nINSTRUCCIONES:\n"
    + "- Recibe dos entradas: REGION_CANDIDATES (un JSON con fragmentos detectados por región) y OCR_TEXT (todo el texto fusionado).\n"
    + "- Devuelve SOLO JSON válido con la siguiente estructura exacta:\n"
    + "{\n  \"nombre\": {\"valor\": string|null, \"confidence\": number, \"source\": string|null},\n  \"apellido\": {...},\n  \"dni\": {...},\n  \"cuit\": {...},\n  \"direccion_texto\": {...},\n  \"telefono\": {...},\n  \"email\": {...},\n  \"fecha\": {...},\n  \"monto\": {...}\n}\n"
    + "- Para cada campo, devuelva: 'valor' (string o null), 'confidence' (0.0-1.0) y 'source' indicando 'region:<name>' o 'ocr' o 'mrz' según corresponda.\n"
    + "- Si un valor proviene de REGION_CANDIDATES use source 'region:<key>' y para MRZ use 'mrz'.\n"
    + "- No añadas explicaciones ni texto fuera del JSON. Si no hay dato, pon null y confidence 0.0.\n"
    + "- Prioriza precisión sobre completitud: si dudás, pon null con confidence baja.\n"
    + "\nEjemplo de respuesta válida:\n{\n  \"nombre\": {\"valor\": \"JUAN\", \"confidence\": 0.95, \"source\": \"mrz\"},\n  \"apellido\": {\"valor\": \"PEREZ\", \"confidence\": 0.95, \"source\": \"mrz\"},\n  \"dni\": {\"valor\": \"12345678\", \"confidence\": 0.98, \"source\": \"mrz\"},\n  \"cuit\": {\"valor\": null, \"confidence\": 0.0, \"source\": null}\n}\n"
)
