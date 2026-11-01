import React, { useRef, useState } from "react";
import { Camera, X, AlertCircle } from "lucide-react";
import type { ReportImage } from "../../types/api";

export async function compressImage(file: File, maxDim = 1200, quality = 0.85): Promise<File> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width);
            width = maxDim;
          } else {
            width = Math.round((width * maxDim) / height);
            height = maxDim;
          }
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          resolve(file);
          return;
        }
        ctx.drawImage(img, 0, 0, width, height);
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }
            const compressed = new File([blob], file.name.replace(/\.[^/.]+$/, ".jpg"), {
              type: "image/jpeg",
              lastModified: Date.now(),
            });
            resolve(compressed);
          },
          "image/jpeg",
          quality
        );
      };
      img.onerror = () => resolve(file);
      img.src = e.target?.result as string;
    };
    reader.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });
}

export interface PendingImage {
  file: File;
  previewUrl: string;
}

interface ImageUploadProps {
  existingImages?: ReportImage[];
  pendingImages: PendingImage[];
  onPendingImagesChange: (images: PendingImage[]) => void;
  onDeleteExistingImage?: (imageId: string) => void;
  maxImages?: number;
  disabled?: boolean;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  existingImages = [],
  pendingImages,
  onPendingImagesChange,
  onDeleteExistingImage,
  maxImages = 3,
  disabled = false,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [compressing, setCompressing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const totalCurrent = existingImages.length + pendingImages.length;
  const remainingSlots = Math.max(0, maxImages - totalCurrent);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setErrorMsg(null);

    if (files.length > remainingSlots) {
      setErrorMsg(`You can only add ${remainingSlots} more image${remainingSlots === 1 ? "" : "s"}. Maximum is ${maxImages}.`);
      return;
    }

    setCompressing(true);
    const newPending: PendingImage[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file.type.startsWith("image/")) {
        setErrorMsg("Only image files (JPEG, PNG, WebP) are allowed.");
        continue;
      }
      try {
        const compressed = await compressImage(file);
        newPending.push({
          file: compressed,
          previewUrl: URL.createObjectURL(compressed),
        });
      } catch (err) {
        console.error("Compression error:", err);
      }
    }

    setCompressing(false);
    onPendingImagesChange([...pendingImages, ...newPending]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const removePending = (index: number) => {
    const target = pendingImages[index];
    if (target) {
      URL.revokeObjectURL(target.previewUrl);
    }
    const updated = pendingImages.filter((_, i) => i !== index);
    onPendingImagesChange(updated);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <label className="form-label" style={{ marginBottom: 0 }}>
          Photos of Item <span style={{ color: "#78909C", fontWeight: "normal", fontSize: "0.85rem" }}>(Optional, up to {maxImages})</span>
        </label>
        <span style={{ fontSize: "0.85rem", color: totalCurrent >= maxImages ? "#C62828" : "#546E7A" }}>
          {totalCurrent} / {maxImages}
        </span>
      </div>

      {errorMsg && (
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#C62828", fontSize: "0.85rem", background: "#FFEBEE", padding: "6px 10px", borderRadius: "4px" }}>
          <AlertCircle size={14} />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Grid of existing + pending previews */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(100px, 1fr))", gap: "10px" }}>
        {existingImages.map((img) => (
          <div
            key={img.id}
            style={{
              position: "relative",
              width: "100%",
              aspectRatio: "1/1",
              borderRadius: "6px",
              overflow: "hidden",
              border: "1px solid #DCE8E1",
              background: "#F6F7F4",
            }}
          >
            <img
              src={img.thumbnail_url || img.image_url}
              alt="Report item"
              loading="lazy"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            {onDeleteExistingImage && !disabled && (
              <button
                type="button"
                onClick={() => onDeleteExistingImage(img.id)}
                title="Remove photo"
                style={{
                  position: "absolute",
                  top: "4px",
                  right: "4px",
                  background: "rgba(38, 50, 56, 0.75)",
                  color: "#FFFFFF",
                  border: "none",
                  borderRadius: "50%",
                  width: "24px",
                  height: "24px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>
        ))}

        {pendingImages.map((p, idx) => (
          <div
            key={idx}
            style={{
              position: "relative",
              width: "100%",
              aspectRatio: "1/1",
              borderRadius: "6px",
              overflow: "hidden",
              border: "1px dashed #527C76",
              background: "#F0F4F2",
            }}
          >
            <img
              src={p.previewUrl}
              alt="Pending upload"
              loading="lazy"
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
            <button
              type="button"
              onClick={() => removePending(idx)}
              title="Remove photo"
              style={{
                position: "absolute",
                top: "4px",
                right: "4px",
                background: "rgba(38, 50, 56, 0.75)",
                color: "#FFFFFF",
                border: "none",
                borderRadius: "50%",
                width: "24px",
                height: "24px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
              }}
            >
              <X size={14} />
            </button>
            <span
              style={{
                position: "absolute",
                bottom: "4px",
                left: "4px",
                background: "rgba(38, 50, 56, 0.8)",
                color: "#FFFFFF",
                fontSize: "0.7rem",
                padding: "2px 5px",
                borderRadius: "3px",
              }}
            >
              Ready
            </span>
          </div>
        ))}

        {/* Add photo button if slots remain */}
        {remainingSlots > 0 && !disabled && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={compressing}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "6px",
              aspectRatio: "1/1",
              borderRadius: "6px",
              border: "2px dashed #B0BEC5",
              background: "#FAFAFA",
              color: "#546E7A",
              cursor: "pointer",
              transition: "border-color 0.2s, background 0.2s",
            }}
          >
            {compressing ? (
              <span style={{ fontSize: "0.75rem" }}>Optimizing...</span>
            ) : (
              <>
                <Camera size={22} color="#527C76" />
                <span style={{ fontSize: "0.75rem", fontWeight: 500 }}>Add Photo</span>
              </>
            )}
          </button>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple={remainingSlots > 1}
        onChange={(e) => handleFiles(e.target.files)}
        style={{ display: "none" }}
      />

      <p style={{ margin: 0, fontSize: "0.75rem", color: "#78909C", lineHeight: 1.4 }}>
        Photos are compressed client-side and stripped of GPS metadata before upload. Photos are visible to logged-in users to aid identification.
      </p>
    </div>
  );
};

