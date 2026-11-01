import React from "react";
import { ArrowLeft, Shield } from "lucide-react";
import { Button } from "../components/ui/Button";

interface PrivacyPolicyPageProps {
  onBack: () => void;
}

export const PrivacyPolicyPage: React.FC<PrivacyPolicyPageProps> = ({ onBack }) => {
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
            <Shield size={24} />
          </div>
          <div>
            <h1 style={{ fontSize: "1.6rem", margin: 0 }}>Privacy Policy</h1>
            <p className="text-secondary" style={{ fontSize: "0.85rem", margin: 0 }}>
              Effective Date: November 2026 | LostLink Data Protection Notice
            </p>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 20, fontSize: "0.92rem", lineHeight: 1.65, color: "var(--color-ink-primary)" }}>
          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>1. Our Privacy Pledge</h3>
            <p>
              LostLink is designed from the ground up with <strong>privacy-first defaults</strong>. Unlike public forums or social media bulletin boards, LostLink never exposes your email address, phone number, or raw location data to web scrapers or unauthorized third parties.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>2. Double-Blind Contact Guarantee</h3>
            <p>
              When you submit a lost or found report, your direct contact details are stored securely and encrypted in our database. When another user finds a potential match and submits a contact request:
            </p>
            <ul style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              <li>The requester <strong>never</strong> sees your email address or phone number.</li>
              <li>You receive a notification and can review the requester's description of the item.</li>
              <li>Only if you explicitly click <strong>"Accept"</strong> are both parties' direct contact methods revealed so you can coordinate recovery.</li>
              <li>If you decline, the requester receives no personal contact information.</li>
            </ul>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>3. Photo Uploads & EXIF Metadata Sanitization</h3>
            <p>
              When you upload photos to assist with item identification, LostLink automatically strips all <strong>EXIF metadata</strong>, including embedded GPS coordinates, camera serial numbers, and device timestamps, before saving files to cloud object storage. Uploaded photos are accessible to authenticated community members to facilitate matching.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>4. Security & Cookie Architecture</h3>
            <p>
              Authentication tokens are stored strictly in <code>httpOnly</code>, <code>SameSite=Lax</code>, and <code>Secure</code> cookies. Tokens are never exposed in JavaScript <code>localStorage</code> or API JSON bodies, preventing XSS-based credential theft. All mutating operations enforce Origin header validation to guard against CSRF attacks.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: "1.1rem", marginBottom: 8, color: "var(--color-ink-primary)" }}>5. Compliance with DPDP Act & GDPR (Right to Erasure)</h3>
            <p>
              In full compliance with India's <strong>Digital Personal Data Protection Act (DPDP Act 2023)</strong> and international data protection standards (GDPR):
            </p>
            <ul style={{ paddingLeft: 20, display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              <li><strong>Right to Erase:</strong> You may invoke "Delete My Account & Personal Data" at any time from your account settings.</li>
              <li><strong>Immediate Anonymization:</strong> All personal identifiers (display name, email, phone) are scrubbed and replaced with non-identifying hashes. All active sessions are terminated immediately.</li>
            </ul>
          </section>

          <section style={{ borderTop: "1px solid var(--color-border)", paddingTop: 16 }}>
            <p style={{ fontSize: "0.82rem", color: "var(--color-ink-secondary)", margin: 0 }}>
              Questions about our privacy practices? Contact privacy@lostlink.org or submit an inquiry through our moderation portal.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

