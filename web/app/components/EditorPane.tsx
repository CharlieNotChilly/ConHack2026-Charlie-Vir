"use client";

import { useState, useCallback } from "react";
import dynamic from "next/dynamic";
import { previewAidSheet, AidSheetRequest } from "../../lib/api";

const MonacoEditor = dynamic(() => import("@monaco-editor/react"), {
  ssr: false,
  loading: () => (
    <div style={{
      display: "flex", alignItems: "center", justifyContent: "center",
      height: "100%", background: "#0d1117", color: "#4b5563", fontSize: 13,
      gap: 8,
    }}>
      <div className="spinner" style={{ borderTopColor: "#4b5563", borderColor: "rgba(75,85,99,0.3)" }} />
      Loading editor…
    </div>
  ),
});

interface Props {
  initialLatex: string;
  warnings?: string[];
  request: AidSheetRequest;
  onBack: () => void;
}

function LaTeXEmptyState() {
  return (
    <div style={{ textAlign: "center", padding: 32 }}>
      <svg width="56" height="56" viewBox="0 0 56 56" fill="none" style={{ marginBottom: 16, opacity: 0.5 }}>
        <rect width="56" height="56" rx="14" fill="rgba(99,102,241,0.12)" />
        <path d="M16 28h6l4-8 6 16 4-8h4" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M20 40h16" stroke="#818cf8" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <p style={{ margin: "0 0 6px", fontSize: 14, fontWeight: 600, color: "#9ca3af" }}>
        No preview compiled yet
      </p>
      <p style={{ margin: 0, fontSize: 12, color: "#4b5563", lineHeight: 1.6 }}>
        Edit your LaTeX on the left, then click<br />
        <strong style={{ color: "#818cf8" }}>Refresh Preview</strong> to compile
      </p>
    </div>
  );
}

