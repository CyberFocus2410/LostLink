import React, { useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { useAuth } from "../../context/AuthContext";
import { api } from "../../api/client";
import { Lock, Mail, User as UserIcon, AlertCircle, CheckCircle2, KeyRound } from "lucide-react";

export type AuthMode = "login" | "register" | "forgot" | "reset";

interface AuthModalProps {
  isOpen: boolean;
  initialMode?: AuthMode;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  initialMode = "login",
  onClose,
  onSuccess,
}) => {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<AuthMode>(initialMode);

  // Form states
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [infoMsg, setInfoMsg] = useState<string | null>(null);

  // Reset errors when mode changes
  const switchMode = (newMode: AuthMode) => {
    setMode(newMode);
    setErrorMsg(null);
    setFieldErrors({});
    setInfoMsg(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setFieldErrors({});

    try {
      await login({ email: email.trim(), password });
      onSuccess?.();
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Invalid credentials. Please check your email and password.");
      if (err.fields) setFieldErrors(err.fields);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setFieldErrors({});

    // Client-side quick password validation
    if (password.length < 8) {
      setFieldErrors({ password: "Password must be at least 8 characters long." });
      setLoading(false);
      return;
    }
    if (!/[A-Za-z]/.test(password) || !/[0-9]/.test(password)) {
      setFieldErrors({ password: "Password must contain at least one letter and one number." });
      setLoading(false);
      return;
    }

    try {
      await register({
        display_name: displayName.trim(),
        email: email.trim(),
        password,
      });
      onSuccess?.();
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Registration failed. Please check your information.");
      if (err.fields) setFieldErrors(err.fields);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setFieldErrors({});
    setInfoMsg(null);

    try {
      await api.forgotPassword({ email: email.trim() });
      setInfoMsg(
        "If an account exists with this email, password reset instructions have been sent. (Email delivery will be connected in Phase 7)."
      );
    } catch (err: any) {
      setErrorMsg(err.message || "Unable to process request.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setFieldErrors({});
    setInfoMsg(null);

    try {
      await api.resetPassword({
        token: resetToken.trim(),
        new_password: newPassword,
      });
      setInfoMsg("Password has been reset successfully. You can now log in.");
      setTimeout(() => switchMode("login"), 2000);
    } catch (err: any) {
      setErrorMsg(
        err.message || "Password reset via email is not yet available. Please contact support."
      );
    } finally {
      setLoading(false);
    }
  };

  const getTitle = () => {
    switch (mode) {
      case "login":
        return "Sign In to LostLink";
      case "register":
        return "Create an Account";
      case "forgot":
        return "Reset Password";
      case "reset":
        return "Set New Password";
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={getTitle()}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {/* Error notification */}
        {errorMsg && (
          <div className="alert-banner alert-banner-error" role="alert">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>{errorMsg}</div>
          </div>
        )}

        {/* Info / Success notification */}
        {infoMsg && (
          <div className="alert-banner alert-banner-success" role="status">
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>{infoMsg}</div>
          </div>
        )}

        {/* ─────────────── LOGIN FORM ─────────────── */}
        {mode === "login" && (
          <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="login-email">
                Email Address
              </label>
              <div style={{ position: "relative" }}>
                <input
                  id="login-email"
                  type="email"
                  className={`form-input ${fieldErrors.email ? "has-error" : ""}`}
                  placeholder="name@campus.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </div>
              {fieldErrors.email && <span className="form-error">{fieldErrors.email}</span>}
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <label className="form-label" htmlFor="login-password">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => switchMode("forgot")}
                  style={{
                    background: "none",
                    border: "none",
                    color: "var(--color-teal)",
                    fontSize: "0.8rem",
                    cursor: "pointer",
                    textDecoration: "underline",
                  }}
                >
                  Forgot password?
                </button>
              </div>
              <input
                id="login-password"
                type="password"
                className={`form-input ${fieldErrors.password ? "has-error" : ""}`}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {fieldErrors.password && <span className="form-error">{fieldErrors.password}</span>}
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              icon={<Lock size={15} />}
              style={{ width: "100%", marginTop: 6 }}
            >
              {loading ? "Signing In..." : "Sign In"}
            </Button>

            <div style={{ textAlign: "center", fontSize: "0.85rem", marginTop: 8, color: "var(--color-ink-secondary)" }}>
              Don't have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode("register")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-teal)",
                  fontWeight: 600,
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Create one now
              </button>
            </div>
          </form>
        )}

        {/* ─────────────── REGISTER FORM ─────────────── */}
        {mode === "register" && (
          <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="register-name">
                Full Name or Preferred Handle
              </label>
              <input
                id="register-name"
                type="text"
                className={`form-input ${fieldErrors.display_name ? "has-error" : ""}`}
                placeholder="Alex Morgan"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                required
                autoFocus
              />
              {fieldErrors.display_name && (
                <span className="form-error">{fieldErrors.display_name}</span>
              )}
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="register-email">
                Email Address
              </label>
              <input
                id="register-email"
                type="email"
                className={`form-input ${fieldErrors.email ? "has-error" : ""}`}
                placeholder="alex@campus.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              {fieldErrors.email && <span className="form-error">{fieldErrors.email}</span>}
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="register-password">
                Password
              </label>
              <input
                id="register-password"
                type="password"
                className={`form-input ${fieldErrors.password ? "has-error" : ""}`}
                placeholder="At least 8 characters with letters & numbers"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <span className="form-hint" style={{ fontSize: "0.75rem" }}>
                Minimum 8 characters with at least one letter and one number.
              </span>
              {fieldErrors.password && <span className="form-error">{fieldErrors.password}</span>}
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              icon={<UserIcon size={15} />}
              style={{ width: "100%", marginTop: 6 }}
            >
              {loading ? "Creating Account..." : "Create Account"}
            </Button>

            <div style={{ textAlign: "center", fontSize: "0.85rem", marginTop: 8, color: "var(--color-ink-secondary)" }}>
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode("login")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-teal)",
                  fontWeight: 600,
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Sign In
              </button>
            </div>
          </form>
        )}

        {/* ─────────────── FORGOT PASSWORD FORM ─────────────── */}
        {mode === "forgot" && (
          <form onSubmit={handleForgotPassword} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p className="text-secondary" style={{ fontSize: "0.85rem", margin: 0 }}>
              Enter your account email. If registered, we will send instructions to reset your password.
            </p>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="forgot-email">
                Email Address
              </label>
              <input
                id="forgot-email"
                type="email"
                className="form-input"
                placeholder="name@campus.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              icon={<Mail size={15} />}
              style={{ width: "100%", marginTop: 6 }}
            >
              {loading ? "Sending..." : "Send Reset Instructions"}
            </Button>

            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginTop: 8 }}>
              <button
                type="button"
                onClick={() => switchMode("login")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-teal)",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Back to Sign In
              </button>
              <button
                type="button"
                onClick={() => switchMode("reset")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-ink-secondary)",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Have a reset token?
              </button>
            </div>
          </form>
        )}

        {/* ─────────────── RESET PASSWORD FORM (Stub UI) ─────────────── */}
        {mode === "reset" && (
          <form onSubmit={handleResetPassword} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <p className="text-secondary" style={{ fontSize: "0.85rem", margin: 0 }}>
              Enter the reset token received via email and choose a new password.
            </p>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="reset-token">
                Reset Token
              </label>
              <input
                id="reset-token"
                type="text"
                className="form-input"
                placeholder="Paste token here"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label" htmlFor="reset-new-password">
                New Password
              </label>
              <input
                id="reset-new-password"
                type="password"
                className="form-input"
                placeholder="At least 8 characters with letters & numbers"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
              <span className="form-hint" style={{ fontSize: "0.75rem" }}>
                Minimum 8 characters with letters and numbers.
              </span>
            </div>

            <Button
              type="submit"
              variant="primary"
              disabled={loading}
              icon={<KeyRound size={15} />}
              style={{ width: "100%", marginTop: 6 }}
            >
              {loading ? "Updating..." : "Set New Password"}
            </Button>

            <div style={{ textAlign: "center", fontSize: "0.85rem", marginTop: 8 }}>
              <button
                type="button"
                onClick={() => switchMode("login")}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--color-teal)",
                  cursor: "pointer",
                  textDecoration: "underline",
                }}
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </Modal>
  );
};

