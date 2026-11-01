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
          padding: "8px 16px",
        }}
      >
        {/* Main Bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            minHeight: 46,
          }}
        >
          {/* Brand */}
          <div
            style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", flexShrink: 0 }}
            onClick={() => onTabChange("dashboard")}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "var(--radius-md)",
                backgroundColor: "var(--color-teal)",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 700,
                fontSize: "1rem",
                letterSpacing: "-0.02em",
              }}
            >
              L
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "1.02rem", color: "var(--color-ink-primary)", letterSpacing: "-0.02em", lineHeight: 1.1 }}>
                LostLink
              </div>
              <div style={{ fontSize: "0.68rem", color: "var(--color-ink-secondary)", letterSpacing: "0.01em" }}>
                Campus Matcher
              </div>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav
            className="navbar-desktop-nav"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
            aria-label="Primary"
          >
            <button
              type="button"
              className={`btn ${activeTab === "dashboard" ? "btn-subtle" : "btn-secondary"}`}
              onClick={() => onTabChange("dashboard")}
              style={{
                border: activeTab === "dashboard" ? "1px solid var(--color-sage)" : "1px solid transparent",
                padding: "6px 12px",
                minHeight: 38,
              }}
            >
              <Compass size={15} />
              <span>Overview</span>
            </button>

            <button
              type="button"
              className={`btn ${activeTab === "reports" ? "btn-subtle" : "btn-secondary"}`}
              onClick={() => onTabChange("reports")}
              style={{
                border: activeTab === "reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
                padding: "6px 12px",
                minHeight: 38,
              }}
            >
              <Layers size={15} />
              <span>Browse Reports</span>
            </button>

            <button
              type="button"
              className={`btn ${activeTab === "my-reports" ? "btn-subtle" : "btn-secondary"}`}
              onClick={() => onTabChange("my-reports")}
              style={{
                border: activeTab === "my-reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
                padding: "6px 12px",
                minHeight: 38,
              }}
            >
              <Bookmark size={15} />
              <span>My Reports</span>
            </button>

            {(user?.role === "admin" || user?.role === "moderator") && (
              <button
                type="button"
                className={`btn ${activeTab === "admin" ? "btn-subtle" : "btn-secondary"}`}
                onClick={() => onTabChange("admin")}
                style={{
                  border: activeTab === "admin" ? "1px solid var(--color-teal)" : "1px solid transparent",
                  padding: "6px 12px",
                  minHeight: 38,
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
          <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
            {/* Health indicator */}
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                fontSize: "0.72rem",
                color: "var(--color-ink-secondary)",
                padding: "3px 7px",
                borderRadius: 4,
                backgroundColor: "var(--color-canvas)",
                border: "1px solid var(--color-border)",
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
              <span style={{ fontWeight: 500 }}>
                {isBackendHealthy ? "Live" : "Offline"}
              </span>
            </div>

            {/* User state / Auth actions */}
            {isAuthenticated && user ? (
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    padding: "3px 8px",
                    borderRadius: "var(--radius-sm)",
                    backgroundColor: "var(--color-sage-light)",
                    border: "1px solid var(--color-sage)",
                    fontSize: "0.8rem",
                    fontWeight: 500,
                    color: "var(--color-teal-dark)",
                    maxWidth: 130,
                  }}
                  title={user.email}
                >
                  <UserIcon size={13} style={{ flexShrink: 0 }} />
                  <span style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {user.display_name}
                  </span>
                </div>

                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => logout()}
                  style={{ padding: "4px 8px", minHeight: 34 }}
                  title="Sign Out"
                  aria-label="Sign Out"
                >
                  <LogOut size={13} />
                  <span className="hide-on-mobile" style={{ fontSize: "0.78rem" }}>Logout</span>
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => onOpenAuth("login")}
                style={{ padding: "5px 10px", minHeight: 34, fontSize: "0.82rem" }}
              >
                <LogIn size={14} />
                <span>Sign In</span>
              </button>
            )}

            <Button
              variant="primary"
              size="sm"
              icon={<PlusCircle size={14} />}
              onClick={handleCreateClick}
              style={{ minHeight: 34, padding: "5px 12px", fontSize: "0.82rem", whiteSpace: "nowrap" }}
            >
              <span className="hide-on-mobile">Report Item</span>
              <span className="show-on-mobile">Report</span>
            </Button>
          </div>
        </div>

        {/* Mobile Sub-Navigation Bar (Horizontally scrollable, smooth touch) */}
        <nav
          className="navbar-mobile-nav"
          style={{
            display: "none",
            alignItems: "center",
            gap: 6,
            overflowX: "auto",
            WebkitOverflowScrolling: "touch",
            paddingTop: 8,
            paddingBottom: 2,
            borderTop: "1px solid var(--color-border)",
            marginTop: 6,
          }}
          aria-label="Mobile Navigation"
        >
          <button
            type="button"
            className={`btn ${activeTab === "dashboard" ? "btn-subtle" : "btn-secondary"} btn-sm`}
            onClick={() => onTabChange("dashboard")}
            style={{
              border: activeTab === "dashboard" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "4px 10px",
              minHeight: 32,
              fontSize: "0.82rem",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            <Compass size={14} />
            <span>Overview</span>
          </button>

          <button
            type="button"
            className={`btn ${activeTab === "reports" ? "btn-subtle" : "btn-secondary"} btn-sm`}
            onClick={() => onTabChange("reports")}
            style={{
              border: activeTab === "reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "4px 10px",
              minHeight: 32,
              fontSize: "0.82rem",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            <Layers size={14} />
            <span>Browse</span>
          </button>

          <button
            type="button"
            className={`btn ${activeTab === "my-reports" ? "btn-subtle" : "btn-secondary"} btn-sm`}
            onClick={() => onTabChange("my-reports")}
            style={{
              border: activeTab === "my-reports" ? "1px solid var(--color-sage)" : "1px solid transparent",
              padding: "4px 10px",
              minHeight: 32,
              fontSize: "0.82rem",
              whiteSpace: "nowrap",
              flexShrink: 0,
            }}
          >
            <Bookmark size={14} />
            <span>My Reports</span>
          </button>

          {(user?.role === "admin" || user?.role === "moderator") && (
            <button
              type="button"
              className={`btn ${activeTab === "admin" ? "btn-subtle" : "btn-secondary"} btn-sm`}
              onClick={() => onTabChange("admin")}
              style={{
                border: activeTab === "admin" ? "1px solid var(--color-teal)" : "1px solid transparent",
                padding: "4px 10px",
                minHeight: 32,
                fontSize: "0.82rem",
                color: "var(--color-teal)",
                fontWeight: 600,
                whiteSpace: "nowrap",
                flexShrink: 0,
              }}
            >
              <ShieldAlert size={14} />
              <span>Admin</span>
            </button>
          )}
        </nav>
      </div>
    </header>
  );
};