export default function EditorPane({ initialLatex, warnings, request, onBack }: Props) {
  const [latexSource, setLatexSource] = useState(initialLatex);
  const [pdfBase64, setPdfBase64] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const refreshPreview = useCallback(async () => {
    setIsRefreshing(true);
    setPreviewError(null);
    try {
      const result = await previewAidSheet({ ...request, latex_source: latexSource });
      setPdfBase64(result.pdf_base64);
    } catch (err) {
      setPreviewError(String(err));
    } finally {
      setIsRefreshing(false);
    }
  }, [request]);

  const exportLatex = () => {
    const blob = new Blob([latexSource], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${request.course_id}-aid-sheet.tex`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportPdf = () => {
    if (!pdfBase64) return;
    const bytes = atob(pdfBase64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${request.course_id}-aid-sheet.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>

      {/* Toolbar */}
      <div style={{
        height: 56,
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
        display: "flex",
        alignItems: "center",
        padding: "0 16px",
        gap: 10,
        flexShrink: 0,
      }}>
        <button className="btn btn-ghost" onClick={onBack} style={{ padding: "5px 12px", fontSize: 13 }}>
          <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M17 10a.75.75 0 0 1-.75.75H5.612l4.158 3.96a.75.75 0 1 1-1.04 1.08l-5.5-5.25a.75.75 0 0 1 0-1.08l5.5-5.25a.75.75 0 1 1 1.04 1.08L5.612 9.25H16.25A.75.75 0 0 1 17 10z" clipRule="evenodd" />
          </svg>
          Back
        </button>

        <div style={{ width: 1, height: 22, background: "rgba(255,255,255,0.1)", margin: "0 2px" }} />

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            background: "linear-gradient(135deg, #6366f1, #7c3aed)",
            borderRadius: 6,
            padding: "3px 9px",
            fontSize: 12,
            fontWeight: 600,
            color: "white",
            letterSpacing: "0.02em",
          }}>
            {request.course_id}
          </div>
          <span style={{ color: "#4b5563", fontSize: 13 }}>
            {request.target_pages} page{request.target_pages !== 1 ? "s" : ""}
          </span>
        </div>

        <div style={{ flex: 1 }} />

        <button
          className="btn btn-blue"
          onClick={refreshPreview}
          disabled={isRefreshing}
          style={{ fontSize: 13 }}
        >
          {isRefreshing ? (
            <>
              <div className="spinner" />
              Compiling…
            </>
          ) : (
            <>
              <svg width="13" height="13" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M15.312 11.424a5.5 5.5 0 0 1-9.201 2.466l-.312-.311h2.433a.75.75 0 0 0 0-1.5H3.989a.75.75 0 0 0-.75.75v4.242a.75.75 0 0 0 1.5 0v-2.43l.31.31a7 7 0 0 0 11.712-3.138.75.75 0 0 0-1.449-.39Zm1.23-3.723a.75.75 0 0 0 .219-.53V2.929a.75.75 0 0 0-1.5 0v2.43l-.31-.31A7 7 0 0 0 3.239 8.188a.75.75 0 1 0 1.448.389A5.5 5.5 0 0 1 13.89 6.11l.311.31H12a.75.75 0 0 0 0 1.5h4.243a.75.75 0 0 0 .53-.219Z" clipRule="evenodd" />
              </svg>
              Refresh Preview
            </>
          )}
        </button>

        <button className="btn btn-slate" onClick={exportLatex} style={{ fontSize: 13 }}>
          <svg width="13" height="13" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 2.75a.75.75 0 0 0-1.5 0v8.614L6.295 8.235a.75.75 0 1 0-1.09 1.03l4.25 4.5a.75.75 0 0 0 1.09 0l4.25-4.5a.75.75 0 0 0-1.09-1.03l-2.955 3.129V2.75Z" />
            <path d="M3.5 12.75a.75.75 0 0 0-1.5 0v2.5A2.75 2.75 0 0 0 4.75 18h10.5A2.75 2.75 0 0 0 18 15.25v-2.5a.75.75 0 0 0-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5Z" />
          </svg>
          Export .tex
        </button>

        <button
          className="btn btn-accent"
          onClick={exportPdf}
          disabled={!pdfBase64}
          style={{ fontSize: 13 }}
        >
          <svg width="13" height="13" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 2.75a.75.75 0 0 0-1.5 0v8.614L6.295 8.235a.75.75 0 1 0-1.09 1.03l4.25 4.5a.75.75 0 0 0 1.09 0l4.25-4.5a.75.75 0 0 0-1.09-1.03l-2.955 3.129V2.75Z" />
            <path d="M3.5 12.75a.75.75 0 0 0-1.5 0v2.5A2.75 2.75 0 0 0 4.75 18h10.5A2.75 2.75 0 0 0 18 15.25v-2.5a.75.75 0 0 0-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5Z" />
          </svg>
          Export PDF
        </button>
      </div>

      {/* Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="warning-banner">
          <svg width="14" height="14" viewBox="0 0 20 20" fill="#f59e0b" style={{ flexShrink: 0 }}>
            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495ZM10 5a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 10 5Zm0 9a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z" clipRule="evenodd" />
          </svg>
          {warnings.join(" · ")}
        </div>
      )}

      {/* Editor split */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "1fr 1fr", overflow: "hidden" }}>

        {/* Monaco editor */}
        <div style={{ height: "100%", borderRight: "1px solid #1f2937", background: "#0d1117" }}>
          <MonacoEditor
            height="100%"
            language="latex"
            theme="vs-dark"
            value={latexSource}
            onChange={(val) => setLatexSource(val ?? "")}
            options={{
              wordWrap: "on",
              minimap: { enabled: false },
              fontSize: 13,
              lineHeight: 21,
              scrollBeyondLastLine: false,
              lineNumbers: "on",
              renderWhitespace: "none",
              padding: { top: 16, bottom: 16 },
              fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, monospace",
              fontLigatures: true,
              smoothScrolling: true,
              cursorBlinking: "smooth",
              renderLineHighlight: "gutter",
            }}
          />
        </div>

        {/* PDF preview */}
        <div style={{
          height: "100%",
          background: "#1a1a2e",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}>
          {previewError ? (
            <div style={{
              margin: 24,
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.25)",
              borderRadius: 10,
              padding: "16px 20px",
              color: "#fca5a5",
              fontSize: 13,
              textAlign: "center",
              maxWidth: 380,
            }}>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>Preview failed</div>
              {previewError}
            </div>
          ) : pdfBase64 ? (
            <iframe
              src={`data:application/pdf;base64,${pdfBase64}`}
              style={{ width: "100%", height: "100%", border: "none" }}
            />
          ) : (
            <LaTeXEmptyState />
          )}
        </div>
      </div>
    </div>
  );
}
