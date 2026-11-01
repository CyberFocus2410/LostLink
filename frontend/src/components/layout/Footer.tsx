import React from "react";

interface FooterProps {
  onNavigate?: (page: "privacy" | "terms") => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
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
            Deterministic Inverted Index & Bounded Min-Heap Core. Double-blind privacy protection.
          </p>
        </div>

        <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
          {onNavigate && (
            <>
              <button
                type="button"
                onClick={() => onNavigate("privacy")}
                style={{ background: "none", border: "none", color: "var(--color-teal)", cursor: "pointer", fontSize: "0.82rem", padding: 0 }}
              >
                Privacy Policy
              </button>
              <span>•</span>
              <button
                type="button"
                onClick={() => onNavigate("terms")}
                style={{ background: "none", border: "none", color: "var(--color-teal)", cursor: "pointer", fontSize: "0.82rem", padding: 0 }}
              >
                Terms of Service
              </button>
              <span>•</span>
            </>
          )}
          <span>Weights: 35% C · 25% L · 20% D · 20% K</span>
        </div>
      </div>
    </footer>
  );
};
