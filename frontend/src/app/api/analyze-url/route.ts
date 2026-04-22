import { NextResponse } from "next/server";

import { backendJsonHeaders, getBackendApiUrl } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const payload = await request.json();

    const response = await fetch(await getBackendApiUrl("/analyze-url"), {
      method: "POST",
      headers: backendJsonHeaders(),
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    const body = await response.text();

    return new NextResponse(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? error.message
            : "Unable to reach the FastAPI backend. Start the Python API before running the frontend analysis.",
      },
      { status: 502 },
    );
  }
}
