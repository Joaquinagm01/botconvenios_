type ActionBarProps = {
  onProcess: () => void
  onGenerate: () => void
  processing: boolean
  generating: boolean
  canGenerate: boolean
}

export function ActionBar({ onProcess, onGenerate, processing, generating, canGenerate }: ActionBarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <button
        type="button"
        onClick={onProcess}
        disabled={processing}
        className="rounded-2xl border border-accent/20 bg-white px-6 py-4 text-lg font-semibold text-accent shadow-sm transition hover:border-accent hover:bg-accent/5 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {processing ? 'Procesando...' : 'Procesar archivos'}
      </button>
      <button
        type="button"
        onClick={onGenerate}
        disabled={!canGenerate || generating}
        className="rounded-2xl bg-success px-6 py-4 text-lg font-semibold text-white shadow-lg shadow-success/20 transition hover:-translate-y-0.5 hover:bg-[#0d8a4d] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {generating ? 'Generando...' : 'Generar convenio'}
      </button>
    </div>
  )
}
