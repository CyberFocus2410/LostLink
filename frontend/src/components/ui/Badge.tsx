import React from "react";
import type { ReportType, ReportStatus, CategoryEnum } from "../../types/api";

interface BadgeProps {
  type?: ReportType;
  status?: ReportStatus;
  category?: CategoryEnum | string;
  children?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({ type, status, category, children }) => {
  if (type) {
    const isLost = type === "LOST";
    return (
      <span className={`badge ${isLost ? "badge-lost" : "badge-found"}`}>
        {type}
      </span>
    );
  }

  if (status) {
    const isActive = status === "ACTIVE";
    return (
      <span className={`badge ${isActive ? "badge-active" : "badge-resolved"}`}>
        {status}
      </span>
    );
  }

  if (category) {
    const formatted = category.replace(/_/g, " ");
    return (
      <span className="badge badge-category">
        {formatted}
      </span>
    );
  }

  return <span className="badge badge-active">{children}</span>;
};
