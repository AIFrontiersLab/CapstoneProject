import { useState } from 'react'
import UploadZone from '../components/UploadZone'
import type { UploadResponse } from '../types'

export default function UploadPage() {
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleUploaded = (res: UploadResponse) => {
    setMessage({
      type: 'success',
      text: `"${res.file_name}" uploaded and indexed (${res.chunk_count} chunks).`,
    })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleError = (err: string) => {
    setMessage({ type: 'error', text: err })
    setTimeout(() => setMessage(null), 6000)
  }

  return (
    <div>
      <div className="glass-panel p-6 md:p-8">
        <h2 className="text-2xl font-semibold text-zinc-800 mb-2 tracking-tight">Upload documents</h2>
        <p className="text-zinc-600 mb-6 text-sm leading-relaxed">
          Upload PDF, TXT, CSV, or Excel files. They will be parsed, chunked, embedded, and indexed for Q&A.
        </p>
        {message && (
          <div
            className={`mb-4 px-4 py-3 rounded-xl border ${
              message.type === 'success'
                ? 'bg-sky-50 border-sky-200 text-sky-800'
                : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {message.text}
          </div>
        )}
        <UploadZone onUploaded={handleUploaded} onError={handleError} />
      </div>
    </div>
  )
}
