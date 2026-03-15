import type { QueryResponse, ExecutionSummary, Citation, RetrievedChunk } from '../types'
import { FileText, ChevronDown, ChevronRight } from 'lucide-react'
import { useState } from 'react'

interface AnswerPanelProps {
  data: QueryResponse | null
  loading: boolean
  useAgent?: boolean
}

export default function AnswerPanel({ data, loading, useAgent }: AnswerPanelProps) {
  const [chunksOpen, setChunksOpen] = useState(false)

  if (loading) {
    return (
      <div className="surface-card p-6 flex items-center gap-3 text-sky-700">
        <div className="w-5 h-5 border-2 border-sky-400 border-t-cyan-200 rounded-full animate-spin" />
        <span>Retrieving and generating answer…</span>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-5">
      <div className="surface-card overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
          <h3 className="font-semibold text-zinc-800">Answer</h3>
        </div>
        <div className="p-4 max-w-none">
          <p className="text-zinc-700 whitespace-pre-wrap">{data.answer}</p>
        </div>
        {data.support_status && (
          <div className="px-4 py-2 border-t border-slate-200 bg-slate-50/80">
            <span className="text-xs text-zinc-500 capitalize">Support: {data.support_status}</span>
          </div>
        )}
      </div>

      {data.citations && data.citations.length > 0 && (
        <div className="surface-card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
            <h3 className="font-semibold text-zinc-800 flex items-center gap-2">
              <FileText className="w-4 h-4" /> Sources
            </h3>
          </div>
          <ul className="p-4 space-y-2">
            {data.citations.map((c, i) => (
              <li key={i} className="text-sm text-zinc-600">
                <span className="font-medium text-zinc-800">{c.source_file}</span>
                {c.page != null && <span className="text-zinc-500">, page {c.page}</span>}
                {c.sheet_name && <span className="text-zinc-500">, sheet &quot;{c.sheet_name}&quot;</span>}
                {c.excerpt && (
                  <p className="mt-1 text-zinc-500 truncate max-w-2xl">{c.excerpt}</p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {useAgent && data.execution_summary && (
        <div className="surface-card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200 bg-slate-50">
            <h3 className="font-semibold text-zinc-800">Execution Summary</h3>
          </div>
          <ul className="p-4 space-y-1 text-sm text-zinc-600">
            {data.execution_summary.summary_steps.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {data.retrieved_chunks && data.retrieved_chunks.length > 0 && (
        <div className="surface-card overflow-hidden">
          <button
            type="button"
            onClick={() => setChunksOpen(!chunksOpen)}
            className="w-full px-4 py-3 flex items-center justify-between border-b border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
          >
            <span className="font-semibold text-zinc-800">Retrieved chunks ({data.retrieved_chunks.length})</span>
            {chunksOpen ? <ChevronDown className="w-4 h-4 text-zinc-600" /> : <ChevronRight className="w-4 h-4 text-zinc-600" />}
          </button>
          {chunksOpen && (
            <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
              {data.retrieved_chunks.map((chunk, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-sm"
                >
                  <div className="text-zinc-500 text-xs mb-1">
                    {String((chunk.metadata as Record<string, unknown>).file_name ?? '')}
                    {(chunk.metadata as Record<string, unknown>).page != null &&
                      `, page ${(chunk.metadata as Record<string, unknown>).page}`}
                  </div>
                  <p className="text-zinc-700 whitespace-pre-wrap line-clamp-4">{chunk.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
