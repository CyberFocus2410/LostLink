import type {
  APIResponse,
  ReportItem,
  ReportCreatePayload,
  ReportUpdatePayload,
  MatchListResponse,
  ContactRequestPayload,
  ReportFlagPayload,
  HealthData,
} from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

class APIErrorWrapper extends Error {
  code: string;
  fields?: Record<string, string>;

  constructor(code: string, message: string, fields?: Record<string, string>) {
    super(message);
    this.name = "APIErrorWrapper";
    this.code = code;
    this.fields = fields;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<APIResponse<T>> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers });
    const json: APIResponse<T> = await res.json();

    if (!res.ok || json.error) {
      const code = json.error?.code || `HTTP_${res.status}`;
      const msg = json.error?.message || `Request failed with status ${res.status}`;
      throw new APIErrorWrapper(code, msg, json.error?.fields);
    }

    return json;
  } catch (err: any) {
    if (err instanceof APIErrorWrapper) {
      throw err;
    }
    // Network or parsing error
    throw new APIErrorWrapper(
      "NETWORK_ERROR",
      "Unable to connect to LostLink service. Please ensure the backend is running.",
      undefined
    );
  }
}

export const api = {
  async getHealth(): Promise<HealthData> {
    const res = await request<HealthData>("/health");
    return res.data!;
  },

  async getReports(params: {
    q?: string;
    type?: string;
    category?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    location?: string;
    page?: number;
    limit?: number;
    sort?: string;
  } = {}): Promise<{ items: ReportItem[]; total: number }> {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.type) query.set("type", params.type);
    if (params.category) query.set("category", params.category);
    if (params.status) query.set("status", params.status);
    if (params.date_from) query.set("date_from", params.date_from);
    if (params.date_to) query.set("date_to", params.date_to);
    if (params.location) query.set("location", params.location);
    if (params.page) query.set("page", String(params.page));
    if (params.limit) query.set("limit", String(params.limit));
    if (params.sort) query.set("sort", params.sort);

    const qs = query.toString();
    const endpoint = `/reports${qs ? `?${qs}` : ""}`;
    const res = await request<ReportItem[]>(endpoint);
    return {
      items: res.data || [],
      total: res.meta?.total || (res.data ? res.data.length : 0),
    };
  },

  async getReport(id: string): Promise<ReportItem> {
    const res = await request<ReportItem>(`/reports/${id}`);
    return res.data!;
  },

  async createReport(data: ReportCreatePayload): Promise<ReportItem> {
    const res = await request<ReportItem>("/reports", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  async updateReport(id: string, data: ReportUpdatePayload): Promise<ReportItem> {
    const res = await request<ReportItem>(`/reports/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  async resolveReport(id: string): Promise<ReportItem> {
    const res = await request<ReportItem>(`/reports/${id}/resolve`, {
      method: "POST",
    });
    return res.data!;
  },

  async getMatches(id: string, limit = 5, minScore = 0): Promise<MatchListResponse> {
    const query = new URLSearchParams({
      limit: String(limit),
      minimum_score: String(minScore),
    });
    const res = await request<MatchListResponse>(`/reports/${id}/matches?${query.toString()}`);
    return res.data!;
  },

  async createContactRequest(data: ContactRequestPayload): Promise<any> {
    const res = await request<any>("/contact-requests", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data;
  },

  async flagReport(id: string, data: ReportFlagPayload): Promise<any> {
    const res = await request<any>(`/reports/${id}/flag`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data;
  },
};
