import React from "react";
import { Compass, PlusCircle, Bookmark, Layers, LogIn, LogOut, User as UserIcon, ShieldAlert } from "lucide-react";
import { Button } from "../ui/Button";
import { useAuth } from "../../context/AuthContext";

interface NavbarProps {
  activeTab: string;
  onTabChange: (tab: "dashboard" | "reports" | "create" | "my-reports" | "admin") => void;
  isBackendHealthy: boolean | null;
  onOpenAuth: (mode?: "login" | "register") => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  onTabChange,
  isBackendHealthy,
  onOpenAuth,
}) => {
  const { user, isAuthenticated, logout } = useAuth();

  const handleCreateClick = () => {
    if (!isAuthenticated) {
      onOpenAuth("login");
      return;
    }
    onTabChange("create");
  };

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
          padding: "10px 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        {/* Brand */}
        <div
          style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}
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
            <div style={{ fontWeight: 700, fontSize: "1.08rem", color: "var(--color-ink-primary)", letterSpacing: "-0.02em" }}>
              LostLink
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--color-ink-secondary)", letterSpacing: "0.02em" }}>
              Smart Campus Matcher
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            overflowX: "auto",
            maxWidth: "100%",
            paddingBottom: 2,
          }}
          aria-label="Primary"
        >
          <button
            className={`btn ${activeTab === "dashboard" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("dashboard")}
            style={{
              border: activeTab === "dashboard" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "6px 12px",
              minHeight: 40,
            }}
          >
            <Compass size={15} />
            <span>Overview</span>
          </button>

          <button
            className={`btn ${activeTab === "reports" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("reports")}
            style={{
              border: activeTab === "reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "6px 12px",
              minHeight: 40,
            }}
          >
            <Layers size={15} />
            <span>Browse Reports</span>
          </button>

          <button
            className={`btn ${activeTab === "my-reports" ? "btn-subtle" : "btn-secondary"}`}
            onClick={() => onTabChange("my-reports")}
            style={{
              border: activeTab === "my-reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "6px 12px",
              minHeight: 40,
            }}
          >
            <Bookmark size={15} />
            <span>My Reports</span>
          </button>

          {(user?.role === "admin" || user?.role === "moderator") && (
            <button
              className={`btn ${activeTab === "admin" ? "btn-subtle" : "btn-secondary"}`}
              onClick={() => onTabChange("admin")}
              style={{
                border: activeTab === "admin" ? "1px solid var(--color-teal)" : "1px solid transparent",
                padding: "6px 12px",
                minHeight: 40,
                color: "var(--color-teal)",
                fontWeight: 600,
              }}
            >
              <ShieldAlert size={15} />
              <span>Admin</span>
            </button>
          )}
        </nav>

        {/* Right Actions: Status, Auth & New Report */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {/* Health indicator */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: "0.72rem",
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
              {isBackendHealthy ? "Live" : "Offline"}
            </span>
          </div>

          {/* User state / Auth actions */}
          {isAuthenticated && user ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "4px 10px",
                  borderRadius: "var(--radius-sm)",
                  backgroundColor: "var(--color-sage-light)",
                  border: "1px solid var(--color-sage)",
                  fontSize: "0.82rem",
                  fontWeight: 500,
                  color: "var(--color-teal-dark)",
                }}
                title={user.email}
              >
                <UserIcon size={14} />
                <span style={{ maxWidth: 110, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {user.display_name}
                </span>
              </div>

              <button
                className="btn btn-secondary btn-sm"
                onClick={() => logout()}
                style={{ padding: "6px 10px", minHeight: 38 }}
                title="Sign Out"
                aria-label="Sign Out"
              >
                <LogOut size={14} />
                <span style={{ fontSize: "0.82rem" }}>Logout</span>
              </button>
            </div>
          ) : (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onOpenAuth("login")}
              style={{ padding: "6px 12px", minHeight: 38 }}
            >
              <LogIn size={15} />
              <span>Sign In</span>
            </button>
          )}

          <Button
            variant="primary"
            icon={<PlusCircle size={15} />}
            onClick={handleCreateClick}
            style={{ minHeight: 38, padding: "6px 14px" }}
          >
            Report Item
          </Button>
        </div>
      </div>
    </header>
  );
};
