export interface IngestResult {
  lecture_id: string;
  pages_indexed: number;
  chunks_indexed: number;
  source_path: string;
}

export interface AidSheetRequest {
  course_id: string;
  target_pages: number;
  instructions?: string;
}

export interface AidSheetDraft {
  latex_source: string;
  warnings?: string[];
}

export interface AidSheetPreview {
  latex_source: string;
  pdf_base64: string;
  warnings?: string[];
}

export async function uploadLecture(file: File): Promise<IngestResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/ingest", { method: "POST", body: form });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Upload failed: ${text}`);
  }
  return res.json();
}

export async function generateAidSheet(payload: AidSheetRequest): Promise<AidSheetDraft> {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Generation failed: ${text}`);
  }
  return res.json();
}

export async function previewAidSheet(payload: AidSheetRequest): Promise<AidSheetPreview> {
  const res = await fetch("/api/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Preview failed: ${text}`);
  }
  return res.json();
}
