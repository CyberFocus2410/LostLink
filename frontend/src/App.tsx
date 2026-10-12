import { useState, useEffect } from "react";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { DashboardPage } from "./pages/DashboardPage";
import { ReportsListPage } from "./pages/ReportsListPage";
import { CreateEditReportPage } from "./pages/CreateEditReportPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { MyReportsPage } from "./pages/MyReportsPage";
import { api } from "./api/client";

type Tab = "dashboard" | "reports" | "create" | "my-reports";

export function App() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const [editReportId, setEditReportId] = useState<string | null>(null);
  const [defaultCreateType, setDefaultCreateType] = useState<"LOST" | "FOUND">("LOST");
  const [reportsFilterType, setReportsFilterType] = useState<string | undefined>(undefined);
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

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
          />
        ) : (
          <DashboardPage
            onNavigateToReports={handleNavigateToReports}
            onNavigateToCreate={handleNavigateToCreate}
            onSelectReport={handleSelectReport}
          />
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
