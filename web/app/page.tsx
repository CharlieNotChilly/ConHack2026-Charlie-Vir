"use client";

import { useState, useCallback } from "react";
import UploadZone from "./components/UploadZone";
import EditorPane from "./components/EditorPane";
import {
  uploadLecture,
  generateAidSheet,
  AidSheetRequest,
  AidSheetDraft,
  IngestResult,
} from "../lib/api";

type Phase = "setup" | "generating" | "editing";

interface UploadEntry {
  filename: string;
  result: IngestResult;
}

function Logo() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
      <rect width="28" height="28" rx="7" fill="url(#logo-grad)" />
      <path d="M7 14h4l2-5 3 10 2-5h3" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="28" y2="28">
          <stop stopColor="#818cf8" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function HomePage() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [uploads, setUploads] = useState<UploadEntry[]>([]);
  const [courseId, setCourseId] = useState("");
  const [targetPages, setTargetPages] = useState(2);
  const [instructions, setInstructions] = useState("");
  const [draft, setDraft] = useState<AidSheetDraft | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFilesAccepted = useCallback(async (files: File[]) => {
    setError(null);
    for (const file of files) {
      try {
        const result = await uploadLecture(file);
        setUploads((prev) => [...prev, { filename: file.name, result }]);
      } catch (err) {
        setError(`Failed to upload ${file.name}: ${err}`);
      }
    }
  }, []);

  const handleGenerate = async () => {
    if (!courseId.trim()) {
      setError("Please enter a Course ID.");
      return;
    }
    setError(null);
    setPhase("generating");
    try {
      const payload: AidSheetRequest = {
        course_id: courseId.trim(),
        target_pages: targetPages,
        instructions: instructions.trim() || undefined,
      };
      const result = await generateAidSheet(payload);
      setDraft(result);
      setPhase("editing");
    } catch (err) {
      setError(`Generation failed: ${err}`);
      setPhase("setup");
    }
  };

  const request: AidSheetRequest = {
    course_id: courseId.trim(),
    target_pages: targetPages,
    instructions: instructions.trim() || undefined,
  };

  if (phase === "editing" && draft) {
    return (
      <EditorPane
        initialLatex={draft.latex_source}
        warnings={draft.warnings}
        request={request}
        onBack={() => setPhase("setup")}
      />
    );
  }

  const isGenerating = phase === "generating";

  return (
    <main style={{ minHeight: "100vh", background: "radial-gradient(ellipse at 20% 0%, #ede9fe 0%, #f0f4ff 35%, #f5f3ff 100%)" }}>
      {/* Header */}
      <header style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 60%, #1a1035 100%)",
        padding: "0 32px",
        height: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Logo />
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: "white", letterSpacing: "-0.3px" }}>
              Lecture → LaTeX
            </div>
            <div style={{ fontSize: 11, color: "#818cf8", marginTop: 1 }}>
              AI-powered aid sheet generator
            </div>
          </div>
        </div>
        <div style={{
          fontSize: 11,
          color: "#4b5563",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: 20,
          padding: "4px 12px",
          letterSpacing: "0.03em",
        }}>
          ConHack 2026
        </div>
      </header>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px 60px" }}>
        {/* Hero line */}
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <h1 style={{ margin: "0 0 8px", fontSize: 26, fontWeight: 700, color: "#1e1b4b", letterSpacing: "-0.5px" }}>
            Generate your aid sheet in seconds
          </h1>
          <p style={{ margin: 0, fontSize: 15, color: "#6b7280" }}>
            Upload lecture PDFs · set constraints · get an editable LaTeX document
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="error-banner" style={{ marginBottom: 24 }}>
            <svg width="16" height="16" viewBox="0 0 20 20" fill="#f87171" style={{ flexShrink: 0, marginTop: 1 }}>
              <path fillRule="evenodd" d="M18 10A8 8 0 1 1 2 10a8 8 0 0 1 16 0zm-8-5a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0v-4.5A.75.75 0 0 1 10 5zm0 10a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" clipRule="evenodd" />
            </svg>
            {error}
          </div>
        )}

        {/* Two-column layout */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, alignItems: "start" }}>

          {/* Step 1: Upload */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div className="step-badge">1</div>
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: "#1e1b4b" }}>
                Upload Lecture PDFs
              </h2>
            </div>
            <UploadZone onFilesAccepted={handleFilesAccepted} />

            {uploads.length > 0 && (
              <ul style={{ margin: "12px 0 0", padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
                {uploads.map((u, i) => (
                  <li key={i} className="file-item">
                    <span className="file-item-name">{u.filename}</span>
                    <span className="file-item-meta">
                      {u.result.pages_indexed}p · {u.result.chunks_indexed} chunks
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {uploads.length === 0 && (
              <p style={{ margin: "12px 0 0", fontSize: 12, color: "#9ca3af", textAlign: "center" }}>
                You can also generate with instructions only — no upload required.
              </p>
            )}
          </div>

          {/* Step 2: Constraints */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
              <div className="step-badge">2</div>
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600, color: "#1e1b4b" }}>
                Set Constraints
              </h2>
            </div>
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              <label className="form-label">
                <span className="label-text">
                  Course ID
                  <span className="label-required">*</span>
                </span>
                <input
                  className="input"
                  type="text"
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value)}
                  placeholder="e.g. CS101, MATH301"
                  onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                />
              </label>

              <label className="form-label">
                <span className="label-text">Target Pages</span>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <input
                    className="input"
                    type="number"
                    min={1}
                    max={10}
                    value={targetPages}
                    onChange={(e) => setTargetPages(Math.max(1, Math.min(10, Number(e.target.value))))}
                    style={{ width: 90 }}
                  />
                  <span style={{ fontSize: 13, color: "#9ca3af" }}>page{targetPages !== 1 ? "s" : ""}</span>
                </div>
              </label>

              <label className="form-label">
                <span className="label-text">Special Instructions</span>
                <textarea
                  className="input"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Include the convolution theorem from lecture 5, focus on integration by parts, prioritize formulas..."
                  rows={5}
                />
              </label>
            </div>
          </div>
        </div>

        {/* Generate CTA */}
        <div style={{ marginTop: 36, display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
          <button
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <div className="spinner" />
                Generating aid sheet...
              </>
            ) : (
              <>
                Generate Aid Sheet
                <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 10a.75.75 0 0 1 .75-.75h10.638L10.23 5.29a.75.75 0 1 1 1.04-1.08l5.5 5.25a.75.75 0 0 1 0 1.08l-5.5 5.25a.75.75 0 1 1-1.04-1.08l4.158-3.96H3.75A.75.75 0 0 1 3 10z" clipRule="evenodd" />
                </svg>
              </>
            )}
          </button>

          {isGenerating && (
            <p style={{ margin: 0, fontSize: 12, color: "#9ca3af", display: "flex", alignItems: "center", gap: 6 }}>
              Retrieving relevant content and composing LaTeX...
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
