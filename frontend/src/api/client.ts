import type {
  APIResponse,
  ReportItem,
  ReportImage,
  Community,
  FacilityCluster,
  ReportCreatePayload,
  ReportUpdatePayload,
  MatchListResponse,
  ContactRequestPayload,
  ContactRequestItem,
  ReportFlagPayload,
  ReportFlagItem,
  HealthData,
  User,
  RegisterPayload,
  LoginPayload,
  ForgotPasswordPayload,
  ResetPasswordPayload,
} from "../types/api";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

export class APIErrorWrapper extends Error {
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
    const res = await fetch(url, {
      credentials: "include", // Sends httpOnly cookies for access/refresh tokens
      ...options,
      headers,
    });
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
  // ─── Health ───
  async getHealth(): Promise<HealthData> {
    const res = await request<HealthData>("/health");
    return res.data!;
  },

  // ─── Auth ───
  async register(data: RegisterPayload): Promise<User> {
    const res = await request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  async login(data: LoginPayload): Promise<User> {
    const res = await request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  async me(): Promise<User> {
    const res = await request<User>("/auth/me");
    return res.data!;
  },

  async refresh(): Promise<User> {
    const res = await request<User>("/auth/refresh", {
      method: "POST",
    });
    return res.data!;
  },

  async logout(): Promise<void> {
    await request<null>("/auth/logout", {
      method: "POST",
    });
  },

  async forgotPassword(data: ForgotPasswordPayload): Promise<void> {
    await request<null>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async resetPassword(data: ResetPasswordPayload): Promise<void> {
    await request<null>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // ─── Reports ───
  async getReports(params: {
    q?: string;
    type?: string;
    category?: string;
    status?: string;
    date_from?: string;
    date_to?: string;
    location?: string;
    owner_id?: string;
    community_id?: string;
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
    if (params.owner_id) query.set("owner_id", params.owner_id);
    if (params.community_id) query.set("community_id", params.community_id);
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

  async getMyReports(page = 1, limit = 50): Promise<{ items: ReportItem[]; total: number }> {
    const res = await request<ReportItem[]>(`/reports/mine?page=${page}&limit=${limit}`);
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

  // ─── Communities & Clusters ───
  async listCommunities(): Promise<Community[]> {
    const res = await request<Community[]>("/communities");
    return res.data || [];
  },

  async createCommunity(data: { name: string; slug: string; description?: string }): Promise<Community> {
    const res = await request<Community>("/communities", {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  async listCommunityClusters(communityIdOrSlug: string): Promise<FacilityCluster[]> {
    const res = await request<FacilityCluster[]>(`/communities/${communityIdOrSlug}/clusters`);
    return res.data || [];
  },

  async createCommunityCluster(
    communityId: string,
    data: { name: string; aliases: string[] }
  ): Promise<FacilityCluster> {
    const res = await request<FacilityCluster>(`/communities/${communityId}/clusters`, {
      method: "POST",
      body: JSON.stringify(data),
    });
    return res.data!;
  },

  // ─── Photo Uploads ───
  async uploadReportImage(reportId: string, file: File): Promise<ReportImage> {
    const url = `${BASE_URL}/reports/${reportId}/images`;
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(url, {
      method: "POST",
      credentials: "include",
      body: formData,
    });
    const json = await res.json();
    if (!res.ok || json.error) {
      const code = json.error?.code || `HTTP_${res.status}`;
      const msg = json.error?.message || `Upload failed with status ${res.status}`;
      throw new APIErrorWrapper(code, msg, json.error?.fields);
    }
    return json.data!;
  },

  async deleteReportImage(reportId: string, imageId: string): Promise<void> {
    await request<any>(`/reports/${reportId}/images/${imageId}`, {
      method: "DELETE",
    });
  },

  // ─── Double-Blind Contact Flow (Phase 7) ───
  async getReceivedContactRequests(): Promise<ContactRequestItem[]> {
    const res = await request<ContactRequestItem[]>("/contact-requests/received");
    return res.data || [];
  },

  async getSentContactRequests(): Promise<ContactRequestItem[]> {
    const res = await request<ContactRequestItem[]>("/contact-requests/sent");
    return res.data || [];
  },

  async acceptContactRequest(requestId: string, notes?: string): Promise<ContactRequestItem> {
    const res = await request<ContactRequestItem>(`/contact-requests/${requestId}/accept`, {
      method: "POST",
      body: JSON.stringify({ owner_notes: notes }),
    });
    return res.data!;
  },

  async declineContactRequest(requestId: string, notes?: string): Promise<ContactRequestItem> {
    const res = await request<ContactRequestItem>(`/contact-requests/${requestId}/decline`, {
      method: "POST",
      body: JSON.stringify({ owner_notes: notes }),
    });
    return res.data!;
  },

  // ─── Account Deletion (DPDP / GDPR) ───
  async deleteMyAccount(): Promise<void> {
    await request<any>("/auth/me", {
      method: "DELETE",
    });
  },

  // ─── Moderation (Phase 7) ───
  async getAdminFlags(flagStatus = "OPEN"): Promise<ReportFlagItem[]> {
    const res = await request<ReportFlagItem[]>(`/admin/flags?flag_status=${flagStatus}`);
    return res.data || [];
  },

  async reviewAdminFlag(flagId: string, action: "REVIEWED" | "DISMISSED"): Promise<ReportFlagItem> {
    const res = await request<ReportFlagItem>(`/admin/flags/${flagId}/review`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    return res.data!;
  },

  async moderateReportStatus(
    reportId: string,
    status: "ACTIVE" | "RESOLVED" | "HIDDEN"
  ): Promise<ReportItem> {
    const res = await request<ReportItem>(`/admin/reports/${reportId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    return res.data!;
  },

  async getAdminReports(statusFilter?: string, limit = 50): Promise<ReportItem[]> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (statusFilter && statusFilter !== "ALL") {
      query.set("status", statusFilter);
    }
    const res = await request<ReportItem[]>(`/admin/reports?${query.toString()}`);
    return res.data || [];
  },

  async getAdminUsers(search?: string, limit = 50): Promise<User[]> {
    const query = new URLSearchParams({ limit: String(limit) });
    if (search) {
      query.set("search", search);
    }
    const res = await request<User[]>(`/admin/users?${query.toString()}`);
    return res.data || [];
  },

  async moderateUserStatus(userId: string, isActive: boolean): Promise<{ message: string }> {
    const res = await request<{ message: string }>(`/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
    });
    return res.data!;
  },

  // ─── Anonymous Product Analytics (Phase 9) ───
  async recordAnalyticsEvent(eventName: string): Promise<void> {
    try {
      await request<any>("/analytics/event", {
        method: "POST",
        body: JSON.stringify({ event_name: eventName }),
      });
    } catch {
      // Telemetry errors must never disrupt user experience
    }
  },

  async getAnalyticsSummary(): Promise<any> {
    const res = await request<any>("/analytics/summary");
    return res.data;
  },
};
