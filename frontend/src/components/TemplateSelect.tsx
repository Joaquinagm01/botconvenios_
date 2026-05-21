import type { TemplateInfo } from '../types'

type TemplateSelectProps = {
  templates: TemplateInfo[]
  value: string
  onChange: (value: string) => void
}

export function TemplateSelect({ templates, value, onChange }: TemplateSelectProps) {
  return (
    <label className="block space-y-2">
      <span className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Plantilla</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-4 text-base text-ink shadow-sm outline-none transition focus:border-accent focus:ring-4 focus:ring-accent/10"
      >
        <option value="">Elegir una plantilla</option>
        {templates.map((template) => (
          <option key={template.filename} value={template.filename}>
            {template.name}
          </option>
        ))}
      </select>
    </label>
  )
}
