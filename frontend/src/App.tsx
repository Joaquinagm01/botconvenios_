import { useEffect, useState } from 'react'
import { ActionBar } from './components/ActionBar'
import { DataEditor } from './components/DataEditor'
import { Dropzone } from './components/Dropzone'
import { ResultPanel } from './components/ResultPanel'
import { TemplateSelect } from './components/TemplateSelect'
import { fetchTemplates, fetchTemplateFields, generateDocument, processFiles } from './api'
import type { DetectedData, GenerateResult, TemplateFieldMappingByTemplate, TemplateInfo } from './types'
import { RolesEditor } from './components/RolesEditor'
import { TemplateMappingEditor } from './components/TemplateMappingEditor'

const emptyData: DetectedData = {
  nombre: '',
  apellido: '',
  dni: '',
  cuit: '',
  direccion: '',
  monto: '',
  fecha: '',
  telefono: '',
  email: '',
  razon_social: '',
  raw_text: '',
  roles: {},
}

function App() {
  const [files, setFiles] = useState<File[]>([])
  const [templates, setTemplates] = useState<TemplateInfo[]>([])
  const [templateFields, setTemplateFields] = useState<TemplateFieldMappingByTemplate>({})
  const [templateMappingSources, setTemplateMappingSources] = useState<Record<string, string>>({})
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [data, setData] = useState<DetectedData>(emptyData)
  const [result, setResult] = useState<GenerateResult | null>(null)
  const [loadingTemplates, setLoadingTemplates] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    setLoadingTemplates(true)
    Promise.all([fetchTemplates(), fetchTemplateFields()])
      .then(([items, fields]) => {
        setTemplates(items)
        setTemplateFields(fields)
        if (items[0]) setSelectedTemplate(items[0].filename)
      })
      .catch((templateError: unknown) => {
        setError(templateError instanceof Error ? templateError.message : 'No se pudieron cargar las plantillas.')
      })
      .finally(() => setLoadingTemplates(false))
  }, [])

  useEffect(() => {
    if (!selectedTemplate || !templateFields[selectedTemplate]) {
      setTemplateMappingSources({})
      return
    }

    const defaults: Record<string, string> = {}
    for (const placeholder of templateFields[selectedTemplate].placeholders) {
      const inferred = templateFields[selectedTemplate].mapping[placeholder]?.inferred?.field
      if (inferred) {
        defaults[placeholder] = inferred
      }
    }
    setTemplateMappingSources(defaults)
  }, [selectedTemplate, templateFields])

  const handleProcess = async () => {
    if (files.length === 0) {
      setError('Primero subí al menos un archivo.')
      return
    }

    setProcessing(true)
    setError('')
    setMessage('Procesando archivos...')
    try {
      const detected = await processFiles(files)
      setData({ ...emptyData, ...detected, roles: detected.roles ?? {} })
      setMessage('Datos detectados. Revisa y corrige si hace falta.')
    } catch (processError: unknown) {
      setError(processError instanceof Error ? processError.message : 'No se pudo procesar el archivo.')
      setMessage('')
    } finally {
      setProcessing(false)
    }
  }

  const handleGenerate = async () => {
    if (!selectedTemplate) {
      setError('Elegí una plantilla antes de generar.')
      return
    }

    const dataWithTemplateAliases: Record<string, string | Record<string, string>> = {
      ...data,
      roles: { ...(data.roles ?? {}) },
    }

    // Alias de placeholders no estandar: permite completar plantillas con llaves numericas u otros tokens.
    for (const [placeholder, source] of Object.entries(templateMappingSources)) {
      if (!source) continue

      if (source.startsWith('roles.')) {
        const roleKey = source.replace('roles.', '')
        const roleValue = data.roles?.[roleKey] ?? ''
        dataWithTemplateAliases[placeholder] = roleValue
        continue
      }

      const value = data[source as keyof DetectedData]
      dataWithTemplateAliases[placeholder] = typeof value === 'string' ? value : ''
    }

    setGenerating(true)
    setError('')
    setMessage('Generando documento...')
    try {
      const generated = await generateDocument(selectedTemplate, dataWithTemplateAliases as DetectedData)
      setResult(generated)
      setMessage('Documento listo para descargar.')
    } catch (generateError: unknown) {
      setError(generateError instanceof Error ? generateError.message : 'No se pudo generar el convenio.')
      setMessage('')
    } finally {
      setGenerating(false)
    }
  }

  const roleKeys = Object.keys(data.roles ?? {})
  const sourceOptions = [
    { value: 'nombre', label: 'Nombre' },
    { value: 'apellido', label: 'Apellido' },
    { value: 'dni', label: 'DNI' },
    { value: 'cuit', label: 'CUIT' },
    { value: 'direccion', label: 'Direccion' },
    { value: 'monto', label: 'Monto' },
    { value: 'fecha', label: 'Fecha' },
    { value: 'telefono', label: 'Telefono' },
    { value: 'email', label: 'Email' },
    { value: 'razon_social', label: 'Razon social' },
    ...roleKeys.map((key) => ({ value: `roles.${key}`, label: `Rol: ${key}` })),
  ]

  return (
    <main className="min-h-screen bg-hero text-ink">
      <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-8 px-4 py-6 sm:px-6 lg:px-8">
        <header className="animate-fadeUp rounded-[2rem] border border-white/60 bg-white/80 px-6 py-5 shadow-soft backdrop-blur">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Local · Gratis · Open Source</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">Bot Convenios</h1>
              <p className="mt-2 max-w-2xl text-base text-slate-600">
                Subí fotos o PDFs, corregí los datos detectados y descargá el convenio final sin depender de internet.
              </p>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="space-y-6">
            <Dropzone files={files} onFilesSelected={setFiles} />

            <div className="rounded-3xl bg-white p-6 shadow-soft">
              <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-ink">Elegir plantilla</h2>
                  <p className="text-sm text-slate-500">Las plantillas `.docx` se leen desde la carpeta local plantillas/.</p>
                </div>
                {loadingTemplates && <span className="text-sm text-accent">Cargando...</span>}
              </div>
              <TemplateSelect templates={templates} value={selectedTemplate} onChange={setSelectedTemplate} />
              {selectedTemplate && templateFields[selectedTemplate] && (
                <TemplateMappingEditor
                  templateName={selectedTemplate}
                  templateMapping={templateFields[selectedTemplate]}
                  selectedSources={templateMappingSources}
                  sourceOptions={sourceOptions}
                  onChangeSource={(placeholder, source) =>
                    setTemplateMappingSources((current) => ({ ...current, [placeholder]: source }))
                  }
                />
              )}
            </div>

            <DataEditor data={data} onChange={(field, value) => setData((current) => ({ ...current, [field]: value }))} />

            <RolesEditor
              roles={data.roles}
              onChangeRole={(key, value) => setData((current) => ({ ...current, roles: { ...(current.roles ?? {}), [key]: value } }))}
              onAddRole={(key) => setData((current) => ({ ...current, roles: { ...(current.roles ?? {}), [key]: '' } }))}
            />

            <ActionBar
              onProcess={handleProcess}
              onGenerate={handleGenerate}
              processing={processing}
              generating={generating}
              canGenerate={Boolean(selectedTemplate)}
            />
          </div>

          <aside className="space-y-6">
            <section className="rounded-3xl bg-white p-6 shadow-soft">
              <h2 className="text-xl font-semibold text-ink">Vista previa</h2>
              <p className="mt-2 text-sm text-slate-500">Resumen rápido de los datos detectados.</p>
              <dl className="mt-5 space-y-3 text-sm">
                {[
                  ['Nombre', data.nombre],
                  ['Apellido', data.apellido],
                  ['DNI', data.dni],
                  ['CUIT', data.cuit],
                  ['Monto', data.monto],
                  ['Fecha', data.fecha],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-start justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3">
                    <dt className="font-medium text-slate-500">{label}</dt>
                    <dd className="text-right font-semibold text-ink">{value || '—'}</dd>
                  </div>
                ))}
                {data.roles && Object.entries(data.roles).map(([k,v]) => (
                  <div key={`role-${k}`} className="flex items-start justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3">
                    <dt className="font-medium text-slate-500">{k}</dt>
                    <dd className="text-right font-semibold text-ink">{v || '—'}</dd>
                  </div>
                ))}
              </dl>
            </section>

            {message && (
              <section className="rounded-3xl border border-accent/20 bg-accent/5 p-5 text-accent">
                {message}
              </section>
            )}

            {error && (
              <section className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-rose-700">
                {error}
              </section>
            )}

            <ResultPanel result={result} />
          </aside>
        </section>
      </div>
    </main>
  )
}

export default App
