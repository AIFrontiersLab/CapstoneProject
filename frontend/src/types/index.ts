export type DocumentIngestionStatus =
  | 'pending'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'indexing'
  | 'completed'
  | 'failed'

export interface DocumentListItem {
  document_id: string
  file_name: string
  file_type: string
  status: DocumentIngestionStatus
  created_at: string
  chunk_count: number
}

export interface DocumentDetail extends DocumentListItem {
  file_size_bytes: number
  page_count?: number
  sheet_names?: string[]
  error_message?: string
}

export interface UploadResponse {
  document_id: string
  file_name: string
  status: DocumentIngestionStatus
  message: string
  chunk_count: number
}

export type SupportStatus = 'supported' | 'partial' | 'insufficient'

export interface Citation {
  source_file: string
  page?: number
  sheet_name?: string
  excerpt?: string
  chunk_id?: string
}

export interface RetrievedChunk {
  content: string
  metadata: Record<string, unknown>
  score?: number
  chunk_id?: string
}

export interface ExecutionSummary {
  planned_query?: string
  retrieval_performed: boolean
  chunks_retrieved: number
  validation_passed: boolean
  support_status: SupportStatus
  summary_steps: string[]
}

export interface QueryResponse {
  question: string
  answer: string
  citations: Citation[]
  retrieved_chunks: RetrievedChunk[]
  execution_summary?: ExecutionSummary
  support_status: SupportStatus
  confidence_note?: string
}

export interface AgentQueryResponse extends QueryResponse {
  execution_summary?: ExecutionSummary
}
