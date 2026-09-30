export interface User { id: number; email: string; created_at: string }
export interface TokenResponse { access_token: string; token_type: string; user: User }

export interface DocumentItem {
  id: number;
  filename: string;
  content_type: string | null;
  status: string;
  chunk_count: number;
  upload_date: string;
}

export interface HistoryItem {
  id: number;
  question: string;
  route: string | null;
  answer: string | null;
  created_at: string;
}

export interface DocSource {
  filename: string | null;
  chunk_index: number | null;
  similarity: number | null;
  matched_by: string[];
  content_preview: string;
}

/** Shape returned by POST /agentic-research-multimodal. */
export interface ResearchResponse {
  question: string;
  route: string;
  plan_reason: string;
  answer: string;
  document_sources: DocSource[];
  has_web_result: boolean;
  has_image_result: boolean;
}

export interface ResearchResult extends ResearchResponse {
  finishedAt: string;
  durationMs: number;
  usedImage: boolean;
}

export interface UploadResponse {
  document_id: number;
  filename: string;
  pages: number;
  chunk_count: number;
  message: string;
}
