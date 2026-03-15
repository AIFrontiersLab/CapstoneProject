import { useCallback, useState } from 'react'
import { Upload, FileText, Loader2 } from 'lucide-react'
import { uploadDocument } from '../lib/api'
import type { UploadResponse } from '../types'

interface UploadZoneProps {
  onUploaded?: (res: UploadResponse) => void
  onError?: (err: string) => void
}

export default function UploadZone({ onUploaded, onError }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const f = e.dataTransfer.files[0]
      if (!f) return
      setFile(f)
      setUploading(true)
      try {
        const res = await uploadDocument(f)
        onUploaded?.(res)
        setFile(null)
      } catch (err) {
        onError?.(err instanceof Error ? err.message : 'Upload failed')
      } finally {
        setUploading(false)
      }
    },
    [onUploaded, onError]
  )

  const handleFileSelect = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0]
      if (!f) return
      setFile(f)
      setUploading(true)
      try {
        const res = await uploadDocument(f)
        onUploaded?.(res)
        setFile(null)
      } catch (err) {
        onError?.(err instanceof Error ? err.message : 'Upload failed')
      } finally {
        setUploading(false)
      }
      e.target.value = ''
    },
    [onUploaded, onError]
  )

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`
        border-2 border-dashed rounded-2xl p-8 text-center transition-all duration-200
        ${dragging ? 'border-sky-400 bg-sky-50 shadow-lg' : 'border-slate-300 hover:border-sky-400 hover:bg-slate-50'}
      `}
    >
      <input
        type="file"
        accept=".pdf,.txt,.csv,.xlsx"
        onChange={handleFileSelect}
        className="hidden"
        id="file-upload"
        disabled={uploading}
      />
      <label htmlFor="file-upload" className="cursor-pointer block">
        {uploading ? (
          <Loader2 className="w-12 h-12 mx-auto text-sky-500 animate-spin mb-3" />
        ) : (
          <Upload className="w-12 h-12 mx-auto text-sky-500 mb-3" />
        )}
        <p className="text-zinc-700 font-medium">
          {uploading ? 'Uploading & indexing…' : 'Drop a file here or click to browse'}
        </p>
        <p className="text-zinc-500 text-sm mt-1">PDF, TXT, CSV, or XLSX (max 25 MB)</p>
        {file && !uploading && (
          <p className="mt-2 text-zinc-600 text-sm flex items-center justify-center gap-2">
            <FileText className="w-4 h-4" /> {file.name}
          </p>
        )}
      </label>
    </div>
  )
}
