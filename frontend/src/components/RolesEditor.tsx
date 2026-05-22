import React, { useState } from 'react'

type RolesEditorProps = {
  roles?: Record<string, string>
  onChangeRole: (key: string, value: string) => void
  onAddRole: (key: string) => void
}

type RolePreset = {
  key: string
  label: string
  placeholder: string
}

const PERSON_PRESETS: RolePreset[] = [
  { key: 'abogado', label: 'Abogado/a', placeholder: 'Nombre y apellido del abogado/a' },
  { key: 'asegurado', label: 'Asegurado/a', placeholder: 'Nombre y apellido del asegurado/a' },
  { key: 'tercero', label: 'Tercero', placeholder: 'Nombre y apellido del tercero' },
  { key: 'hijos', label: 'Hijos', placeholder: 'Cantidad o detalle de hijos' },
]

const VEHICLE_PRESETS: RolePreset[] = [
  { key: 'auto', label: 'Auto', placeholder: 'Marca, modelo y/o dominio del auto' },
  { key: 'bici', label: 'Bici', placeholder: 'Marca, color y/o detalle de la bici' },
]

export function RolesEditor({ roles = {}, onChangeRole, onAddRole }: RolesEditorProps) {
  const [newKey, setNewKey] = useState('')
  const usedKeys = new Set(Object.keys(roles).map((key) => key.toLowerCase()))
  const presetKeys = new Set([...PERSON_PRESETS, ...VEHICLE_PRESETS].map((item) => item.key))
  const extraRoles = Object.entries(roles).filter(([key]) => !presetKeys.has(key.toLowerCase()))

  const renderPreset = (preset: RolePreset) => (
    <label key={preset.key} className="flex w-full flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-3">
      <span className="text-sm font-semibold text-slate-600">{preset.label}</span>
      <input
        value={roles[preset.key] ?? ''}
        placeholder={preset.placeholder}
        onChange={(e) => onChangeRole(preset.key, e.target.value)}
        className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-base text-ink outline-none transition focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10"
      />
    </label>
  )

  return (
    <section className="rounded-3xl bg-white p-6 shadow-soft">
      <h2 className="text-xl font-semibold text-ink">Roles detectados</h2>
      <p className="mt-1 text-sm text-slate-500">Completá o corregí los campos clave para personas y vehículos.</p>

      <div className="mt-4 space-y-3">
        {Object.entries(roles).length === 0 && (
          <div className="text-sm text-slate-500">No se detectaron roles automáticamente.</div>
        )}

        <div>
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">Personas</h3>
          <div className="grid gap-3 sm:grid-cols-2">{PERSON_PRESETS.map(renderPreset)}</div>
        </div>

        <div className="pt-2">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">Vehiculos</h3>
          <div className="grid gap-3 sm:grid-cols-2">{VEHICLE_PRESETS.map(renderPreset)}</div>
        </div>

        {extraRoles.length > 0 && (
          <div className="pt-2">
            <h3 className="mb-2 text-sm font-semibold uppercase tracking-[0.14em] text-slate-500">Otros roles detectados</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              {extraRoles.map(([key, value]) => (
                <label key={key} className="flex w-full flex-col gap-2 rounded-2xl border border-slate-100 bg-slate-50 p-3">
                  <span className="text-sm font-semibold text-slate-600">{key}</span>
                  <input
                    value={value}
                    placeholder={`Valor para ${key}`}
                    onChange={(e) => onChangeRole(key, e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-base text-ink outline-none transition focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10"
                  />
                </label>
              ))}
            </div>
          </div>
        )}

        <div className="mt-3 flex gap-2">
          <input
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            placeholder="Agregar rol (ej. conductor)"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-base outline-none"
          />
          <button
            onClick={() => {
              const normalized = newKey.trim().toLowerCase()
              if (normalized && !usedKeys.has(normalized)) {
                onAddRole(normalized)
                setNewKey('')
              }
            }}
            className="rounded-2xl bg-accent px-4 py-3 text-white"
          >
            Agregar
          </button>
        </div>
      </div>
    </section>
  )
}
