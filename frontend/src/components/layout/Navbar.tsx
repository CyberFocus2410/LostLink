import React from "react";
import { Compass, PlusCircle, Bookmark, Layers } from "lucide-react";
import { Button } from "../ui/Button";

interface NavbarProps {
  activeTab: "dashboard" | "reports" | "create" | "my-reports";
  onTabChange: (tab: "dashboard" | "reports" | "create" | "my-reports") => void;
  isBackendHealthy: boolean | null;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  isBackendHealthy,
}) => {
  return (
    <header
      style={{
        backgroundColor: "var(--color-surface)",
        borderBottom: "1px solid var(--color-border)",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
          padding: "12px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Brand */}
        <div
          style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }}
          onClick={() => onTabChange("dashboard")}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: "var(--radius-md)",
              backgroundColor: "var(--color-teal)",
              color: "#FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 700,
              fontSize: "1.05rem",
              letterSpacing: "-0.02em",
            }}
          >
            L
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem", color: "var(--color-ink-primary)", letterSpacing: "-0.02em" }}>
              LostLink
            </div>
            <div style={{ fontSize: "0.72rem", color: "var(--color-ink-secondary)", letterSpacing: "0.02em" }}>
              Smart Campus Matcher
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <button
            className={`btn ${activeTab === "dashboard" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("dashboard")}
            style={{ border: activeTab === "dashboard" ? "1px solid var(--color-sage)" : "1px solid transparent" }}
          >
            <Compass size={16} />
            <span>Overview</span>
          </button>

          <button
            className={`btn ${activeTab === "reports" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("reports")}
            style={{ border: activeTab === "reports" ? "1px solid var(--color-sage)" : "1px solid transparent" }}
          >
            <Layers size={16} />
            <span>Browse Reports</span>
          </button>

          <button
            className={`btn ${activeTab === "my-reports" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("my-reports")}
            style={{ border: activeTab === "my-reports" ? "1px solid var(--color-sage)" : "1px solid transparent" }}
          >
            <Bookmark size={16} />
            <span>My Reports</span>
          </button>
        </nav>

        {/* Actions & Health Dot */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {/* Health indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.75rem",
              color: "var(--color-ink-secondary)",
              padding: "4px 8px",
              borderRadius: 4,
              backgroundColor: "var(--color-canvas)",
            }}
            title={isBackendHealthy ? "Backend API Online" : "Backend Disconnected"}
          >
            <span
              style={{
                width: 7,
                height: 7,
                borderRadius: "50%",
                backgroundColor: isBackendHealthy ? "var(--color-success)" : "var(--color-error)",
              }}
            />
            <span>
              {isBackendHealthy ? "API Live" : "Offline"}
            </span>
          </div>

          <Button
            variant="primary"
            icon={<PlusCircle size={16} />}
            onClick={() => onTabChange("create")}
          >
            Report Item
          </Button>
        </div>
      </div>
    </header>
  );
};
