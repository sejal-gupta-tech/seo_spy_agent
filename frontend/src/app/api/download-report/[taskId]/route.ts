import { NextResponse } from "next/server";

import { getBackendApiUrl } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  context: { params: Promise<{ taskId: string }> },
) {
  const { taskId } = await context.params;

  try {
    const response = await fetch(await getBackendApiUrl(`/download-report/${taskId}`), {
      cache: "no-store",
    });

    const buffer = await response.arrayBuffer();
    const headers = new Headers();

    const contentType = response.headers.get("content-type");
    const contentDisposition = response.headers.get("content-disposition");

    if (contentType) {
      headers.set("content-type", contentType);
    }

    if (contentDisposition) {
      headers.set("content-disposition", contentDisposition);
    }

    return new NextResponse(buffer, {
      status: response.status,
      headers,
    });
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error
            ? error.message
            : "Unable to download the report because the FastAPI backend is not reachable.",
      },
      { status: 502 },
    );
  }
}
