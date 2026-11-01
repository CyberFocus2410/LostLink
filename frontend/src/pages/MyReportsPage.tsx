import React, { useEffect, useState, useCallback } from "react";
import { CheckCircle2, Eye, PlusCircle, MapPin, Calendar, Lock, MessageSquare, Trash2, Check, X } from "lucide-react";
import { api } from "../api/client";
import type { ReportItem, ContactRequestItem } from "../types/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Modal } from "../components/ui/Modal";
import { useAuth } from "../context/AuthContext";

interface MyReportsPageProps {
  onSelectReport: (id: string) => void;
  onNavigateToCreate: (type?: "LOST" | "FOUND") => void;
  onOpenAuth: () => void;
}

export const MyReportsPage: React.FC<MyReportsPageProps> = ({
  onSelectReport,
  onNavigateToCreate,
  onOpenAuth,
}) => {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState<"reports" | "requests">("reports");
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [contactRequests, setContactRequests] = useState<ContactRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  // Contact request action states
  const [actionNotes, setActionNotes] = useState<Record<string, string>>({});
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Account deletion modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);

  const loadData = useCallback(async () => {
    if (!isAuthenticated) {
      setReports([]);
      setContactRequests([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [reportsRes, requestsRes] = await Promise.all([
        api.getMyReports(1, 100).catch(() => ({ items: [], total: 0 })),
        api.getReceivedContactRequests().catch(() => []),
      ]);
      setReports(reportsRes.items);
      setContactRequests(requestsRes);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (!authLoading) {
      loadData();
    }
  }, [authLoading, loadData]);

  const handleResolve = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setResolvingId(id);
    try {
      const updated = await api.resolveReport(id);
      setReports((prev) => prev.map((r) => (r.id === id ? updated : r)));
    } catch (err: any) {
      alert(err.message || "Failed to resolve report.");
    } finally {
      setResolvingId(null);
    }
  };

  const handleAcceptRequest = async (requestId: string) => {
    setActionLoadingId(requestId);
    try {
      const updated = await api.acceptContactRequest(requestId, actionNotes[requestId]);
      setContactRequests((prev) => prev.map((r) => (r.id === requestId ? updated : r)));
    } catch (err: any) {
      alert(err.message || "Failed to accept contact request.");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeclineRequest = async (requestId: string) => {
    setActionLoadingId(requestId);
    try {
      const updated = await api.declineContactRequest(requestId, actionNotes[requestId]);
      setContactRequests((prev) => prev.map((r) => (r.id === requestId ? updated : r)));
    } catch (err: any) {
      alert(err.message || "Failed to decline contact request.");
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setDeletingAccount(true);
    try {
      await api.deleteMyAccount();
      await logout();
      setDeleteModalOpen(false);
      alert("Your account and all personal identifiable information have been permanently removed.");
    } catch (err: any) {
      alert(err.message || "Failed to delete account.");
    } finally {
      setDeletingAccount(false);
    }
  };

  if (!authLoading && !isAuthenticated) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center", maxWidth: 520, margin: "40px auto" }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            backgroundColor: "var(--color-sage-light)",
            color: "var(--color-teal)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 16px",
          }}
        >
          <Lock size={24} />
        </div>
        <h3>Sign In to View Your Reports</h3>
        <p className="text-secondary" style={{ fontSize: "0.88rem", marginTop: 8, marginBottom: 24 }}>
          Reports you create are tied to your authenticated account. Sign in to monitor candidate matches and resolve your listings.
        </p>
        <Button variant="primary" onClick={onOpenAuth} style={{ minWidth: 160 }}>
          Sign In / Register
        </Button>
      </div>
    );
  }

  const pendingRequestsCount = contactRequests.filter((r) => r.status === "PENDING").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2>Account Dashboard</h2>
          <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
            Signed in as <strong>{user?.display_name}</strong> ({user?.email})
          </p>
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <Button variant="secondary" size="sm" onClick={() => onNavigateToCreate("FOUND")}>
            Report Found
          </Button>
          <Button variant="primary" size="sm" icon={<PlusCircle size={14} />} onClick={() => onNavigateToCreate("LOST")}>
            Report Lost
          </Button>
        </div>
      </div>

      {/* Sub-tabs: My Reports vs Received Contact Requests */}
      <div style={{ display: "flex", gap: 12, borderBottom: "1px solid var(--color-border)", paddingBottom: 8 }}>
        <button
          type="button"
          onClick={() => setActiveSubTab("reports")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: activeSubTab === "reports" ? 700 : 500,
            color: activeSubTab === "reports" ? "var(--color-teal)" : "var(--color-ink-secondary)",
            borderBottom: activeSubTab === "reports" ? "2px solid var(--color-teal)" : "2px solid transparent",
            padding: "6px 12px",
            fontSize: "0.92rem",
          }}
        >
          My Listings ({reports.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveSubTab("requests")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            fontWeight: activeSubTab === "requests" ? 700 : 500,
            color: activeSubTab === "requests" ? "var(--color-teal)" : "var(--color-ink-secondary)",
            borderBottom: activeSubTab === "requests" ? "2px solid var(--color-teal)" : "2px solid transparent",
            padding: "6px 12px",
            fontSize: "0.92rem",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          Received Contact Requests ({contactRequests.length})
          {pendingRequestsCount > 0 && (
            <span
              style={{
                backgroundColor: "#E65100",
                color: "#FFFFFF",
                fontSize: "0.72rem",
                fontWeight: 700,
                borderRadius: "10px",
                padding: "1px 6px",
              }}
            >
              {pendingRequestsCount} new
            </span>
          )}
        </button>
      </div>

      {/* Tab 1: My Reports */}
      {activeSubTab === "reports" && (
        <>
          {loading ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              Loading your reports...
            </div>
          ) : reports.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center" }}>
              <p style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>No reports filed yet</p>
              <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4, marginBottom: 16 }}>
                Submit a lost or found report to automatically match with campus items.
              </p>
              <div style={{ display: "flex", justifyContent: "center", gap: 10 }}>
                <Button variant="primary" onClick={() => onNavigateToCreate("LOST")}>
                  Report Lost Item
                </Button>
                <Button variant="secondary" onClick={() => onNavigateToCreate("FOUND")}>
                  Report Found Item
                </Button>
              </div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="card card-interactive"
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: 14,
                  }}
                  onClick={() => onSelectReport(report.id)}
                >
                  <div style={{ display: "flex", gap: 14, flex: 1, minWidth: 260, alignItems: "center" }}>
                    {report.images && report.images.length > 0 && (
                      <div style={{ width: 64, height: 64, borderRadius: 6, overflow: "hidden", flexShrink: 0, border: "1px solid var(--color-border)", backgroundColor: "#F0F4F2" }}>
                        <img
                          src={report.images[0].thumbnail_url || report.images[0].image_url}
                          alt={report.item_name}
                          loading="lazy"
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      </div>
                    )}
                    <div>
                      <div style={{ display: "flex", gap: 6, marginBottom: 6, flexWrap: "wrap" }}>
                        <Badge type={report.type} />
                        <Badge category={report.category} />
                        <Badge status={report.status} />
                      </div>
                      <h4 style={{ fontSize: "1.05rem" }}>{report.item_name}</h4>
                      <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: "0.8rem", color: "var(--color-ink-secondary)", flexWrap: "wrap" }}>
                        <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {report.location_text}</span>
                        <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {report.event_date}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    {report.status === "ACTIVE" && (
                      <Button
                        variant="subtle"
                        size="sm"
                        icon={<CheckCircle2 size={14} />}
                        loading={resolvingId === report.id}
                        onClick={(e) => handleResolve(report.id, e)}
                      >
                        Mark Resolved
                      </Button>
                    )}
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Eye size={14} />}
                      onClick={() => onSelectReport(report.id)}
                    >
                      View Matches
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Tab 2: Received Contact Requests */}
      {activeSubTab === "requests" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {contactRequests.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
              <MessageSquare size={32} style={{ margin: "0 auto 12px", color: "var(--color-teal)" }} />
              <p style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>No contact requests yet</p>
              <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4 }}>
                When other community members believe they have found an item matching your listings, their requests will appear here.
              </p>
            </div>
          ) : (
            contactRequests.map((req) => (
              <div key={req.id} className="card" style={{ padding: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8, marginBottom: 10 }}>
                  <div>
                    <span
                      style={{
                        fontSize: "0.75rem",
                        fontWeight: 700,
                        padding: "2px 8px",
                        borderRadius: 4,
                        backgroundColor: req.status === "ACCEPTED" ? "#E8F5E9" : req.status === "DECLINED" ? "#FFEBEE" : "#FFF3E0",
                        color: req.status === "ACCEPTED" ? "#2E7D32" : req.status === "DECLINED" ? "#C62828" : "#E65100",
                      }}
                    >
                      {req.status}
                    </span>
                    <h4 style={{ marginTop: 6, marginBottom: 2 }}>From: {req.requester_name}</h4>
                    <span style={{ fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
                      Received: {req.created_at.slice(0, 10)}
                    </span>
                  </div>

                  {req.status === "ACCEPTED" ? (
                    <div style={{ backgroundColor: "#F0F4F2", padding: "8px 12px", borderRadius: 6, fontSize: "0.85rem" }}>
                      <div><strong>Direct Email:</strong> <a href={`mailto:${req.requester_email}`}>{req.requester_email}</a></div>
                      {req.requester_phone && <div><strong>Phone:</strong> {req.requester_phone}</div>}
                    </div>
                  ) : req.status === "DECLINED" ? (
                    <span style={{ fontSize: "0.85rem", color: "#C62828" }}>Declined — Contact Info Withheld</span>
                  ) : null}
                </div>

                <div style={{ backgroundColor: "#F6F7F4", padding: 12, borderRadius: 6, marginBottom: 14 }}>
                  <p style={{ margin: 0, fontStyle: "italic", fontSize: "0.9rem" }}>"{req.message}"</p>
                </div>

                {req.status === "PENDING" && (
                  <div style={{ display: "flex", flexDirection: "column", gap: 8, borderTop: "1px solid var(--color-border)", paddingTop: 12 }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Optional note to requester (e.g. meet at Library desk 3 PM)..."
                      value={actionNotes[req.id] || ""}
                      onChange={(e) => setActionNotes({ ...actionNotes, [req.id]: e.target.value })}
                      style={{ fontSize: "0.85rem" }}
                    />
                    <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon={<X size={14} />}
                        loading={actionLoadingId === req.id}
                        onClick={() => handleDeclineRequest(req.id)}
                      >
                        Decline
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        icon={<Check size={14} />}
                        loading={actionLoadingId === req.id}
                        onClick={() => handleAcceptRequest(req.id)}
                      >
                        Accept & Share Contact Info
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Privacy & Account Deletion Section (DPDP / GDPR) */}
      <div
        className="card"
        style={{
          marginTop: 24,
          padding: 20,
          border: "1px solid #FFCDD2",
          backgroundColor: "#FFF8F8",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div>
          <h4 style={{ margin: 0, color: "#C62828", display: "flex", alignItems: "center", gap: 6 }}>
            <Trash2 size={16} /> Delete Account & Personal Data
          </h4>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.82rem", color: "#546E7A" }}>
            Under India's DPDP Act & GDPR, you may permanently erase your account, sessions, and contact records.
          </p>
        </div>
        <Button variant="danger" size="sm" onClick={() => setDeleteModalOpen(true)}>
          Delete My Account
        </Button>
      </div>

      {/* Confirmation Modal */}
      <Modal isOpen={deleteModalOpen} onClose={() => setDeleteModalOpen(false)} title="Confirm Account Erasure">
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <p style={{ fontSize: "0.9rem", lineHeight: 1.5, margin: 0 }}>
            This action is <strong>permanent</strong>. In accordance with data privacy regulations:
          </p>
          <ul style={{ paddingLeft: 20, fontSize: "0.85rem", margin: 0, display: "flex", flexDirection: "column", gap: 4 }}>
            <li>Your email address and display name will be permanently anonymized.</li>
            <li>All active sessions and refresh tokens will be revoked immediately.</li>
            <li>Your listings will have all personal contact details scrubbed.</li>
          </ul>
          <p style={{ fontSize: "0.85rem", color: "#C62828", margin: 0 }}>
            Type <strong>DELETE</strong> below to confirm:
          </p>
          <input
            type="text"
            className="form-input"
            value={deleteConfirmText}
            onChange={(e) => setDeleteConfirmText(e.target.value)}
            placeholder="DELETE"
          />
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
            <Button variant="secondary" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={deleteConfirmText !== "DELETE"}
              loading={deletingAccount}
              onClick={handleDeleteAccount}
            >
              Permanently Erase
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
