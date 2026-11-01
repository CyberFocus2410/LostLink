import React, { useState, useEffect } from "react";
import { Lock, ArrowLeft, LogIn, MapPin, Navigation } from "lucide-react";
import { api } from "../api/client";
import type { ReportType, CategoryEnum, Community, ReportImage } from "../types/api";
import { Button } from "../components/ui/Button";
import { ImageUpload } from "../components/ui/ImageUpload";
import type { PendingImage } from "../components/ui/ImageUpload";
import { useAuth } from "../context/AuthContext";

interface CreateEditReportPageProps {
  editReportId?: string | null;
  defaultType?: "LOST" | "FOUND";
  onCancel: () => void;
  onSuccess: (reportId: string) => void;
  onOpenAuth?: () => void;
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

export const CreateEditReportPage: React.FC<CreateEditReportPageProps> = ({
  editReportId,
  defaultType = "LOST",
  onCancel,
  onSuccess,
  onOpenAuth,
}) => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const isEditing = Boolean(editReportId);

  const [type, setType] = useState<ReportType>(defaultType);
  const [itemName, setItemName] = useState("");
  const [category, setCategory] = useState<CategoryEnum>("ELECTRONICS");
  const [description, setDescription] = useState("");
  const [eventDate, setEventDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [locationText, setLocationText] = useState("");
  const [communities, setCommunities] = useState<Community[]>([]);
  const [communityId, setCommunityId] = useState<string>("");
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");
  const [geoStatus, setGeoStatus] = useState<string | null>(null);

  // Photos
  const [existingImages, setExistingImages] = useState<ReportImage[]>([]);
  const [pendingImages, setPendingImages] = useState<PendingImage[]>([]);

  // Private contact fields — prefill from authenticated user profile
  const [contactName, setContactName] = useState(() => user?.display_name || "");
  const [contactEmail, setContactEmail] = useState(() => user?.email || "");
  const [contactPhone, setContactPhone] = useState("");

  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(isEditing);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState<string | null>(null);

  useEffect(() => {
    api.listCommunities()
      .then((data) => setCommunities(data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (user && !isEditing) {
      if (!contactName) setContactName(user.display_name);
      if (!contactEmail) setContactEmail(user.email);
    }
  }, [user, isEditing]);

  useEffect(() => {
    if (editReportId) {
      loadExistingReport(editReportId);
    }
  }, [editReportId]);

  const loadExistingReport = async (id: string) => {
    setInitialLoading(true);
    try {
      const rep = await api.getReport(id);
      setType(rep.type);
      setItemName(rep.item_name);
      setCategory(rep.category);
      setDescription(rep.description);
      setEventDate(rep.event_date);
      setLocationText(rep.location_text);
      if (rep.community_id) setCommunityId(rep.community_id);
      if (rep.latitude != null) setLatitude(String(rep.latitude));
      if (rep.longitude != null) setLongitude(String(rep.longitude));
      if (rep.images) setExistingImages(rep.images);
    } catch {
      setGeneralError("Failed to load existing report data for editing.");
    } finally {
      setInitialLoading(false);
    }
  };

  const handleDeleteExistingImage = async (imageId: string) => {
    if (!editReportId) return;
    try {
      await api.deleteReportImage(editReportId, imageId);
      setExistingImages((prev) => prev.filter((img) => img.id !== imageId));
    } catch (err: any) {
      setGeneralError(err.message || "Failed to remove image.");
    }
  };

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      setGeoStatus("Geolocation is not supported by your browser.");
      return;
    }
    setGeoStatus("Fetching device GPS coordinates...");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude.toFixed(6));
        setLongitude(pos.coords.longitude.toFixed(6));
        setGeoStatus("GPS coordinates attached!");
        setTimeout(() => setGeoStatus(null), 3000);
      },
      (err) => {
        setGeoStatus("Could not acquire location: " + err.message);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};

    if (!itemName.trim() || itemName.trim().length < 2) {
      errors.item_name = "Item name must be at least 2 characters.";
    }

    if (!description.trim() || description.trim().length < 5) {
      errors.description = "Please provide at least 5 characters of descriptive detail.";
    }

    if (!locationText.trim() || locationText.trim().length < 2) {
      errors.location_text = "Please specify a location (e.g. 'Main Library 2nd Floor').";
    }

