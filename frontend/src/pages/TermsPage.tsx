import React from "react";
import { ArrowLeft, FileText } from "lucide-react";
import { Button } from "../components/ui/Button";

interface TermsPageProps {
  onBack: () => void;
}

export const TermsPage: React.FC<TermsPageProps> = ({ onBack }) => {
  return (
    <div style={{ maxWidth: 780, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24, paddingBottom: 40 }}>
      <div>
        <Button variant="secondary" size="sm" icon={<ArrowLeft size={15} />} onClick={onBack}>
          Back
        </Button>
      </div>

      <div className="card" style={{ padding: 36 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 8,
              backgroundColor: "var(--color-sage-light)",
              color: "var(--color-teal)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <FileText size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.6rem", margin: 0 }}>Terms of Service</h1>
            <p className="text-secondary" style={{ fontSize: "0.85rem", margin: 0 }}>
              Effective Date: November 2026 | Community Guidelines & Disclaimers
            </p>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20, fontSize: "0.92rem", lineHeight: 1.65, color: "var(--color-ink-primary)" }}>
          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>1. Purpose of the Service</h3>
            <p>
              LostLink is a community recovery coordination platform that pairs lost and found notices using transparent, explainable heuristic scoring. LostLink serves solely as an informational facilitator and does not take custody of items.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>2. Verification of Ownership Disclaimer</h3>
            <p>
              <strong>Heuristic scores are NOT legal proof of ownership.</strong> A high matching score simply indicates that category, approximate location, date, and keyword tokens align. Before transferring custody of any property:
            </p>
            <ul style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              <li>Finders should ask claimants for distinguishing features not mentioned in public listings (e.g., lock screen wallpapers, serial numbers, concealed contents).</li>
              <li>Coordinate item handoffs in well-lit, public locations such as a campus security office, student union, or library front desk.</li>
            </ul>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>3. Prohibited Conduct</h3>
            <p>Users agree NOT to:</p>
            <ul style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              <li>Post fraudulent, spam, or misleading reports.</li>
              <li>Upload offensive, illegal, or infringing imagery.</li>
              <li>Attempt to scrape, harass, or abuse community members through contact requests.</li>
            </ul>
            <p style={{ marginTop: 8 }}>
              Violations will result in immediate content removal and permanent account deactivation.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>4. Limitation of Liability</h3>
            <p>
              LostLink and its operators shall not be liable for damaged, unrecovered, or disputed items, or for interactions between community members.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

