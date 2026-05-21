import React, { useState } from 'react'

type RolesEditorProps = {
  roles?: Record<string, string>
  onChangeRole: (key: string, value: string) => void
  onAddRole: (key: string) => void
}

export function RolesEditor({ roles = {}, onChangeRole, onAddRole }: RolesEditorProps) {
  const [newKey, setNewKey] = useState('')

  return (
    <section className="rounded-3xl bg-white p-6 shadow-soft">
      <h2 className="text-xl font-semibold text-ink">Roles detectados</h2>
      <p className="mt-1 text-sm text-slate-500">Abogado, asegurado, tercero, auto, bici, hijos, etc.</p>

      <div className="mt-4 space-y-3">
        {Object.entries(roles).length === 0 && (
          <div className="text-sm text-slate-500">No se detectaron roles automáticamente.</div>
        )}

        {Object.entries(roles).map(([key, value]) => (
          <label key={key} className="flex w-full flex-col gap-2">
            <span className="text-sm font-medium text-slate-600">{key}</span>
            <input
              value={value}
              placeholder={`Valor para ${key}`}
              onChange={(e) => onChangeRole(key, e.target.value)}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-base text-ink outline-none transition focus:border-accent focus:bg-white focus:ring-4 focus:ring-accent/10"
            />
          </label>
        ))}

        <div className="mt-3 flex gap-2">
          <input
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            placeholder="Agregar rol (ej. conductor)"
            className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-base outline-none"
          />
          <button
            onClick={() => {
              if (newKey.trim()) {
                onAddRole(newKey.trim())
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
