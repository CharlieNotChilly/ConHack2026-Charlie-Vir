"use client";

import { useCallback, useState } from "react";

interface Props {
  onFilesAccepted: (files: File[]) => Promise<void>;
}

function CloudUploadIcon() {
  return (
    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 16V8m0 0-3 3m3-3 3 3" stroke="#6366f1" />
      <path d="M20.5 16.5A4.5 4.5 0 0 0 16 12h-.75A7.5 7.5 0 1 0 5 18.5" stroke="#6366f1" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="1.5" strokeLinecap="round">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83">
        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite" />
      </path>
    </svg>
  );
}

export default function UploadZone({ onFilesAccepted }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleFiles = useCallback(
    async (files: File[]) => {
      const pdfs = files.filter(
        (f) => f.type === "application/pdf" || f.name.endsWith(".pdf")
      );
      if (pdfs.length === 0) return;
      setIsUploading(true);
      await onFilesAccepted(pdfs);
      setIsUploading(false);
    },
    [onFilesAccepted]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(Array.from(e.dataTransfer.files));
    },
    [handleFiles]
  );

  const zoneClass = [
    "upload-zone",
    isDragging ? "dragging" : "",
    isUploading ? "uploading" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={zoneClass}
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      onClick={() => !isUploading && document.getElementById("pdf-file-input")?.click()}
    >
      <input
        id="pdf-file-input"
        type="file"
        accept=".pdf,application/pdf"
        multiple
        style={{ display: "none" }}
        onChange={(e) => {
          if (e.target.files) handleFiles(Array.from(e.target.files));
          e.target.value = "";
        }}
      />

      {isUploading ? (
        <>
          <SpinnerIcon />
          <p style={{ margin: 0, color: "#6366f1", fontSize: 14, fontWeight: 600 }}>
            Uploading & indexing...
          </p>
          <p style={{ margin: 0, color: "#9ca3af", fontSize: 12 }}>
            Parsing pages and building embeddings
          </p>
        </>
      ) : (
        <>
          <CloudUploadIcon />
          <p style={{ margin: 0, fontWeight: 600, color: "#1e293b", fontSize: 14 }}>
            Drop PDFs here
          </p>
          <p style={{ margin: 0, color: "#9ca3af", fontSize: 12 }}>
            or <span style={{ color: "#6366f1", fontWeight: 500 }}>browse files</span> · multiple supported
          </p>
        </>
      )}
    </div>
  );
}
