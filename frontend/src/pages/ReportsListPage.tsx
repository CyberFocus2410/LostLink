import React, { useEffect, useState } from "react";
import { Search, RefreshCw, ChevronLeft, ChevronRight, MapPin, Calendar } from "lucide-react";
import { api } from "../api/client";
import type { ReportItem, CategoryEnum } from "../types/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";

interface ReportsListPageProps {
  initialType?: string;
  onSelectReport: (id: string) => void;
  onNavigateToCreate: () => void;
}

const CATEGORIES: { label: string; value: CategoryEnum }[] = [
  { label: "Electronics", value: "ELECTRONICS" },
  { label: "Keys & Cards", value: "KEYS_CARDS" },
  { label: "Bags & Wallets", value: "BAGS_WALLETS" },
  { label: "Clothing", value: "CLOTHING" },
  { label: "Documents & Books", value: "DOCUMENTS_BOOKS" },
  { label: "Jewelry & Watches", value: "JEWELRY_WATCHES" },
  { label: "Other", value: "OTHER" },
];

export const ReportsListPage: React.FC<ReportsListPageProps> = ({
  initialType,
  onSelectReport,
  onNavigateToCreate,
}) => {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [q, setQ] = useState("");
  const [type, setType] = useState<string>(initialType || "");
  const [category, setCategory] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [location, setLocation] = useState<string>("");
  const [sort, setSort] = useState<string>("date_desc");
  const [page, setPage] = useState(1);
  const limit = 9;

  useEffect(() => {
    fetchReports();
  }, [type, category, status, sort, page]);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getReports({
        q: q.trim() || undefined,
        type: type || undefined,
        category: category || undefined,
        status: status || undefined,
        location: location.trim() || undefined,
        sort,
        page,
        limit,
      });
      setReports(res.items);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchReports();
  };

  const handleResetFilters = () => {
    setQ("");
    setType("");
    setCategory("");
    setStatus("");
    setLocation("");
    setSort("date_desc");
    setPage(1);
  };

  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2>Browse Reports</h2>
          <p className="text-secondary" style={{ fontSize: "0.88rem" }}>
            Search, filter, and inspect verified campus lost and found notices.
          </p>
        </div>
        <Button variant="primary" onClick={onNavigateToCreate}>
          Report an Item
        </Button>
      </div>

      {/* Filter & Search Bar */}
      <div className="card" style={{ padding: "var(--space-4)" }}>
        <form onSubmit={handleSearchSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Top Row: Search and submit */}
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ position: "relative", flex: 1 }}>
              <input
                type="text"
                className="form-input"
                placeholder="Search by keywords, item name, or description..."
                value={q}
                onChange={(e) => setQ(e.target.value)}
                style={{ paddingLeft: 34 }}
              />
              <Search
                size={16}
                style={{ position: "absolute", left: 10, top: 11, color: "var(--color-ink-secondary)" }}
              />
            </div>
            <Button type="submit" variant="primary" icon={<Search size={15} />}>
              Search
            </Button>
            <Button type="button" variant="secondary" icon={<RefreshCw size={15} />} onClick={handleResetFilters}>
              Reset
            </Button>
          </div>

          {/* Bottom Filter Controls */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 8 }}>
            {/* Type */}
            <select
              className="form-select"
              value={type}
              onChange={(e) => { setType(e.target.value); setPage(1); }}
            >
              <option value="">All Types (Lost & Found)</option>
              <option value="LOST">Lost Only</option>
              <option value="FOUND">Found Only</option>
            </select>

            {/* Category */}
            <select
              className="form-select"
              value={category}
              onChange={(e) => { setCategory(e.target.value); setPage(1); }}
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>

            {/* Status */}
            <select
              className="form-select"
              value={status}
              onChange={(e) => { setStatus(e.target.value); setPage(1); }}
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active Only</option>
              <option value="RESOLVED">Resolved Only</option>
            </select>

            {/* Location */}
            <input
              type="text"
              className="form-input"
              placeholder="Filter location..."
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />

            {/* Sort */}
            <select
              className="form-select"
              value={sort}
              onChange={(e) => { setSort(e.target.value); setPage(1); }}
            >
              <option value="date_desc">Latest Event Date</option>
              <option value="date_asc">Oldest Event Date</option>
              <option value="created_desc">Recently Created</option>
              <option value="created_asc">First Created</option>
            </select>
          </div>
        </form>
      </div>

      {/* Results Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.85rem", color: "var(--color-ink-secondary)" }}>
        <span>Showing <strong>{reports.length}</strong> of <strong>{total}</strong> reports</span>
        <span>Page {page} of {totalPages}</span>
      </div>

      {/* Report Cards Grid */}
      {loading ? (
        <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
          Loading reports from database...
        </div>
      ) : error ? (
        <div className="alert-banner alert-banner-error">
          {error}
        </div>
      ) : reports.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: "center" }}>
          <p style={{ fontWeight: 600, color: "var(--color-ink-primary)" }}>No reports found</p>
          <p className="text-secondary" style={{ fontSize: "0.85rem", marginTop: 4, marginBottom: 16 }}>
            No records matched your current query and filter combination.
          </p>
          <Button variant="secondary" onClick={handleResetFilters}>
            Clear all filters
          </Button>
        </div>
      ) : (
        <div className="grid-3" style={{ gap: 14 }}>
          {reports.map((report) => (
            <div
              key={report.id}
              className="card card-interactive"
              style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}
              onClick={() => onSelectReport(report.id)}
            >
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Badge type={report.type} />
                    <Badge category={report.category} />
                  </div>
                  <Badge status={report.status} />
                </div>
                <h4 style={{ marginBottom: 6 }}>{report.item_name}</h4>
                <p
                  className="text-secondary"
                  style={{
                    fontSize: "0.85rem",
                    lineClamp: 2,
                    WebkitLineClamp: 2,
                    display: "-webkit-box",
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    lineHeight: 1.45,
                  }}
                >
                  {report.description}
                </p>
              </div>

              <div
                style={{
                  marginTop: 14,
                  paddingTop: 10,
                  borderTop: "1px solid var(--color-border)",
                  fontSize: "0.78rem",
                  color: "var(--color-ink-secondary)",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span><MapPin size={12} style={{ verticalAlign: "middle" }} /> {report.location_text}</span>
                <span><Calendar size={12} style={{ verticalAlign: "middle" }} /> {report.event_date}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: 12, marginTop: 12 }}>
          <Button
            variant="secondary"
            size="sm"
            icon={<ChevronLeft size={16} />}
            disabled={page <= 1 || loading}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span style={{ fontSize: "0.85rem", color: "var(--color-ink-secondary)" }}>
            {page} / {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            icon={<ChevronRight size={16} />}
            disabled={page >= totalPages || loading}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
};