    if (!eventDate) {
      errors.event_date = "Please select the date the item was lost or found.";
    } else {
      const today = new Date().toISOString().split("T")[0];
      if (eventDate > today) {
        errors.event_date = "Event date cannot be in the future.";
      }
    }

    if (!isEditing) {
      if (!contactName.trim() || contactName.trim().length < 2) {
        errors.contact_name = "Contact name is required.";
      }
      if (!contactEmail.trim() || !contactEmail.includes("@")) {
        errors.contact_email = "Please enter a valid campus or personal email address.";
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setGeneralError(null);

    try {
      const parsedLat = latitude ? parseFloat(latitude) : undefined;
      const parsedLon = longitude ? parseFloat(longitude) : undefined;
      const validLat = parsedLat !== undefined && !isNaN(parsedLat) ? parsedLat : undefined;
      const validLon = parsedLon !== undefined && !isNaN(parsedLon) ? parsedLon : undefined;

      let targetReportId = editReportId;
      if (isEditing && editReportId) {
        const updated = await api.updateReport(editReportId, {
          item_name: itemName.trim(),
          category,
          description: description.trim(),
          event_date: eventDate,
          location_text: locationText.trim(),
          community_id: communityId || undefined,
          latitude: validLat,
          longitude: validLon,
        });
        targetReportId = updated.id;
      } else {
        const created = await api.createReport({
          type,
          item_name: itemName.trim(),
          category,
          description: description.trim(),
          event_date: eventDate,
          location_text: locationText.trim(),
          community_id: communityId || undefined,
          latitude: validLat,
          longitude: validLon,
          contact_name: contactName.trim(),
          contact_email: contactEmail.trim(),
          contact_phone: contactPhone.trim() || undefined,
        });
        targetReportId = created.id;
      }

      // Upload pending images
      if (targetReportId && pendingImages.length > 0) {
        for (const p of pendingImages) {
          try {
            await api.uploadReportImage(targetReportId, p.file);
          } catch (imgErr) {
            console.error("Image upload warning:", imgErr);
          }
        }
      }

      onSuccess(targetReportId!);
    } catch (err: any) {
      if (err.fields) {
        setFieldErrors(err.fields);
      }
      setGeneralError(err.message || "Failed to submit report. Please review the highlighted fields.");
    } finally {
      setLoading(false);
    }
  };

  if (!isEditing && !authLoading && !isAuthenticated) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center", maxWidth: 520, margin: "40px auto" }}>
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: "50%",
            backgroundColor: "var(--color-sage-light)",
            color: "var(--color-teal)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 16px",
          }}
        >
          <Lock size={24} />
        </div>
        <h3>Authentication Required</h3>
        <p className="text-secondary" style={{ fontSize: "0.88rem", marginTop: 8, marginBottom: 24 }}>
          You must be signed in to submit a lost or found item notice. This allows you to manage, edit, and resolve your reports.
        </p>
        <div style={{ display: "flex", justifyContent: "center", gap: 12 }}>
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="primary" icon={<LogIn size={15} />} onClick={onOpenAuth}>
            Sign In / Register
          </Button>
        </div>
      </div>
    );
  }

  if (initialLoading) {
    return (
      <div className="card" style={{ padding: 48, textAlign: "center", color: "var(--color-ink-secondary)" }}>
        Loading report details...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 680, margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <button
          onClick={onCancel}
          style={{ background: "none", border: "none", cursor: "pointer", color: "var(--color-ink-secondary)", display: "flex", alignItems: "center" }}
        >
          <ArrowLeft size={18} />
        </button>
        <div>
          <h2>{isEditing ? "Edit Report" : "Submit Item Report"}</h2>
          <p className="text-secondary" style={{ fontSize: "0.85rem" }}>
            {isEditing
              ? "Update item details and synchronize matching indexes."
              : "Register a lost or found item. The engine will match opposite reports automatically."}
          </p>
        </div>
      </div>

      {generalError && (
        <div className="alert-banner alert-banner-error">
          {generalError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="card" style={{ padding: "var(--space-6)" }}>
        {/* Report Type Toggle (Only editable on create) */}
        {!isEditing && (
          <div className="form-group" style={{ marginBottom: 20 }}>
            <label className="form-label">Report Type</label>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                type="button"
                className={`btn ${type === "LOST" ? "btn-primary" : "btn-secondary"}`}
                style={{
                  flex: 1,
                  borderColor: type === "LOST" ? "#C04928" : "var(--color-border)",
                  backgroundColor: type === "LOST" ? "#C04928" : "#FFFFFF",
                  color: type === "LOST" ? "#FFFFFF" : "var(--color-ink-primary)",
                }}
                onClick={() => setType("LOST")}
              >
                I Lost an Item
              </button>
              <button
                type="button"
                className={`btn ${type === "FOUND" ? "btn-primary" : "btn-secondary"}`}
                style={{
                  flex: 1,
                  borderColor: type === "FOUND" ? "#386A51" : "var(--color-border)",
                  backgroundColor: type === "FOUND" ? "#386A51" : "#FFFFFF",
                  color: type === "FOUND" ? "#FFFFFF" : "var(--color-ink-primary)",
                }}
                onClick={() => setType("FOUND")}
              >
                I Found an Item
              </button>
            </div>
            <span className="form-hint">
              {type === "LOST"
                ? "You will be matched against reports of found items."
                : "You will be matched against reports from people looking for their lost property."}
            </span>
          </div>
        )}

        {/* Item Name */}
        <div className="form-group">
          <label className="form-label" htmlFor="item_name">
            Item Name <span style={{ color: "var(--color-error)" }}>*</span>
          </label>
          <input
            id="item_name"
            type="text"
            className={`form-input ${fieldErrors.item_name ? "has-error" : ""}`}
            placeholder="e.g. Space Gray MacBook Pro 14-inch"
            value={itemName}
            onChange={(e) => setItemName(e.target.value)}
          />
          {fieldErrors.item_name && <span className="form-error">{fieldErrors.item_name}</span>}
        </div>

        {/* Category & Date Grid */}
        <div className="grid-2">
          <div className="form-group">
            <label className="form-label" htmlFor="category">
              Category <span style={{ color: "var(--color-error)" }}>*</span>
            </label>
            <select
              id="category"
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value as CategoryEnum)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="event_date">
              Event Date <span style={{ color: "var(--color-error)" }}>*</span>
            </label>
            <input
              id="event_date"
              type="date"
              className={`form-input ${fieldErrors.event_date ? "has-error" : ""}`}
              value={eventDate}
              max={new Date().toISOString().split("T")[0]}
              onChange={(e) => setEventDate(e.target.value)}
            />
            {fieldErrors.event_date && <span className="form-error">{fieldErrors.event_date}</span>}
          </div>
        </div>

        {/* Location Text */}
        <div className="form-group">
          <label className="form-label" htmlFor="location_text">
            Location <span style={{ color: "var(--color-error)" }}>*</span>
          </label>
          <input
            id="location_text"
            type="text"
            className={`form-input ${fieldErrors.location_text ? "has-error" : ""}`}
            placeholder="e.g. Main Library 2nd Floor Study Hall"
            value={locationText}
            onChange={(e) => setLocationText(e.target.value)}
          />
          {fieldErrors.location_text ? (
            <span className="form-error">{fieldErrors.location_text}</span>
          ) : (
            <span className="form-hint">Mention the building, floor, room, or landmark.</span>
          )}
        </div>

        {/* Community / Campus Selection */}
        {communities.length > 0 && (
          <div className="form-group">
            <label className="form-label" htmlFor="community">
              Community / Campus <span style={{ color: "var(--color-ink-secondary)", fontWeight: "normal" }}>(Optional)</span>
            </label>
            <select
              id="community"
              className="form-select"
              value={communityId}
              onChange={(e) => setCommunityId(e.target.value)}
            >
              <option value="">Global / No specific community</option>
              {communities.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            <span className="form-hint">Matching is partitioned by community when specified.</span>
          </div>
        )}

        {/* GPS Coordinates (Optional) */}
        <div className="form-group" style={{ backgroundColor: "#F9F9F8", padding: 12, borderRadius: 8, border: "1px solid var(--color-border)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
            <label className="form-label" style={{ marginBottom: 0, display: "flex", alignItems: "center", gap: 6 }}>
              <MapPin size={16} color="var(--color-teal)" />
              GPS Coordinates <span style={{ color: "var(--color-ink-secondary)", fontWeight: "normal", fontSize: "0.8rem" }}>(Optional - Enables Haversine Distance)</span>
            </label>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: "4px 10px", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: 4 }}
              onClick={handleGetLocation}
            >
              <Navigation size={14} /> Detect Current Location
            </button>
          </div>
          {geoStatus && (
            <div style={{ fontSize: "0.8rem", color: "var(--color-teal)", marginBottom: 8 }}>
              {geoStatus}
            </div>
          )}
          <div className="grid-2">
            <div>
              <label style={{ fontSize: "0.75rem", color: "var(--color-ink-secondary)", display: "block", marginBottom: 4 }}>Latitude</label>
              <input
                type="number"
                step="any"
                className="form-input"
                placeholder="e.g. 37.7749"
                value={latitude}
                onChange={(e) => setLatitude(e.target.value)}
              />
            </div>
            <div>
              <label style={{ fontSize: "0.75rem", color: "var(--color-ink-secondary)", display: "block", marginBottom: 4 }}>Longitude</label>
              <input
                type="number"
                step="any"
                className="form-input"
                placeholder="e.g. -122.4194"
                value={longitude}
                onChange={(e) => setLongitude(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Description */}
        <div className="form-group">
          <label className="form-label" htmlFor="description">
            Detailed Description <span style={{ color: "var(--color-error)" }}>*</span>
          </label>
          <textarea
            id="description"
            rows={4}
            className={`form-textarea ${fieldErrors.description ? "has-error" : ""}`}
            placeholder="Include distinctive colors, stickers, brand names, scratches, or contents inside..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            {fieldErrors.description ? (
              <span className="form-error">{fieldErrors.description}</span>
            ) : (
              <span className="form-hint">Descriptive keywords directly power the Jaccard similarity matcher.</span>
            )}
            <span style={{ fontSize: "0.75rem", color: "var(--color-ink-secondary)" }}>
              {description.length} / 1000
            </span>
          </div>
        </div>

        {/* Item Photos */}
        <div style={{ backgroundColor: "#FFFFFF", padding: 16, borderRadius: 8, border: "1px solid var(--color-border)" }}>
          <ImageUpload
            existingImages={existingImages}
            pendingImages={pendingImages}
            onPendingImagesChange={setPendingImages}
            onDeleteExistingImage={isEditing ? handleDeleteExistingImage : undefined}
            disabled={loading}
          />
        </div>

        {/* Private Contact Information (Only when creating) */}
        {!isEditing && (
          <div
            style={{
              marginTop: 18,
              paddingTop: 16,
              borderTop: "1px solid var(--color-border)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 12 }}>
              <Lock size={15} style={{ color: "var(--color-teal)" }} />
              <h4 style={{ fontSize: "0.95rem" }}>Private Contact Details</h4>
            </div>
            <p className="text-secondary" style={{ fontSize: "0.82rem", marginBottom: 14 }}>
              Your contact details are encrypted and kept private. They are never rendered in public search lists or candidate payloads.
            </p>

            <div className="grid-2">
              <div className="form-group">
                <label className="form-label" htmlFor="contact_name">
                  Full Name <span style={{ color: "var(--color-error)" }}>*</span>
                </label>
                <input
                  id="contact_name"
                  type="text"
                  className={`form-input ${fieldErrors.contact_name ? "has-error" : ""}`}
                  placeholder="e.g. Alex Rivera"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                />
                {fieldErrors.contact_name && <span className="form-error">{fieldErrors.contact_name}</span>}
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="contact_email">
                  Email Address <span style={{ color: "var(--color-error)" }}>*</span>
                </label>
                <input
                  id="contact_email"
                  type="email"
                  className={`form-input ${fieldErrors.contact_email ? "has-error" : ""}`}
                  placeholder="e.g. alex.r@campus.edu"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                />
                {fieldErrors.contact_email && <span className="form-error">{fieldErrors.contact_email}</span>}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="contact_phone">
                Phone Number <span style={{ fontSize: "0.8rem", color: "var(--color-ink-secondary)", fontWeight: 400 }}>(Optional)</span>
              </label>
              <input
                id="contact_phone"
                type="tel"
                className="form-input"
                placeholder="e.g. +1 (555) 019-2831"
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 20 }}>
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {isEditing ? "Save Changes" : "Submit & Find Matches"}
          </Button>
        </div>
      </form>
    </div>
  );
};
