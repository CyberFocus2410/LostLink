import React from "react";
import type { MatchComponentScores } from "../../types/api";

interface ScoreBreakdownProps {
  totalScore: number;
  components: MatchComponentScores;
  reasons: string[];
  sharedKeywords: string[];
}

export const ScoreBreakdown: React.FC<ScoreBreakdownProps> = ({
  totalScore,
  components,
  reasons,
  sharedKeywords,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 70) return "var(--color-teal)";
    if (score >= 45) return "var(--color-warning)";
    return "var(--color-ink-secondary)";
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {/* Total Score Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <span style={{ fontSize: "0.78rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em", color: "var(--color-ink-secondary)" }}>
            Heuristic Match Score
          </span>
          <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
            <span style={{ fontSize: "1.75rem", fontWeight: 700, color: getScoreColor(totalScore) }}>
              {Math.round(totalScore)}
            </span>
            <span style={{ fontSize: "0.9rem", color: "var(--color-ink-secondary)" }}>/ 100</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ flex: 1, maxWidth: 180, marginLeft: 16 }}>
          <div style={{ height: 6, width: "100%", backgroundColor: "var(--color-border)", borderRadius: 3, overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: `${Math.min(100, Math.max(0, totalScore))}%`,
                backgroundColor: getScoreColor(totalScore),
                borderRadius: 3,
                transition: "width 0.3s ease",
              }}
            />
          </div>
        </div>
      </div>

      {/* Component Pills */}
      <div className="score-components-grid">
        <div style={{ padding: "4px 8px", backgroundColor: "var(--color-canvas)", borderRadius: 4, border: "1px solid var(--color-border)" }}>
          <div style={{ color: "var(--color-ink-secondary)" }}>Category (35%)</div>
          <div style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>{components.category_score} pts</div>
        </div>
        <div style={{ padding: "4px 8px", backgroundColor: "var(--color-canvas)", borderRadius: 4, border: "1px solid var(--color-border)" }}>
          <div style={{ color: "var(--color-ink-secondary)" }}>Location (25%)</div>
          <div style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>{components.location_score} pts</div>
        </div>
        <div style={{ padding: "4px 8px", backgroundColor: "var(--color-canvas)", borderRadius: 4, border: "1px solid var(--color-border)" }}>
          <div style={{ color: "var(--color-ink-secondary)" }}>Date (20%)</div>
          <div style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>{components.date_score} pts</div>
        </div>
        <div style={{ padding: "4px 8px", backgroundColor: "var(--color-canvas)", borderRadius: 4, border: "1px solid var(--color-border)" }}>
          <div style={{ color: "var(--color-ink-secondary)" }}>Keywords (20%)</div>
          <div style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>{components.keyword_score} pts</div>
        </div>
      </div>

      {/* Shared Keywords */}
      {sharedKeywords.length > 0 && (
        <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap", marginTop: 4 }}>
          <span style={{ fontSize: "0.78rem", color: "var(--color-ink-secondary)", fontWeight: 500 }}>Shared terms:</span>
          {sharedKeywords.map((kw) => (
            <span
              key={kw}
              style={{
                fontSize: "0.75rem",
                padding: "2px 6px",
                backgroundColor: "var(--color-sage-light)",
                color: "var(--color-teal-dark)",
                borderRadius: 4,
                border: "1px solid var(--color-sage)",
              }}
            >
              {kw}
            </span>
          ))}
        </div>
      )}

      {/* Reasons List */}
      <ul style={{ listStyle: "none", padding: 0, marginTop: 4, display: "flex", flexDirection: "column", gap: 4 }}>
        {reasons.map((r, i) => (
          <li
            key={i}
            style={{
              fontSize: "0.82rem",
              color: "var(--color-ink-secondary)",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span style={{ width: 4, height: 4, borderRadius: "50%", backgroundColor: "var(--color-teal)" }} />
            <span>{r}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
