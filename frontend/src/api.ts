import type { DetectedData, GenerateResult, TemplateInfo } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || 'No fue posible completar la operación')
  }
  return response.json() as Promise<T>
}

export async function fetchTemplates(): Promise<TemplateInfo[]> {
  const response = await fetch(`${API_BASE}/api/templates`)
  return handleResponse<TemplateInfo[]>(response)
}

export async function processFiles(files: File[]): Promise<DetectedData> {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))

  const response = await fetch(`${API_BASE}/api/process`, {
    method: 'POST',
    body: formData,
  })

  const payload = await handleResponse<{ detected: DetectedData }>(response)
  return payload.detected
}

export async function generateDocument(templateName: string, data: DetectedData): Promise<GenerateResult> {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ template_name: templateName, data }),
  })

  return handleResponse<GenerateResult>(response)
}
