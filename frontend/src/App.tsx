import { useState, useEffect } from "react";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { DashboardPage } from "./pages/DashboardPage";
import { ReportsListPage } from "./pages/ReportsListPage";
import { CreateEditReportPage } from "./pages/CreateEditReportPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { MyReportsPage } from "./pages/MyReportsPage";
import { PrivacyPolicyPage } from "./pages/PrivacyPolicyPage";
import { TermsPage } from "./pages/TermsPage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { AuthModal, type AuthMode } from "./components/auth/AuthModal";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { PwaPrompt } from "./components/pwa/PwaPrompt";
import { api } from "./api/client";

type Tab = "dashboard" | "reports" | "create" | "my-reports" | "privacy" | "terms" | "admin";

function AppContent() {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [editReportId, setEditReportId] = useState<string | null>(null);
  const [defaultCreateType, setDefaultCreateType] = useState<"LOST" | "FOUND">("LOST");
  const [reportsFilterType, setReportsFilterType] = useState<string | undefined>(undefined);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  // Auth Modal state
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<AuthMode>("login");

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      await api.getHealth();
      setIsBackendHealthy(true);
    } catch {
      setIsBackendHealthy(false);
    }
  };

  const handleOpenAuth = (mode: AuthMode = "login") => {
    setAuthModalMode(mode);
    setAuthModalOpen(true);
  };

  const handleSelectReport = (id: string) => {
    setSelectedReportId(id);
    setEditReportId(null);
  };

  const handleNavigateToReports = (filters?: { type?: string }) => {
    setSelectedReportId(null);
    setEditReportId(null);
    setReportsFilterType(filters?.type);
    setActiveTab("reports");
  };

  const handleNavigateToCreate = (defaultType: "LOST" | "FOUND" = "LOST") => {
    setSelectedReportId(null);
    setEditReportId(null);
    setDefaultCreateType(defaultType);
    if (!isAuthenticated) {
      handleOpenAuth("login");
    }
    setActiveTab("create");
  };

  const handleEditReport = (id: string) => {
    setEditReportId(id);
    setSelectedReportId(null);
    setActiveTab("create");
  };

  return (
    <div className="app-container">
      <Navbar
        activeTab={activeTab}
        onTabChange={(tab) => {
          setSelectedReportId(null);
          setEditReportId(null);
          setActiveTab(tab);
        }}
        isBackendHealthy={isBackendHealthy}
        onOpenAuth={(mode) => handleOpenAuth(mode || "login")}
      />

      <main className="main-content">
        {selectedReportId ? (
          <ReportDetailPage
            reportId={selectedReportId}
            onBack={() => setSelectedReportId(null)}
            onEdit={handleEditReport}
            onViewCandidate={handleSelectReport}
          />
        ) : activeTab === "create" ? (
          <CreateEditReportPage
            editReportId={editReportId}
            defaultType={defaultCreateType}
            onCancel={() => {
              setEditReportId(null);
              setActiveTab("dashboard");
            }}
            onSuccess={(newId) => {
              setEditReportId(null);
              setSelectedReportId(newId);
            }}
            onOpenAuth={() => handleOpenAuth("login")}
          />
        ) : activeTab === "reports" ? (
          <ReportsListPage
            initialType={reportsFilterType}
            onSelectReport={handleSelectReport}
            onNavigateToCreate={() => handleNavigateToCreate("LOST")}
          />
        ) : activeTab === "my-reports" ? (
          <MyReportsPage
            onSelectReport={handleSelectReport}
            onNavigateToCreate={handleNavigateToCreate}
            onOpenAuth={() => handleOpenAuth("login")}
          />
        ) : activeTab === "admin" ? (
          <AdminDashboardPage
            onNavigateToDetail={(id) => {
              setSelectedReportId(id);
              setEditReportId(null);
            }}
          />
        ) : activeTab === "privacy" ? (
          <PrivacyPolicyPage onBack={() => setActiveTab("dashboard")} />
        ) : activeTab === "terms" ? (
          <TermsPage onBack={() => setActiveTab("dashboard")} />
        ) : (
          <DashboardPage
            onNavigateToReports={handleNavigateToReports}
            onNavigateToCreate={handleNavigateToCreate}
            onSelectReport={handleSelectReport}
          />
        )}
      </main>

      <Footer
        onNavigate={(page) => {
          setSelectedReportId(null);
          setEditReportId(null);
          setActiveTab(page);
        }}
      />

      <AuthModal
        isOpen={authModalOpen}
        initialMode={authModalMode}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={() => {
          setAuthModalOpen(false);
        }}
      />

      <PwaPrompt />
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
