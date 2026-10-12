import React, { useEffect, useState } from "react";
import { Bookmark, CheckCircle2, Eye, PlusCircle, MapPin, Calendar } from "lucide-react";
import { api } from "../api/client";
import type { ReportItem } from "../types/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

interface MyReportsPageProps {
  onSelectReport: (id: string) => void;
  onNavigateToCreate: (type?: "LOST" | "FOUND") => void;
}

export const MyReportsPage: React.FC<MyReportsPageProps> = ({
  onSelectReport,
  onNavigateToCreate,
}) => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  useEffect(() => {
    loadMyReports();
  }, []);

  const loadMyReports = async () => {
    setLoading(true);
    try {
      const storedIds: string[] = JSON.parse(
        localStorage.getItem("lostlink_my_reports") || "[]"
      );

      if (storedIds.length === 0) {
        setReports([]);
        setLoading(false);
        return;
      }

      const fetched: ReportItem[] = [];
      for (const id of storedIds) {
        try {
          const item = await api.getReport(id);
          fetched.push(item);
        } catch {
          // Ignore missing IDs
        }
      }
      setReports(fetched);
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2>My Reports</h2>
          <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
            Track notices submitted from this device and manage their resolution state.
          </p>
        </div>
        <Button variant="primary" icon={<PlusCircle size={15} />} onClick={() => onNavigateToCreate()}>
          New Report
        </Button>
      </div>

      {loading ? (
        <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
          Loading your personal reports...
        </div>
      ) : reports.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: "center" }}>
          <Bookmark size={32} style={{ color: "var(--color-teal)", margin: "0 auto 12px" }} />
          <h3>No Personal Reports Filed Yet</h3>
          <p className="text-secondary" style={{ fontSize: "0.88rem", marginTop: 4, marginBottom: 20, maxWidth: 420, marginInline: "auto" }}>
            Reports you file from this browser will appear here so you can check candidate matches and resolve them once returned.
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
              <div style={{ flex: 1, minWidth: 260 }}>
                <div style={{ display: "flex", gap: 6, marginBottom: 4 }}>
                  <Badge type={report.type} />
                  <Badge category={report.category} />
                  <Badge status={report.status} />
                </div>
                <h4 style={{ fontSize: "1.05rem" }}>{report.item_name}</h4>
                <div style={{ display: "flex", gap: 16, marginTop: 6, fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
                  <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {report.location_text}</span>
                  <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {report.event_date}</span>
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
    </div>
  );
};
