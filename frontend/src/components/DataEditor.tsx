import type { DetectedData } from '../types'

type DataEditorProps = {
  data: DetectedData
  onChange: (field: keyof DetectedData, value: string) => void
}

const fields: Array<{ key: keyof DetectedData; label: string; placeholder: string }> = [
  { key: 'nombre', label: 'Nombre', placeholder: 'Nombre' },
  { key: 'apellido', label: 'Apellido', placeholder: 'Apellido' },
  { key: 'dni', label: 'DNI', placeholder: 'DNI' },
  { key: 'cuit', label: 'CUIT', placeholder: 'CUIT' },
  { key: 'direccion', label: 'Dirección', placeholder: 'Dirección' },
  { key: 'monto', label: 'Monto', placeholder: 'Monto' },
  { key: 'fecha', label: 'Fecha', placeholder: 'Fecha' },
  { key: 'telefono', label: 'Teléfono', placeholder: 'Teléfono' },
  { key: 'email', label: 'Email', placeholder: 'Email' },
  { key: 'razon_social', label: 'Razón social', placeholder: 'Razón social' },
]

export function DataEditor({ data, onChange }: DataEditorProps) {
  return (
    <section className="rounded-3xl bg-white p-6 shadow-soft">
      <div className="mb-5">
        <h2 className="text-xl font-semibold text-ink">Datos detectados</h2>
        <p className="mt-1 text-sm text-slate-500">Revisá y corregí antes de generar el convenio.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {fields.map((field) => (
          <label key={field.key as string} className="space-y-2">
            <span className="text-sm font-medium text-slate-600">{field.label}</span>
            <input
              value={data[field.key]}
              placeholder={field.placeholder}
              onChange={(event) => onChange(field.key, event.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-ink outline-none transition focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10"
            />
          </label>
        ))}
      </div>
    </section>
  )
}
