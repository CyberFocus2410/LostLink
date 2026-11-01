import React, { useState, useEffect, useRef } from "react";
import { Download, RefreshCw, Share, WifiOff, X } from "lucide-react";
import { registerSW } from "virtual:pwa-register";

export const PwaPrompt: React.FC = () => {
  const [needRefresh, setNeedRefresh] = useState(false);
  const [offlineReady, setOfflineReady] = useState(false);
  const updateFunctionRef = useRef<((reloadPage?: boolean) => Promise<void>) | null>(null);

  const [installPrompt, setInstallPrompt] = useState<any>(null);
  const [showIOSHint, setShowIOSHint] = useState(false);

  const [isStandalone] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((window.navigator as any).standalone)
    );
  });

  const [isIOS] = useState(() => {
    if (typeof window === "undefined") return false;
    const ua = window.navigator.userAgent.toLowerCase();
    const isIOSDevice = /iphone|ipad|ipod/.test(ua);
    const isSafari =
      ua.includes("safari") &&
      !ua.includes("chrome") &&
      !ua.includes("crios") &&
      !ua.includes("fxios");
    const standalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      Boolean((window.navigator as any).standalone);
    return isIOSDevice && isSafari && !standalone;
  });

  const [isOffline, setIsOffline] = useState(!navigator.onLine);

  useEffect(() => {
    // Register service worker with update callback
    const updateSW = registerSW({
      onNeedRefresh() {
        setNeedRefresh(true);
      },
      onOfflineReady() {
        setOfflineReady(true);
        setTimeout(() => setOfflineReady(false), 4000);
      },
    });
    updateFunctionRef.current = updateSW;

    // Listen for beforeinstallprompt event (Chromium / Android)
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);

    // Network status listeners
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!installPrompt) return;
    installPrompt.prompt();
    const choice = await installPrompt.userChoice;
    if (choice.outcome === "accepted") {
      setInstallPrompt(null);
    }
  };

  const handleUpdate = async () => {
    if (updateFunctionRef.current) {
      await updateFunctionRef.current(true);
    }
  };

  return (
    <>
      {/* Offline Toast */}
      {isOffline && (
        <div
          role="status"
          style={{
            position: "fixed",
            top: "env(safe-area-inset-top, 0px)",
            left: 0,
            right: 0,
            zIndex: 1000,
            backgroundColor: "#263238",
            color: "#FAF8F5",
            padding: "8px 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            fontSize: "0.85rem",
            boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
          }}
        >
          <WifiOff size={16} color="#E57373" />
          <span>You are currently offline. Cached reports and shell remain available.</span>
        </div>
      )}

      {/* Offline Ready Toast */}
      {offlineReady && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 1000,
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-teal)",
            borderRadius: 8,
            padding: "12px 18px",
            boxShadow: "var(--shadow-card)",
            fontSize: "0.88rem",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ color: "var(--color-teal)", fontWeight: 600 }}>LostLink is ready for offline use.</span>
        </div>
      )}

      {/* Update Available Toast */}
      {needRefresh && (
        <div
          style={{
            position: "fixed",
            bottom: 24,
            right: 24,
            zIndex: 1000,
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-border-dark)",
            borderRadius: 8,
            padding: "14px 18px",
            boxShadow: "var(--shadow-modal)",
            display: "flex",
            alignItems: "center",
            gap: 12,
            maxWidth: 360,
          }}
        >
          <div style={{ flex: 1, fontSize: "0.88rem" }}>
            <div style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>Update Available</div>
            <div style={{ color: "var(--color-ink-secondary)", fontSize: "0.8rem" }}>
              A new version of LostLink is ready.
            </div>
          </div>
          <button
            onClick={handleUpdate}
            className="btn btn-primary btn-sm"
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            onClick={() => setNeedRefresh(false)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-secondary)", padding: 4 }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Install Button Banner (Chrome / Android) */}
      {installPrompt && !isStandalone && (
        <div
          style={{
            position: "fixed",
            bottom: "calc(16px + env(safe-area-inset-bottom, 0px))",
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 900,
            backgroundColor: "var(--color-surface)",
            border: "1px solid var(--color-teal)",
            borderRadius: 30,
            padding: "8px 16px",
            boxShadow: "var(--shadow-modal)",
            display: "flex",
            alignItems: "center",
            gap: 12,
            width: "max-content",
            maxWidth: "92vw",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: 6,
                backgroundColor: "var(--color-teal)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#FFFFFF",
              }}
            >
              <Download size={16} />
            </div>
            <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--color-ink-primary)" }}>
              Install LostLink App
            </span>
          </div>
          <button onClick={handleInstallClick} className="btn btn-primary btn-sm" style={{ borderRadius: 20 }}>
            Install
          </button>
          <button
            onClick={() => setInstallPrompt(null)}
            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-secondary)", padding: 2 }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* iOS Safari Install Button & Guide */}
      {isIOS && !isStandalone && (
        <>
          <div
            style={{
              position: "fixed",
              bottom: "calc(16px + env(safe-area-inset-bottom, 0px))",
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 900,
              backgroundColor: "var(--color-surface)",
              border: "1px solid var(--color-teal)",
              borderRadius: 30,
              padding: "8px 16px",
              boxShadow: "var(--shadow-modal)",
              display: "flex",
              alignItems: "center",
              gap: 10,
              width: "max-content",
              maxWidth: "92vw",
            }}
          >
            <Share size={16} color="var(--color-teal)" />
            <span style={{ fontSize: "0.85rem", color: "var(--color-ink-primary)", fontWeight: 500 }}>
              Install on iPhone
            </span>
            <button
              onClick={() => setShowIOSHint(true)}
              className="btn btn-secondary btn-sm"
              style={{ borderRadius: 20 }}
            >
              How to Install
            </button>
          </div>

          {showIOSHint && (
            <div
              className="modal-backdrop"
              onClick={() => setShowIOSHint(false)}
              style={{
                position: "fixed",
                inset: 0,
                backgroundColor: "rgba(38, 50, 56, 0.45)",
                zIndex: 1100,
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "center",
              }}
            >
              <div
                className="card"
                onClick={(e) => e.stopPropagation()}
                style={{
                  width: "100%",
                  maxWidth: 420,
                  borderBottomLeftRadius: 0,
                  borderBottomRightRadius: 0,
                  padding: 24,
                  animation: "slideUp 0.25s ease-out",
                  border: "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h3 style={{ fontSize: "1.1rem" }}>Install LostLink on iOS</h3>
                  <button
                    onClick={() => setShowIOSHint(false)}
                    style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-secondary)" }}
                  >
                    <X size={20} />
                  </button>
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--color-ink-secondary)", marginBottom: 16 }}>
                  Install LostLink to your home screen for instant full-screen access and offline support:
                </p>
                <ol style={{ paddingLeft: 20, fontSize: "0.9rem", lineHeight: 1.8, marginBottom: 20 }}>
                  <li>
                    Tap the <strong>Share</strong> button <Share size={14} style={{ display: "inline", verticalAlign: "middle" }} /> at the bottom of Safari.
                  </li>
                  <li>Scroll down and tap <strong>"Add to Home Screen"</strong>.</li>
                  <li>Tap <strong>"Add"</strong> in the top right corner.</li>
                </ol>
                <button
                  onClick={() => setShowIOSHint(false)}
                  className="btn btn-primary"
                  style={{ width: "100%" }}
                >
                  Got It
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </>
  );
};
