import React from "react";

export const Footer: React.FC = () => {
  return (
    <footer
      style={{
        backgroundColor: "var(--color-surface)",
        borderTop: "1px solid var(--color-border)",
        padding: "24px 16px",
        marginTop: "auto",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 16,
          fontSize: "0.82rem",
          color: "var(--color-ink-secondary)",
        }}
      >
        <div>
          <strong style={{ color: "var(--color-ink-primary)" }}>LostLink</strong> — Smart Lost & Found Matcher
          <p style={{ marginTop: 2, fontSize: "0.78rem" }}>
            Campus Problem-Based Learning (PBL) System. Deterministic Inverted Index & Bounded Min-Heap Core.
          </p>
        </div>

        <div style={{ display: "flex", gap: 16 }}>
          <span>Weights: 35% C · 25% L · 20% D · 20% K</span>
          <span>•</span>
          <span>Decay: 15 pts/day</span>
        </div>
      </div>
    </footer>
  );
};
