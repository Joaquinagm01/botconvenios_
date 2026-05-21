import type { GenerateResult } from '../types'

type ResultPanelProps = {
  result: GenerateResult | null
}

export function ResultPanel({ result }: ResultPanelProps) {
  if (!result) return null

  return (
    <section className="rounded-3xl border border-success/20 bg-white p-6 shadow-soft">
      <h2 className="text-xl font-semibold text-ink">Documento generado</h2>
      <p className="mt-2 text-sm text-slate-500">Ya podés descargar los archivos finales.</p>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row">
        <a
          href={result.docx_url}
          className="rounded-2xl bg-ink px-5 py-3 text-center font-semibold text-white transition hover:bg-slate-800"
        >
          Descargar DOCX
        </a>
        <a
          href={result.pdf_url}
          className="rounded-2xl bg-accent px-5 py-3 text-center font-semibold text-white transition hover:bg-[#1857bb]"
        >
          Descargar PDF
        </a>
      </div>

      {result.preview_text && <p className="mt-4 text-sm text-slate-600">{result.preview_text}</p>}
    </section>
  )
}
