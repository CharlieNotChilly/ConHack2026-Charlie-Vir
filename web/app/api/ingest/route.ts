import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: NextRequest) {
  const formData = await request.formData();
  try {
    const res = await fetch(`${BACKEND}/ingest/upload`, {
      method: "POST",
      body: formData,
    });
    const text = await res.text();
    let data: unknown = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }

    if (!res.ok) {
      return NextResponse.json(
        {
          error: "Backend error",
          status: res.status,
          detail: data || res.statusText,
        },
        { status: res.status }
      );
    }

    return NextResponse.json(data ?? {}, { status: res.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json(
      {
        error: "Backend request failed",
        detail: message,
        backend: BACKEND,
      },
      { status: 502 }
    );
  }
}
