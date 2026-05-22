import type { TemplateFieldMapping } from '../types'

type SourceOption = {
  value: string
  label: string
}

type TemplateMappingEditorProps = {
  templateName: string
  templateMapping?: TemplateFieldMapping
  selectedSources: Record<string, string>
  sourceOptions: SourceOption[]
  onChangeSource: (placeholder: string, source: string) => void
}

export function TemplateMappingEditor({
  templateName,
  templateMapping,
  selectedSources,
  sourceOptions,
  onChangeSource,
}: TemplateMappingEditorProps) {
  if (!templateMapping) return null

  return (
    <div className="mt-4 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-slate-700">Mapping de placeholders</h3>
          <p className="text-xs text-slate-500">Plantilla: {templateName}</p>
        </div>
      </div>

      {templateMapping.placeholders.length === 0 ? (
        <p className="mt-3 text-slate-500">No se detectaron placeholders en esta plantilla.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {templateMapping.placeholders.map((placeholder) => {
            const row = templateMapping.mapping[placeholder]
            const inferred = row?.inferred?.field ?? ''
            const confidence = row?.inferred?.confidence ?? 0
            return (
              <li key={placeholder} className="rounded-xl border border-slate-200 bg-white p-3">
                <div className="mb-2 flex items-start justify-between gap-3">
                  <div>
                    <div className="font-semibold text-ink">{placeholder}</div>
                    <div className="text-xs text-slate-500">
                      Sugerido: {inferred || 'sin asignar'}
                      {inferred ? ` (${Math.round(confidence * 100)}%)` : ''}
                    </div>
                  </div>
                </div>

                <label className="block">
                  <span className="mb-1 block text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Usar valor de</span>
                  <select
                    value={selectedSources[placeholder] ?? inferred}
                    onChange={(event) => onChangeSource(placeholder, event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 outline-none transition focus:border-accent focus:ring-4 focus:ring-accent/10"
                  >
                    <option value="">Sin asignar</option>
                    {sourceOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                {row?.snippet ? <p className="mt-2 line-clamp-2 text-xs text-slate-500">{row.snippet}</p> : null}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
