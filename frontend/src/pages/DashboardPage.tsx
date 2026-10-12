import React, { useEffect, useState } from "react";
import { Search, PlusCircle, ArrowRight, MapPin, Calendar } from "lucide-react";
import { api } from "../api/client";
import type { ReportItem, MatchResultItem } from "../types/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ScoreBreakdown } from "../components/ui/ScoreBreakdown";
import { DisclaimerBanner } from "../components/ui/DisclaimerBanner";

interface DashboardPageProps {
  onNavigateToReports: (filters?: { type?: string }) => void;
  onNavigateToCreate: (defaultType?: "LOST" | "FOUND") => void;
  onSelectReport: (id: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigateToReports,
  onNavigateToCreate,
  onSelectReport,
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [recentReports, setRecentReports] = useState<ReportItem[]>([]);
  const [stats, setStats] = useState({
    totalActive: 0,
    lostCount: 0,
    foundCount: 0,
    resolvedCount: 0,
  });
  const [spotlightMatch, setSpotlightMatch] = useState<{
    source: ReportItem;
    topMatch: MatchResultItem;
  } | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getReports({ limit: 6, sort: "date_desc" });
      setRecentReports(res.items);

      const [allRes, lostRes, foundRes, resolvedRes] = await Promise.all([
        api.getReports({ status: "ACTIVE", limit: 1 }),
        api.getReports({ type: "LOST", status: "ACTIVE", limit: 1 }),
        api.getReports({ type: "FOUND", status: "ACTIVE", limit: 1 }),
        api.getReports({ status: "RESOLVED", limit: 1 }),
      ]);

      setStats({
        totalActive: allRes.total,
        lostCount: lostRes.total,
        foundCount: foundRes.total,
        resolvedCount: resolvedRes.total,
      });

      const activeLost = res.items.find((r: ReportItem) => r.type === "LOST" && r.status === "ACTIVE");
      if (activeLost) {
        try {
          const matchRes = await api.getMatches(activeLost.id, 1);
          if (matchRes.matches.length > 0) {
            setSpotlightMatch({
              source: activeLost,
              topMatch: matchRes.matches[0],
            });
          }
        } catch {
          // If no matches, spotlight remains null
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-8)" }}>
      {/* Hero / Action Section */}
      <section
        className="card"
        style={{
          padding: "var(--space-8)",
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
        }}
      >
        <div style={{ maxWidth: 640 }}>
          <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--color-teal)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Campus Lost & Found Matcher
          </span>
          <h1 style={{ marginTop: 6, marginBottom: 12 }}>
            Deterministic Item Matching for Campus Recovery
          </h1>
          <p className="text-secondary" style={{ lineHeight: 1.6, marginBottom: 20 }}>
            LostLink pairs lost and found reports using in-memory category clustering, keyword token inverted indexing, and transparent heuristic scoring.
          </p>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Button
              variant="primary"
              icon={<PlusCircle size={16} />}
              onClick={() => onNavigateToCreate("LOST")}
            >
              Report Lost Item
            </Button>
            <Button
              variant="secondary"
              icon={<PlusCircle size={16} />}
              onClick={() => onNavigateToCreate("FOUND")}
            >
              Report Found Item
            </Button>
            <Button
              variant="subtle"
              icon={<Search size={16} />}
              onClick={() => onNavigateToReports()}
            >
              Browse All Reports
            </Button>
          </div>
        </div>
      </section>

      {/* Real Statistics Metrics */}
      <section className="grid-3" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <div className="card" style={{ padding: "var(--space-4)" }}>
          <div className="text-secondary" style={{ fontSize: "0.8rem", fontWeight: 600 }}>ACTIVE REPORTS</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-ink-primary)", marginTop: 4 }}>
            {stats.totalActive}
          </div>
        </div>
        <div className="card" style={{ padding: "var(--space-4)", cursor: "pointer" }} onClick={() => onNavigateToReports({ type: "LOST" })}>
          <div className="text-secondary" style={{ fontSize: "0.8rem", fontWeight: 600 }}>LOST ITEMS</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#C04928", marginTop: 4 }}>
            {stats.lostCount}
          </div>
        </div>
        <div className="card" style={{ padding: "var(--space-4)", cursor: "pointer" }} onClick={() => onNavigateToReports({ type: "FOUND" })}>
          <div className="text-secondary" style={{ fontSize: "0.8rem", fontWeight: 600 }}>FOUND ITEMS</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#386A51", marginTop: 4 }}>
            {stats.foundCount}
          </div>
        </div>
        <div className="card" style={{ padding: "var(--space-4)" }}>
          <div className="text-secondary" style={{ fontSize: "0.8rem", fontWeight: 600 }}>RESOLVED RECOVERIES</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--color-teal)", marginTop: 4 }}>
            {stats.resolvedCount}
          </div>
        </div>
      </section>

      {/* Spotlight Match Spotlight (if real match exists) */}
      {spotlightMatch && (
        <section className="card" style={{ backgroundColor: "var(--color-warm-sand-light)", borderColor: "var(--color-warm-sand)" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
            <div>
              <span style={{ fontSize: "0.78rem", fontWeight: 600, textTransform: "uppercase", color: "var(--color-warning)" }}>
                Active Candidate Match Spotlight
              </span>
              <h3 style={{ marginTop: 2 }}>Potential Match Discovered by Engine</h3>
            </div>
            <Button
              variant="secondary"
              size="sm"
              icon={<ArrowRight size={14} />}
              onClick={() => onSelectReport(spotlightMatch.source.id)}
            >
              Inspect Comparison
            </Button>
          </div>

          <DisclaimerBanner />

          <div className="grid-2" style={{ gap: 16, marginTop: 14 }}>
            {/* Source Lost Report */}
            <div style={{ padding: 14, backgroundColor: "#FFFFFF", borderRadius: 6, border: "1px solid var(--color-border)" }}>
              <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 6 }}>
                <Badge type={spotlightMatch.source.type} />
                <Badge category={spotlightMatch.source.category} />
              </div>
              <h4 style={{ fontSize: "1.05rem" }}>{spotlightMatch.source.item_name}</h4>
              <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4 }}>
                {spotlightMatch.source.description}
              </p>
              <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
                <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {spotlightMatch.source.location_text}</span>
                <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {spotlightMatch.source.event_date}</span>
              </div>
            </div>

            {/* Candidate Found Report */}
            <div style={{ padding: 14, backgroundColor: "#FFFFFF", borderRadius: 6, border: "1px solid var(--color-border)" }}>
              <div style={{ display: "flex", gap: 6, alignItems: "center", marginBottom: 6 }}>
                <Badge type={spotlightMatch.topMatch.candidate.type} />
                <Badge category={spotlightMatch.topMatch.candidate.category} />
              </div>
              <h4 style={{ fontSize: "1.05rem" }}>{spotlightMatch.topMatch.candidate.item_name}</h4>
              <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4 }}>
                {spotlightMatch.topMatch.candidate.description}
              </p>
              <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: "0.8rem", color: "var(--color-ink-secondary)" }}>
                <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {spotlightMatch.topMatch.candidate.location_text}</span>
                <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {spotlightMatch.topMatch.candidate.event_date}</span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 14, padding: 12, backgroundColor: "#FFFFFF", borderRadius: 6, border: "1px solid var(--color-border)" }}>
            <ScoreBreakdown
              totalScore={spotlightMatch.topMatch.total_score}
              components={spotlightMatch.topMatch.components}
              reasons={spotlightMatch.topMatch.reasons}
              sharedKeywords={spotlightMatch.topMatch.shared_keywords}
            />
          </div>
        </section>
      )}

      {/* Recent Reports List */}
      <section>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
          <h2>Recent Activity</h2>
          <Button
            variant="secondary"
            size="sm"
            icon={<ArrowRight size={14} />}
            onClick={() => onNavigateToReports()}
          >
            View All Reports
          </Button>
        </div>

        {loading ? (
          <div className="card" style={{ padding: 32, textAlign: "center", color: "var(--color-ink-secondary)" }}>
            Loading campus reports...
          </div>
        ) : error ? (
          <div className="alert-banner alert-banner-error">
            {error}
          </div>
        ) : recentReports.length === 0 ? (
          <div className="card" style={{ padding: 32, textAlign: "center", color: "var(--color-ink-secondary)" }}>
            No reports filed yet. Use "Report Item" above to submit one.
          </div>
        ) : (
          <div className="grid-3" style={{ gap: 14 }}>
            {recentReports.map((report) => (
              <div
                key={report.id}
                className="card card-interactive"
                style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
                onClick={() => onSelectReport(report.id)}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <Badge type={report.type} />
                    <Badge status={report.status} />
                  </div>
                  <h4 style={{ marginBottom: 4 }}>{report.item_name}</h4>
                  <p className="text-secondary" style={{ fontSize: "0.85rem", lineClamp: 2, WebkitLineClamp: 2, display: "-webkit-box", WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                    {report.description}
                  </p>
                </div>

                <div style={{ marginTop: 12, paddingTop: 10, borderTop: "1px solid var(--color-border)", fontSize: "0.78rem", color: "var(--color-ink-secondary)", display: "flex", justifyContent: "space-between" }}>
                  <span>{report.location_text}</span>
                  <span>{report.event_date}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
