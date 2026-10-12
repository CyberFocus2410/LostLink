import React from "react";
import { ShieldAlert } from "lucide-react";

interface DisclaimerBannerProps {
  className?: string;
}

export const DisclaimerBanner: React.FC<DisclaimerBannerProps> = ({ className = "" }) => {
  return (
    <div className={`alert-banner alert-banner-disclaimer ${className}`}>
      <ShieldAlert size={18} style={{ flexShrink: 0, marginTop: 2, color: "#9A7137" }} />
      <div>
        <strong>Potential match — not verified ownership.</strong>
        <p style={{ marginTop: 2, fontSize: "0.82rem", color: "#6A5C4B" }}>
          Scores reflect heuristic overlap in category, location, reported date, and keywords. Physical recovery requires verification through official campus procedure.
        </p>
      </div>
    </div>
  );
};
