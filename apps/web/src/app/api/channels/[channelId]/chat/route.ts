import { apiFetch } from "@/lib/api";

/**
 * Streaming proxy: the browser can't hold the Clerk JWT, so it POSTs here and this
 * server route forwards to FastAPI (attaching the token via apiFetch) and pipes the
 * SSE stream straight back to the client.
 */
export async function POST(
  req: Request,
  { params }: { params: Promise<{ channelId: string }> },
) {
  const { channelId } = await params;
  const body = await req.text();

  const upstream = await apiFetch(`/channels/${channelId}/chat`, {
    method: "POST",
    body,
  });

  if (!upstream.ok || !upstream.body) {
    return new Response("chat unavailable", { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache, no-transform",
    },
  });
}
