export type DetectedData = {
  nombre: string
  apellido: string
  dni: string
  cuit: string
  direccion: string
  monto: string
  fecha: string
  telefono: string
  email: string
  razon_social: string
  raw_text: string
  roles?: Record<string, string>
}

export type TemplateInfo = {
  name: string
  filename: string
}

export type TemplateFieldMapping = {
  placeholders: string[]
  mapping: Record<string, { snippet: string | null; inferred: { field: string | null; confidence: number; reason: string } }>
}

export type GenerateResult = {
  docx_name: string
  pdf_name: string
  docx_url: string
  pdf_url: string
  preview_text?: string | null
}
