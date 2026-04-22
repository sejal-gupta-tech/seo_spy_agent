import { NextResponse } from "next/server";

import { backendJsonHeaders, getBackendApiUrl } from "@/lib/backend";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

export async function POST(request: Request) {
  try {
    const payload = await request.json();

    const response = await fetch(await getBackendApiUrl("/analyze-url/stream"), {
      method: "POST",
      headers: backendJsonHeaders(),
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!response.body) {
      const body = await response.text();
      return new NextResponse(body, {
        status: response.status,
        headers: {
          "content-type":
            response.headers.get("content-type") ?? "application/json",
        },
      });
    }

    return new NextResponse(response.body, {
      status: response.status,
      headers: {
        "content-type":
          response.headers.get("content-type") ??
          "application/x-ndjson; charset=utf-8",
        "cache-control": "no-cache",
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? error.message
            : "Unable to reach the FastAPI backend. Start the Python API before running the streamed analysis.",
      },
      { status: 502 },
    );
  }
}
