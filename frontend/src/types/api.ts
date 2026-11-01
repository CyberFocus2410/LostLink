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

export interface ReportImage {
  id: string;
  report_id: string;
  image_url: string;
  thumbnail_url?: string | null;
  file_size: number;
  content_type: string;
  created_at: string;
}

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
  owner_id?: string | null;
  community_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  images?: ReportImage[];
  created_at: string;
  updated_at: string;
}

export interface Community {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface FacilityCluster {
  id: string;
  community_id: string;
  name: string;
  aliases: string[];
  created_at: string;
}

export interface User {
  id: string;
  display_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface RegisterPayload {
  display_name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export interface ReportCreatePayload {
  type: ReportType;
  item_name: string;
  category: CategoryEnum;
  description: string;
  event_date: string;
  location_text: string;
  community_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
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
  community_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
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
  requester_phone?: string;
  message: string;
}

export interface ContactRequestItem {
  id: string;
  report_id: string;
  requester_id?: string | null;
  requester_name: string;
  requester_email: string;
  requester_phone?: string | null;
  message: string;
  status: "PENDING" | "ACCEPTED" | "DECLINED";
  owner_response?: string | null;
  responded_at?: string | null;
  created_at: string;
}

export interface ReportFlagItem {
  id: string;
  report_id: string;
  reporter_id?: string | null;
  reason: string;
  status: string;
  created_at: string;
  report_item_name?: string;
  report_type?: string;
  report_category?: string;
  report_status?: string;
  report_description?: string;
  report_location?: string;
  report_image_url?: string;
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
