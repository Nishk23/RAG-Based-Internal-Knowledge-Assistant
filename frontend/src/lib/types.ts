export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface DocumentSummary {
  document_id: string;
  document_name: string;
  chunk_count: number;
  created_at: string;
  allowed_roles: string[];
  metadata: Record<string, unknown>;
}

export interface UploadResponse {
  document_id: string;
  document_name: string;
  chunk_count: number;
  checksum: string;
  message: string;
}

export interface SampleLoadResponse {
  documents_loaded: number;
  chunks_indexed: number;
  message: string;
}

export interface SourceChunk {
  citation_index: number;
  document_name: string;
  chunk_id: string;
  text: string;
  score: number;
}

export interface EvaluationResult {
  status: string;
  metrics: Record<string, number | null>;
  skipped_metrics: string[];
  message: string;
}

export interface ChatRequest {
  question: string;
  top_k: number;
  evaluate: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  retrieval_method: string;
  evaluation: EvaluationResult | null;
  request_id: string;
}

export interface EvaluationRequest {
  question: string;
  answer: string;
  contexts: string[];
  ground_truth?: string;
}
