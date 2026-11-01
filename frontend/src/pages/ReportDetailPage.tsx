import React, { useEffect, useState } from "react";
import { ArrowLeft, CheckCircle2, Flag, Edit, MessageSquare, MapPin, Calendar } from "lucide-react";
import { api } from "../api/client";
import type { ReportItem, MatchResultItem } from "../types/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ScoreBreakdown } from "../components/ui/ScoreBreakdown";
import { DisclaimerBanner } from "../components/ui/DisclaimerBanner";
import { Modal } from "../components/ui/Modal";
import { useAuth } from "../context/AuthContext";

interface ReportDetailPageProps {
  reportId: string;
  onBack: () => void;
  onEdit: (id: string) => void;
  onViewCandidate: (candidateId: string) => void;
}

export const ReportDetailPage: React.FC<ReportDetailPageProps> = ({
  reportId,
  onBack,
  onEdit,
  onViewCandidate,
}) => {
  const { user } = useAuth();
  const [report, setReport] = useState<ReportItem | null>(null);
  const [matches, setMatches] = useState<MatchResultItem[]>([]);
  const [candidatePoolSize, setCandidatePoolSize] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Resolution state
  const [resolving, setResolving] = useState(false);
  const [resolveSuccess, setResolveSuccess] = useState(false);

  // Contact Modal state
  const [contactModalOpen, setContactModalOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ReportItem | null>(null);
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [contactSubmitting, setContactSubmitting] = useState(false);
  const [contactSuccessMsg, setContactSuccessMsg] = useState<string | null>(null);

  // Flag Modal state
  const [flagModalOpen, setFlagModalOpen] = useState(false);
  const [flagReason, setFlagReason] = useState("");
  const [flagSubmitting, setFlagSubmitting] = useState(false);
  const [flagSuccessMsg, setFlagSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    loadReportAndMatches();
  }, [reportId]);

  const loadReportAndMatches = async () => {
    setLoading(true);
    setError(null);
    try {
      const rep = await api.getReport(reportId);
      setReport(rep);

      if (rep.status === "ACTIVE") {
        const matchRes = await api.getMatches(reportId, 10);
        setMatches(matchRes.matches);
        setCandidatePoolSize(matchRes.candidate_count);
      } else {
        setMatches([]);
        setCandidatePoolSize(0);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load report details");
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async () => {
    if (!report) return;
    setResolving(true);
    try {
      const updated = await api.resolveReport(report.id);
      setReport(updated);
      setMatches([]);
      setResolveSuccess(true);
      setTimeout(() => setResolveSuccess(false), 4000);
    } catch (err: any) {
      alert(err.message || "Could not resolve report.");
    } finally {
      setResolving(false);
    }
  };

  const handleOpenContactModal = (cand: ReportItem) => {
    setSelectedCandidate(cand);
    setContactName("");
    setContactEmail("");
    setContactMessage(
      `Hello, I saw your report for "${cand.item_name}" and believe it corresponds to my notice. Here are distinguishing details:`
    );
    setContactSuccessMsg(null);
    setContactModalOpen(true);
  };

  const handleSendContactRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCandidate) return;

    setContactSubmitting(true);
    try {
      await api.createContactRequest({
        report_id: selectedCandidate.id,
        requester_name: contactName.trim(),
        requester_email: contactEmail.trim(),
        message: contactMessage.trim(),
      });
      setContactSuccessMsg("Contact request transmitted successfully. The finder/reporter will receive your message.");
      setTimeout(() => {
        setContactModalOpen(false);
        setContactSuccessMsg(null);
      }, 2500);
    } catch (err: any) {
      alert(err.message || "Failed to send contact request.");
    } finally {
      setContactSubmitting(false);
    }
  };

  const handleSendFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!report) return;

    setFlagSubmitting(true);
    try {
      await api.flagReport(report.id, { reason: flagReason.trim() });
      setFlagSuccessMsg("Report has been flagged for administrative review.");
      setTimeout(() => {
        setFlagModalOpen(false);
        setFlagSuccessMsg(null);
      }, 2000);
    } catch (err: any) {
      alert(err.message || "Failed to flag report.");
    } finally {
      setFlagSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
        Loading report and matching candidates...
      </div>
    );
  }

  if (error || !report) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <Button variant="secondary" icon={<ArrowLeft size={16} />} onClick={onBack}>
          Back to Reports
        </Button>
        <div className="alert-banner alert-banner-error">
          {error || "Report was not found."}
        </div>
      </div>
    );
  }

  const isResolved = report.status === "RESOLVED";
  const isOwner = Boolean(
    user && report.owner_id && (report.owner_id === user.id || user.role === "admin")
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Back button & Action Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <Button variant="secondary" size="sm" icon={<ArrowLeft size={15} />} onClick={onBack}>
          Back to Reports
        </Button>

        <div style={{ display: "flex", gap: 8 }}>
          {isOwner && !isResolved && (
            <>
              <Button variant="secondary" size="sm" icon={<Edit size={14} />} onClick={() => onEdit(report.id)}>
                Edit
              </Button>
              <Button
                variant="subtle"
                size="sm"
                icon={<CheckCircle2 size={14} />}
                loading={resolving}
                onClick={handleResolve}
              >
                Mark as Resolved
              </Button>
            </>
          )}
          <Button variant="secondary" size="sm" icon={<Flag size={14} />} onClick={() => setFlagModalOpen(true)}>
            Flag
          </Button>
        </div>
      </div>

      {resolveSuccess && (
        <div className="alert-banner alert-banner-success">
          Report marked as <strong>RESOLVED</strong>. The item has been removed from active matching.
        </div>
      )}

      {/* Admin Quick Moderation Strip */}
      {(user?.role === "admin" || user?.role === "moderator") && (
        <div
          className="card"
          style={{
            backgroundColor: report.status === "HIDDEN" ? "var(--color-error-bg)" : "var(--color-sage-light)",
            borderColor: report.status === "HIDDEN" ? "var(--color-error)" : "var(--color-teal)",
            padding: "12px 18px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <span style={{ fontWeight: 700, fontSize: "0.85rem", color: "var(--color-ink-primary)" }}>
              Admin Moderation:
            </span>
            <span
              className={`badge ${
                report.status === "ACTIVE"
                  ? "badge-active"
                  : report.status === "RESOLVED"
                  ? "badge-resolved"
                  : "badge-lost"
              }`}
            >
              {report.status === "HIDDEN" ? "TAKEN DOWN (HIDDEN)" : report.status}
            </span>
            <span style={{ fontSize: "0.82rem", color: "var(--color-ink-secondary)" }}>
              {report.status === "HIDDEN"
                ? "This post is taken down and hidden from public search & matching."
                : "This post is live and visible to campus users."}
            </span>
          </div>

          <div>
            {report.status === "HIDDEN" ? (
              <Button
                variant="primary"
                size="sm"
                onClick={async () => {
                  try {
                    const updated = await api.moderateReportStatus(report.id, "ACTIVE");
                    setReport(updated);
                  } catch (e: any) {
                    alert(e.message || "Failed to restore report");
                  }
                }}
              >
                Restore Post (Make Visible)
              </Button>
            ) : (
              <Button
                variant="danger"
                size="sm"
                onClick={async () => {
                  try {
                    const updated = await api.moderateReportStatus(report.id, "HIDDEN");
                    setReport(updated);
                  } catch (e: any) {
                    alert(e.message || "Failed to take down report");
                  }
                }}
              >
                Take Down (Hide from Public)
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Main Report Card */}
      <section className="card" style={{ padding: "var(--space-6)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12, marginBottom: 12 }}>
          <div>
            <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
              <Badge type={report.type} />
              <Badge category={report.category} />
              <Badge status={report.status} />
            </div>
            <h1>{report.item_name}</h1>
          </div>

          <div style={{ fontSize: "0.8rem", color: "var(--color-ink-secondary)", textAlign: "right" }}>
            <div>ID: <span style={{ fontFamily: "var(--font-family-mono)" }}>{report.id.slice(0, 8)}...</span></div>
            <div>Filed: {report.created_at.slice(0, 10)}</div>
          </div>
        </div>

        {/* Description */}
        <p style={{ fontSize: "0.95rem", lineHeight: 1.6, color: "var(--color-ink-primary)", marginTop: 8, marginBottom: 20 }}>
          {report.description}
        </p>

        {/* Photo Gallery if images exist */}
        {report.images && report.images.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ color: "var(--color-ink-secondary)", fontSize: "0.78rem", marginBottom: 8, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Photos ({report.images.length})
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
              {report.images.map((img) => (
                <a
                  key={img.id}
                  href={img.image_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "block",
                    width: 140,
                    height: 140,
                    borderRadius: 8,
                    overflow: "hidden",
                    border: "1px solid var(--color-border)",
                    backgroundColor: "#F0F4F2",
                  }}
                >
                  <img
                    src={img.thumbnail_url || img.image_url}
                    alt={report.item_name}
                    loading="lazy"
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Metadata Details Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 12,
            paddingTop: 16,
            borderTop: "1px solid var(--color-border)",
            fontSize: "0.85rem",
          }}
        >
          <div>
            <div style={{ color: "var(--color-ink-secondary)", fontSize: "0.78rem" }}>REPORTED LOCATION</div>
            <div style={{ fontWeight: 600, display: "flex", alignItems: "center", gap: 4, marginTop: 2 }}>
              <MapPin size={14} style={{ color: "var(--color-teal)" }} />
              {report.location_text}
            </div>
          </div>

          <div>
            <div style={{ color: "var(--color-ink-secondary)", fontSize: "0.78rem" }}>EVENT DATE</div>
            <div style={{ fontWeight: 600, display: "flex", alignItems: "center", gap: 4, marginTop: 2 }}>
              <Calendar size={14} style={{ color: "var(--color-teal)" }} />
              {report.event_date}
            </div>
          </div>

          <div>
            <div style={{ color: "var(--color-ink-secondary)", fontSize: "0.78rem" }}>NORMALIZED LOCATION</div>
            <div style={{ fontWeight: 500, color: "var(--color-ink-secondary)", marginTop: 2 }}>
              {report.normalized_location}
            </div>
          </div>
        </div>
      </section>

      {/* Ranked Candidate Matches Section */}
      <section style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <div>
            <h2>Ranked Potential Matches</h2>
            <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
              Opposite-type candidate reports ranked using our 4-component heuristic formula.
            </p>
          </div>
          {report.status === "ACTIVE" && (
            <span style={{ fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
              Pool evaluated: <strong>{candidatePoolSize}</strong> active reports
            </span>
          )}
        </div>

        <DisclaimerBanner />

        {isResolved ? (
          <div className="card" style={{ padding: 36, textAlign: "center", color: "var(--color-ink-secondary)" }}>
            <CheckCircle2 size={32} style={{ color: "var(--color-success)", margin: "0 auto 8px" }} />
            <p style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>Report is Resolved</p>
            <p style={{ fontSize: "0.85rem", marginTop: 4 }}>
              Active candidate discovery is disabled for resolved items.
            </p>
          </div>
        ) : matches.length === 0 ? (
          <div className="card" style={{ padding: 36, textAlign: "center", color: "var(--color-ink-secondary)" }}>
            <p style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>No matching candidates found</p>
            <p style={{ fontSize: "0.85rem", marginTop: 4 }}>
              No opposite-type reports currently meet the category or keyword overlap criteria. When someone submits a compatible notice, it will appear here automatically.
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {matches.map((item, idx) => (
              <div
                key={item.candidate.id}
                className="card"
                style={{
                  borderLeft: "4px solid var(--color-teal)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 14,
                }}
              >
                {/* Candidate Header */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          fontWeight: 700,
                          backgroundColor: "var(--color-teal-soft)",
                          color: "var(--color-teal-dark)",
                          padding: "2px 6px",
                          borderRadius: 4,
                        }}
                      >
                        Rank #{idx + 1}
                      </span>
                      <Badge type={item.candidate.type} />
                      <Badge category={item.candidate.category} />
                    </div>
                    <h3
                      style={{ cursor: "pointer", color: "var(--color-teal-dark)" }}
                      onClick={() => onViewCandidate(item.candidate.id)}
                    >
                      {item.candidate.item_name}
                    </h3>
                  </div>

                  <div style={{ display: "flex", gap: 8 }}>
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onViewCandidate(item.candidate.id)}
                    >
                      View Report
                    </Button>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<MessageSquare size={13} />}
                      onClick={() => handleOpenContactModal(item.candidate)}
                    >
                      Request Contact
                    </Button>
                  </div>
                </div>

                {/* Candidate Description */}
                <p className="text-secondary" style={{ fontSize: "0.88rem", lineHeight: 1.5 }}>
                  {item.candidate.description}
                </p>

                {/* Candidate Photos if present */}
                {item.candidate.images && item.candidate.images.length > 0 && (
                  <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
                    {item.candidate.images.map((img) => (
                      <a
                        key={img.id}
                        href={img.image_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          width: 72,
                          height: 72,
                          borderRadius: 6,
                          overflow: "hidden",
                          flexShrink: 0,
                          border: "1px solid var(--color-border)",
                          backgroundColor: "#F0F4F2",
                        }}
                      >
                        <img
                          src={img.thumbnail_url || img.image_url}
                          alt={item.candidate.item_name}
                          loading="lazy"
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      </a>
                    ))}
                  </div>
                )}

                {/* Candidate Details Snippet */}
                <div style={{ display: "flex", gap: 16, fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
                  <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {item.candidate.location_text}</span>
                  <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {item.candidate.event_date}</span>
                </div>

                {/* Score Breakdown Component */}
                <div style={{ marginTop: 4, paddingTop: 12, borderTop: "1px solid var(--color-border)" }}>
                  <ScoreBreakdown
                    totalScore={item.total_score}
                    components={item.components}
                    reasons={item.reasons}
                    sharedKeywords={item.shared_keywords}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Contact Request Modal */}
      <Modal
        isOpen={contactModalOpen}
        onClose={() => setContactModalOpen(false)}
        title="Initiate Safe Contact Request"
      >
        {contactSuccessMsg ? (
          <div className="alert-banner alert-banner-success" style={{ margin: "16px 0" }}>
            {contactSuccessMsg}
          </div>
        ) : (
          <form onSubmit={handleSendContactRequest} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
              Connecting with finder/reporter of: <strong>{selectedCandidate?.item_name}</strong>.
            </p>

            <div className="form-group">
              <label className="form-label" htmlFor="req_name">Your Name</label>
              <input
                id="req_name"
                type="text"
                className="form-input"
                required
                placeholder="e.g. Robin Banks"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="req_email">Your Email Address</label>
              <input
                id="req_email"
                type="email"
                className="form-input"
                required
                placeholder="e.g. robin.b@campus.edu"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="req_msg">Message</label>
              <textarea
                id="req_msg"
                rows={4}
                className="form-textarea"
                required
                value={contactMessage}
                onChange={(e) => setContactMessage(e.target.value)}
              />
              <span className="form-hint">
                Provide identifying details to substantiate ownership without exposing sensitive serials.
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
              <Button type="button" variant="secondary" onClick={() => setContactModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={contactSubmitting}>
                Send Request
              </Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Flag Report Modal */}
      <Modal
        isOpen={flagModalOpen}
        onClose={() => setFlagModalOpen(false)}
        title="Flag Report for Review"
      >
        {flagSuccessMsg ? (
          <div className="alert-banner alert-banner-success" style={{ margin: "16px 0" }}>
            {flagSuccessMsg}
          </div>
        ) : (
          <form onSubmit={handleSendFlag} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
              Help keep LostLink reliable. Flag reports containing inaccurate details, spam, or inappropriate text.
            </p>

            <div className="form-group">
              <label className="form-label" htmlFor="flag_reason">Reason for Flagging</label>
              <textarea
                id="flag_reason"
                rows={3}
                className="form-textarea"
                required
                placeholder="Describe why this report needs moderator review..."
                value={flagReason}
                onChange={(e) => setFlagReason(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
              <Button type="button" variant="secondary" onClick={() => setFlagModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="danger" loading={flagSubmitting}>
                Submit Flag
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
