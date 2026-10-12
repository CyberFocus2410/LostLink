export type ReportType = "LOST" | "FOUND";
export type ReportStatus = "ACTIVE" | "RESOLVED" | "HIDDEN";

export type CategoryEnum =
  | "ELECTRONICS"
  | "KEYS_CARDS"
  | "BAGS_WALLETS"
  | "CLOTHING"
  | "DOCUMENTS_BOOKS"
  | "JEWELRY_WATCHES"
  | "OTHER";

export interface ReportItem {
  id: string;
  type: ReportType;
  item_name: string;
  category: CategoryEnum;
  description: string;
  event_date: string;
  location_text: string;
  normalized_location: string;
  status: ReportStatus;
  created_at: string;
  updated_at: string;
}

export interface ReportCreatePayload {
  type: ReportType;
  item_name: string;
  category: CategoryEnum;
  description: string;
  event_date: string;
  location_text: string;
  contact_name: string;
  contact_email: string;
  contact_phone?: string;
}

export interface ReportUpdatePayload {
  item_name?: string;
  category?: CategoryEnum;
  description?: string;
  event_date?: string;
  location_text?: string;
  status?: ReportStatus;
}

export interface MatchComponentScores {
  category_score: number;
  location_score: number;
  date_score: number;
  keyword_score: number;
}

export interface MatchResultItem {
  candidate: ReportItem;
  total_score: number;
  components: MatchComponentScores;
  shared_keywords: string[];
  reasons: string[];
  disclaimer: string;
}

export interface MatchListResponse {
  source_report: ReportItem;
  matches: MatchResultItem[];
  candidate_count: number;
}

export interface ContactRequestPayload {
  report_id: string;
  requester_name: string;
  requester_email: string;
  message: string;
}

export interface ReportFlagPayload {
  reason: string;
}

export interface APIError {
  code: string;
  message: string;
  fields?: Record<string, string>;
}

export interface APIMeta {
  page?: number;
  limit?: number;
  total?: number;
  extra?: Record<string, any>;
}

export interface APIResponse<T> {
  data: T | null;
  error: APIError | null;
  meta?: APIMeta | null;
}

export interface HealthData {
  status: string;
  service: string;
  environment: string;
  indexed_records: number;
  indexed_categories: number;
  indexed_tokens: number;
}
