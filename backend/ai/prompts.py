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
