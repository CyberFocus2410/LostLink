import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../api/client";
import type { ReportItem, ReportFlagItem, User } from "../types/api";
import { Button } from "../components/ui/Button";
import {
  ShieldAlert,
  Users,
  FileText,
  Activity,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  UserCheck,
  UserX,
  RefreshCw,
  Search,
} from "lucide-react";

interface AdminDashboardPageProps {
  onNavigateToDetail?: (reportId: string) => void;
}

export const AdminDashboardPage: React.FC<AdminDashboardPageProps> = ({
  onNavigateToDetail,
}) => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<"flags" | "reports" | "users">("flags");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Analytics summary
  const [analytics, setAnalytics] = useState<any>(null);

  // Tab 1: Flags
  const [flags, setFlags] = useState<ReportFlagItem[]>([]);
  const [flagFilter, setFlagFilter] = useState("OPEN");

  // Tab 2: Reports
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [reportFilter, setReportFilter] = useState("ALL");
  const [reportSearch, setReportSearch] = useState("");

  // Tab 3: Users
  const [users, setUsers] = useState<User[]>([]);
  const [userSearch, setUserSearch] = useState("");

  const isAdmin = user?.role === "admin" || user?.role === "moderator";

  const showNotification = (text: string, type: "success" | "error" = "success") => {
    setMessage({ text, type });
    setTimeout(() => setMessage(null), 4000);
  };

  const loadAnalytics = useCallback(async () => {
    try {
      const data = await api.getAnalyticsSummary();
      setAnalytics(data);
    } catch {
      // ignore
    }
  }, []);

  const loadFlags = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAdminFlags(flagFilter);
      setFlags(data);
    } catch (err: any) {
      showNotification(err.message || "Failed to load flags", "error");
    } finally {
      setLoading(false);
    }
  }, [flagFilter]);

  const loadReports = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAdminReports(reportFilter, 50);
      setReports(data);
    } catch (err: any) {
      showNotification(err.message || "Failed to load reports", "error");
    } finally {
      setLoading(false);
    }
  }, [reportFilter]);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getAdminUsers(userSearch, 50);
      setUsers(data);
    } catch (err: any) {
      showNotification(err.message || "Failed to load users", "error");
    } finally {
      setLoading(false);
    }
  }, [userSearch]);

  useEffect(() => {
    if (!isAdmin) return;
    loadAnalytics();
  }, [isAdmin, loadAnalytics]);

  useEffect(() => {
    if (!isAdmin) return;
    if (activeTab === "flags") loadFlags();
    if (activeTab === "reports") loadReports();
    if (activeTab === "users") loadUsers();
  }, [isAdmin, activeTab, loadFlags, loadReports, loadUsers]);

  // Actions
  const handleReviewFlag = async (flagId: string, action: "REVIEWED" | "DISMISSED") => {
    try {
      await api.reviewAdminFlag(flagId, action);
      showNotification(`Flag marked as ${action.toLowerCase()}`);
      loadFlags();
    } catch (err: any) {
      showNotification(err.message || "Action failed", "error");
    }
  };

  const handleModerateReport = async (
    reportId: string,
    status: "ACTIVE" | "RESOLVED" | "HIDDEN"
  ) => {
    try {
      await api.moderateReportStatus(reportId, status);
      showNotification(`Report status set to ${status}`);
      if (activeTab === "flags") loadFlags();
      if (activeTab === "reports") loadReports();
    } catch (err: any) {
      showNotification(err.message || "Action failed", "error");
    }
  };

  const handleToggleUser = async (targetUser: User) => {
    if (targetUser.id === user?.id) {
      showNotification("You cannot deactivate your own admin account", "error");
      return;
    }
    const newStatus = !targetUser.is_active;
    try {
      await api.moderateUserStatus(targetUser.id, newStatus);
      showNotification(`User ${targetUser.display_name} ${newStatus ? "reactivated" : "deactivated"}`);
      loadUsers();
    } catch (err: any) {
      showNotification(err.message || "Action failed", "error");
    }
  };

  if (!isAdmin) {
    return (
      <div className="card" style={{ maxWidth: 600, margin: "60px auto", padding: 48, textAlign: "center" }}>
        <ShieldAlert size={48} color="#D97706" style={{ margin: "0 auto 16px" }} />
        <h2>Administrative Privileges Required</h2>
        <p className="text-secondary" style={{ marginTop: 8 }}>
          You must be signed in as an administrator or community moderator to access this control center.
        </p>
      </div>
    );
  }

  const filteredReports = reports.filter((r) =>
    reportSearch ? r.item_name.toLowerCase().includes(reportSearch.toLowerCase()) : true
  );

  const pendingFlagsCount = flags.filter((f) => f.status === "OPEN").length;

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "8px 0" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: 16,
          paddingBottom: 20,
          borderBottom: "1px solid var(--color-border)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-teal-soft)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--color-teal)",
              }}
            >
              <ShieldAlert size={22} />
            </div>
            <div>
              <h1 style={{ fontSize: "1.65rem", fontWeight: 700, margin: 0 }}>Admin & Moderation Center</h1>
              <p className="text-secondary" style={{ fontSize: "0.88rem", marginTop: 2 }}>
                System-wide moderation, abuse flag triage, and user account management.
              </p>
            </div>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          icon={<RefreshCw size={14} className={loading ? "animate-spin" : ""} />}
          onClick={() => {
            loadAnalytics();
            if (activeTab === "flags") loadFlags();
            if (activeTab === "reports") loadReports();
            if (activeTab === "users") loadUsers();
          }}
        >
          Refresh Data
        </Button>
      </div>

      {/* Notifications */}
      {message && (
        <div
          style={{
            marginTop: 16,
            padding: "10px 16px",
            borderRadius: "var(--radius-md)",
            fontSize: "0.88rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            backgroundColor: message.type === "success" ? "var(--color-success-bg)" : "var(--color-error-bg)",
            color: message.type === "success" ? "var(--color-success)" : "var(--color-error)",
            border: `1px solid ${message.type === "success" ? "var(--color-success)" : "var(--color-error)"}`,
          }}
        >
          <span>{message.text}</span>
          <button
            onClick={() => setMessage(null)}
            style={{ background: "none", border: "none", cursor: "pointer", fontWeight: 700, marginLeft: 12 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Product Analytics Cards */}
      {analytics && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 14,
            marginTop: 20,
          }}
        >
          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--color-ink-secondary)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Active Reports
              </span>
              <FileText size={18} color="var(--color-teal)" />
            </div>
            <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-ink-primary)", marginTop: 6 }}>
              {analytics.active_reports ?? 0}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", marginTop: 4 }}>
              {analytics.active_lost ?? 0} lost · {analytics.active_found ?? 0} found
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--color-ink-secondary)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Resolved Items
              </span>
              <CheckCircle size={18} color="var(--color-success)" />
            </div>
            <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-ink-primary)", marginTop: 6 }}>
              {analytics.resolved_reports ?? 0}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", marginTop: 4 }}>
              Successfully returned items
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--color-ink-secondary)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Campus Clusters
              </span>
              <Activity size={18} color="#6366F1" />
            </div>
            <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-ink-primary)", marginTop: 6 }}>
              {analytics.active_communities ?? 0}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", marginTop: 4 }}>
              Active geographical zones
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "var(--color-ink-secondary)" }}>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Pending Flags
              </span>
              <ShieldAlert size={18} color="#D97706" />
            </div>
            <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-ink-primary)", marginTop: 6 }}>
              {flags.filter((f) => f.status === "OPEN").length}
            </div>
            <div style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", marginTop: 4 }}>
              Awaiting review
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div
        style={{
          display: "flex",
          gap: 16,
          borderBottom: "1px solid var(--color-border)",
          marginTop: 28,
          marginBottom: 20,
          overflowX: "auto",
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab("flags")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: activeTab === "flags" ? 700 : 500,
            color: activeTab === "flags" ? "var(--color-teal)" : "var(--color-ink-secondary)",
            borderBottom: activeTab === "flags" ? "2px solid var(--color-teal)" : "2px solid transparent",
            padding: "8px 14px",
            fontSize: "0.94rem",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <ShieldAlert size={16} />
          <span>Abuse Flags</span>
          {pendingFlagsCount > 0 && (
            <span
              style={{
                backgroundColor: "#E65100",
                color: "#FFFFFF",
                fontSize: "0.72rem",
                fontWeight: 700,
                borderRadius: "10px",
                padding: "1px 7px",
              }}
            >
              {pendingFlagsCount}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("reports")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: activeTab === "reports" ? 700 : 500,
            color: activeTab === "reports" ? "var(--color-teal)" : "var(--color-ink-secondary)",
            borderBottom: activeTab === "reports" ? "2px solid var(--color-teal)" : "2px solid transparent",
            padding: "8px 14px",
            fontSize: "0.94rem",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <FileText size={16} />
          <span>Reports Moderation</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab("users")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: activeTab === "users" ? 700 : 500,
            color: activeTab === "users" ? "var(--color-teal)" : "var(--color-ink-secondary)",
            borderBottom: activeTab === "users" ? "2px solid var(--color-teal)" : "2px solid transparent",
            padding: "8px 14px",
            fontSize: "0.94rem",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Users size={16} />
          <span>User Accounts</span>
        </button>
      </div>

      {/* Tab 1: Abuse Flags */}
      {activeTab === "flags" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
            <h2 style={{ fontSize: "1.15rem", fontWeight: 600 }}>Reported Content Flags</h2>
            <div style={{ display: "flex", gap: 6 }}>
              {["OPEN", "REVIEWED", "DISMISSED"].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setFlagFilter(st)}
                  className={`btn ${flagFilter === st ? "btn-primary" : "btn-secondary"} btn-sm`}
                  style={{ minHeight: 32, padding: "4px 12px", fontSize: "0.78rem" }}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              Loading flags...
            </div>
          ) : flags.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              No {flagFilter.toLowerCase()} flags currently queued.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {flags.map((flag) => (
                <div key={flag.id} className="card" style={{ padding: 18 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 14 }}>
                    <div style={{ flex: 1, minWidth: 260 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
                        <span className={`badge ${flag.status === "OPEN" ? "badge-lost" : "badge-resolved"}`}>
                          Flag: {flag.status}
                        </span>
                        {flag.report_type && (
                          <span className={`badge ${flag.report_type === "LOST" ? "badge-lost" : "badge-found"}`}>
                            {flag.report_type}
                          </span>
                        )}
                        {flag.report_category && (
                          <span className="badge badge-category">
                            {flag.report_category}
                          </span>
                        )}
                        {flag.report_status && (
                          <span
                            className={`badge ${
                              flag.report_status === "ACTIVE"
                                ? "badge-active"
                                : flag.report_status === "RESOLVED"
                                ? "badge-resolved"
                                : "badge-lost"
                            }`}
                          >
                            Post: {flag.report_status === "HIDDEN" ? "TAKEN DOWN" : flag.report_status}
                          </span>
                        )}
                        <span style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)" }}>
                          Reported: {new Date(flag.created_at).toLocaleDateString()}
                        </span>
                      </div>

                      {/* Item Details and Photo */}
                      <div style={{ display: "flex", gap: 14, alignItems: "flex-start", marginTop: 8, marginBottom: 12 }}>
                        {flag.report_image_url && (
                          <img
                            src={flag.report_image_url}
                            alt={flag.report_item_name || "Report"}
                            style={{
                              width: 68,
                              height: 68,
                              objectFit: "cover",
                              borderRadius: "var(--radius-sm)",
                              border: "1px solid var(--color-border)",
                              flexShrink: 0,
                            }}
                          />
                        )}
                        <div>
                          <h3
                            style={{
                              margin: 0,
                              fontSize: "1.08rem",
                              color: "var(--color-ink-primary)",
                              cursor: onNavigateToDetail ? "pointer" : "default",
                            }}
                            onClick={() => onNavigateToDetail && onNavigateToDetail(flag.report_id)}
                          >
                            {flag.report_item_name || `Report #${flag.report_id.slice(0, 8)}`}
                          </h3>
                          {flag.report_description && (
                            <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4, lineHeight: 1.45 }}>
                              {flag.report_description}
                            </p>
                          )}
                          {flag.report_location && (
                            <div style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", marginTop: 4 }}>
                              📍 {flag.report_location}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Reported Reason Banner */}
                      <div
                        style={{
                          backgroundColor: "var(--color-canvas)",
                          borderLeft: "3px solid #D97706",
                          padding: "10px 14px",
                          borderRadius: "var(--radius-sm)",
                          marginTop: 6,
                          marginBottom: 6,
                        }}
                      >
                        <strong style={{ fontSize: "0.85rem", color: "#B45309" }}>Reported Abuse Reason:</strong>{" "}
                        <span style={{ fontSize: "0.85rem", color: "var(--color-ink-primary)" }}>{flag.reason}</span>
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                      {onNavigateToDetail && (
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<Eye size={13} />}
                          onClick={() => onNavigateToDetail(flag.report_id)}
                        >
                          View Full Post
                        </Button>
                      )}

                      {flag.report_status === "HIDDEN" ? (
                        <Button
                          variant="primary"
                          size="sm"
                          icon={<CheckCircle size={13} />}
                          onClick={() => handleModerateReport(flag.report_id, "ACTIVE")}
                        >
                          Restore Post
                        </Button>
                      ) : (
                        <Button
                          variant="danger"
                          size="sm"
                          icon={<EyeOff size={13} />}
                          onClick={() => handleModerateReport(flag.report_id, "HIDDEN")}
                        >
                          Take Down (Hide)
                        </Button>
                      )}

                      {flag.status === "OPEN" && (
                        <>
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<CheckCircle size={13} />}
                            onClick={() => handleReviewFlag(flag.id, "REVIEWED")}
                          >
                            Mark Reviewed
                          </Button>
                          <Button
                            variant="subtle"
                            size="sm"
                            icon={<XCircle size={13} />}
                            onClick={() => handleReviewFlag(flag.id, "DISMISSED")}
                          >
                            Dismiss
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Reports Moderation */}
      {activeTab === "reports" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <div style={{ position: "relative", minWidth: 260, flex: 1, maxWidth: 360 }}>
              <Search
                size={16}
                color="var(--color-ink-secondary)"
                style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)" }}
              />
              <input
                type="text"
                placeholder="Search reports by title..."
                value={reportSearch}
                onChange={(e) => setReportSearch(e.target.value)}
                className="form-input"
                style={{ paddingLeft: 34, height: 38, fontSize: "0.88rem" }}
              />
            </div>

            <div style={{ display: "flex", gap: 6 }}>
              {["ALL", "ACTIVE", "RESOLVED", "HIDDEN"].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setReportFilter(st)}
                  className={`btn ${reportFilter === st ? "btn-primary" : "btn-secondary"} btn-sm`}
                  style={{ minHeight: 32, padding: "4px 12px", fontSize: "0.78rem" }}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              Loading reports...
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              No reports match your filters.
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--color-canvas)", borderBottom: "1px solid var(--color-border)" }}>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Item Name
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Type
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Category
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Date
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Status
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "right", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredReports.map((r) => (
                    <tr
                      key={r.id}
                      style={{ borderBottom: "1px solid var(--color-border)", transition: "background 0.15s" }}
                    >
                      <td style={{ padding: "12px 16px", fontWeight: 600 }}>{r.item_name}</td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className={`badge ${r.type === "LOST" ? "badge-lost" : "badge-found"}`}>
                          {r.type}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--color-ink-secondary)", fontSize: "0.82rem" }}>
                        {r.category}
                      </td>
                      <td style={{ padding: "12px 16px", color: "var(--color-ink-secondary)", fontSize: "0.82rem" }}>
                        {r.event_date}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span
                          className={`badge ${
                            r.status === "ACTIVE"
                              ? "badge-active"
                              : r.status === "RESOLVED"
                              ? "badge-resolved"
                              : "badge-lost"
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right" }}>
                        <div style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
                          {onNavigateToDetail && (
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={<Eye size={12} />}
                              onClick={() => onNavigateToDetail(r.id)}
                            >
                              View
                            </Button>
                          )}
                          {r.status === "HIDDEN" ? (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleModerateReport(r.id, "ACTIVE")}
                            >
                              Restore
                            </Button>
                          ) : (
                            <Button
                              variant="danger"
                              size="sm"
                              icon={<EyeOff size={12} />}
                              onClick={() => handleModerateReport(r.id, "HIDDEN")}
                            >
                              Take Down
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 3: User Accounts */}
      {activeTab === "users" && (
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <h2 style={{ fontSize: "1.15rem", fontWeight: 600 }}>User Accounts Management</h2>
            <div style={{ position: "relative", width: 280 }}>
              <Search
                size={16}
                color="var(--color-ink-secondary)"
                style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)" }}
              />
              <input
                type="text"
                placeholder="Search by email or name..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="form-input"
                style={{ paddingLeft: 34, height: 38, fontSize: "0.88rem" }}
              />
            </div>
          </div>

          {loading ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              Loading users...
            </div>
          ) : users.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              No users found.
            </div>
          ) : (
            <div className="card" style={{ padding: 0, overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ backgroundColor: "var(--color-canvas)", borderBottom: "1px solid var(--color-border)" }}>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      User
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Email
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Role
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "left", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Status
                    </th>
                    <th style={{ padding: "12px 16px", textAlign: "right", fontSize: "0.75rem", textTransform: "uppercase", color: "var(--color-ink-secondary)" }}>
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr
                      key={u.id}
                      style={{ borderBottom: "1px solid var(--color-border)", transition: "background 0.15s" }}
                    >
                      <td style={{ padding: "12px 16px", fontWeight: 600 }}>{u.display_name}</td>
                      <td style={{ padding: "12px 16px", fontFamily: "var(--font-family-mono)", fontSize: "0.82rem", color: "var(--color-ink-secondary)" }}>
                        {u.email}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className="badge badge-active">{u.role}</span>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <span className={`badge ${u.is_active ? "badge-found" : "badge-lost"}`}>
                          {u.is_active ? "Active" : "Deactivated"}
                        </span>
                      </td>
                      <td style={{ padding: "12px 16px", textAlign: "right" }}>
                        {u.id === user?.id ? (
                          <span style={{ fontSize: "0.8rem", color: "var(--color-ink-secondary)", fontStyle: "italic" }}>
                            Current User
                          </span>
                        ) : u.is_active ? (
                          <Button
                            variant="danger"
                            size="sm"
                            icon={<UserX size={13} />}
                            onClick={() => handleToggleUser(u)}
                          >
                            Deactivate
                          </Button>
                        ) : (
                          <Button
                            variant="primary"
                            size="sm"
                            icon={<UserCheck size={13} />}
                            onClick={() => handleToggleUser(u)}
                          >
                            Reactivate
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
