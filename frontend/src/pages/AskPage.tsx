import { useState } from 'react'
import { query, agentsQuery } from '../lib/api'
import type { QueryResponse, AgentQueryResponse } from '../types'
import AnswerPanel from '../components/AnswerPanel'

export default function AskPage() {
  const [question, setQuestion] = useState('')
  const [useAgent, setUseAgent] = useState(true)
  const [result, setResult] = useState<QueryResponse | AgentQueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    setError(null)
    setResult(null)
    setLoading(true)
    try {
      const res = useAgent ? await agentsQuery(question.trim()) : await query(question.trim())
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="glass-panel p-6 md:p-8 mb-8">
        <h2 className="text-2xl font-semibold text-zinc-800 mb-2 tracking-tight">Ask a question</h2>
        <p className="text-zinc-600 mb-6 text-sm leading-relaxed">
          Ask natural language questions about your uploaded documents. Use the agent workflow for an execution summary.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What is the eligibility period for benefits?"
            className="w-full px-4 py-3.5 rounded-xl bg-white border border-slate-300 text-zinc-800 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-sky-400/50 focus:border-sky-400 resize-none shadow-inner transition-all duration-200"
            rows={3}
            maxLength={2000}
          />
        <div className="flex flex-wrap items-center gap-4">
          <label className="flex items-center gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={useAgent}
              onChange={(e) => setUseAgent(e.target.checked)}
              className="rounded border-slate-400 bg-white text-sky-500 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-white"
            />
            <span className="text-zinc-700 text-sm">Use agent workflow (Planner → Retriever → Reasoner → Validator)</span>
          </label>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
          >
            {loading ? 'Asking…' : 'Ask'}
          </button>
        </div>
        </form>
      </div>
      {error && (
        <div className="mt-4 rounded-xl bg-red-50 border border-red-200 text-red-700 px-4 py-3 text-sm">
          {error}
        </div>
      )}
      <div className="mt-6">
        <AnswerPanel data={result} loading={loading} useAgent={useAgent} />
      </div>
    </div>
  )
}
