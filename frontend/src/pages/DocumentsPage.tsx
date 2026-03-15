import { useEffect, useState } from 'react'
import { listDocuments } from '../lib/api'
import type { DocumentListItem } from '../types'
import { FileText, Loader2 } from 'lucide-react'

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listDocuments()
      .then(setDocs)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  const statusColor = (status: string) => {
    if (status === 'completed') return 'text-zinc-600'
    if (status === 'failed') return 'text-red-600'
    return 'text-amber-600'
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-zinc-600">
        <Loader2 className="w-5 h-5 animate-spin" />
        Loading documents…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">
        {error}
      </div>
    )
  }

  return (
    <div>
      <div className="glass-panel p-6 md:p-8">
        <h2 className="text-2xl font-semibold text-zinc-800 mb-2 tracking-tight">Uploaded documents</h2>
        <p className="text-zinc-600 mb-6 text-sm leading-relaxed">
          All documents that have been uploaded and indexed for semantic search.
        </p>
        {docs.length === 0 ? (
          <p className="text-zinc-500">No documents yet. Upload some from the Upload page.</p>
        ) : (
          <ul className="space-y-3">
            {docs.map((d) => (
              <li
                key={d.document_id}
                className="surface-card flex items-center gap-4 p-4"
              >
              <FileText className="w-5 h-5 text-zinc-500 shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="font-medium text-zinc-800 truncate">{d.file_name}</p>
                <p className="text-sm text-zinc-500">
                  {d.chunk_count} chunks · {d.file_type} ·{' '}
                  <span className={statusColor(d.status)}>{d.status}</span>
                </p>
              </div>
              <span className="text-xs text-zinc-500 shrink-0">
                {new Date(d.created_at).toLocaleDateString()}
              </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
