import type { ChangeEvent, DragEvent } from 'react'

type DropzoneProps = {
  files: File[]
  onFilesSelected: (files: File[]) => void
}

const acceptedExtensions = ['.jpg', '.jpeg', '.png', '.pdf']

export function Dropzone({ files, onFilesSelected }: DropzoneProps) {
  const handleInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = Array.from(event.target.files ?? [])
    onFilesSelected(selected)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const dropped = Array.from(event.dataTransfer.files ?? [])
    onFilesSelected(dropped)
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(event) => event.preventDefault()}
      className="rounded-3xl border-2 border-dashed border-accent/30 bg-white/80 p-6 shadow-soft transition hover:border-accent/60"
    >
      <div className="flex flex-col gap-4 text-center">
        <div>
          <p className="text-lg font-semibold text-ink">Arrastrá tus archivos acá</p>
          <p className="mt-2 text-sm text-slate-600">Fotos JPG/PNG o PDFs. Podés subir varios documentos a la vez.</p>
        </div>

        <label className="mx-auto inline-flex cursor-pointer items-center justify-center rounded-2xl bg-accent px-6 py-3 text-base font-semibold text-white shadow-lg shadow-accent/20 transition hover:-translate-y-0.5 hover:bg-[#1857bb]">
          <span>Subir archivos</span>
          <input
            type="file"
            multiple
            accept={acceptedExtensions.join(',')}
            className="hidden"
            onChange={handleInputChange}
          />
        </label>

        <div className="text-sm text-slate-500">
          Formatos permitidos: {acceptedExtensions.join(' · ')}
        </div>

        {files.length > 0 && (
          <ul className="mx-auto max-w-xl space-y-2 text-left text-sm text-slate-700">
            {files.map((file) => (
              <li key={`${file.name}-${file.size}`} className="rounded-xl bg-slate-50 px-4 py-3">
                {file.name}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
