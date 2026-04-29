import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  // [C] TODO: forward to Python service and return draft
  const body = await request.json();
  return NextResponse.json({ latex_source: "% TODO", request: body });
}
