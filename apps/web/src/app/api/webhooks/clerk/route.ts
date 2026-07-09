import { Webhook } from "svix";
import { headers } from "next/headers";
import type { WebhookEvent } from "@clerk/nextjs/server";

/**
 * Clerk -> our system sync.
 *
 * Clerk is the source of truth for identity; Postgres holds an application-side mirror so
 * we can attach channels, subscriptions, and AI memory to stable user/org rows without a
 * network call to Clerk on every request.
 *
 * This route verifies the Svix signature (never trust an unsigned webhook) and forwards
 * the validated event to the FastAPI backend, which owns persistence. The forward is
 * authenticated with an internal shared secret so only our web app can call it.
 */
export async function POST(req: Request) {
  const secret = process.env.CLERK_WEBHOOK_SECRET;
  if (!secret) {
    return new Response("Webhook secret not configured", { status: 500 });
  }

  const headerPayload = await headers();
  const svixId = headerPayload.get("svix-id");
  const svixTimestamp = headerPayload.get("svix-timestamp");
  const svixSignature = headerPayload.get("svix-signature");

  if (!svixId || !svixTimestamp || !svixSignature) {
    return new Response("Missing Svix headers", { status: 400 });
  }

  const body = await req.text();

  let event: WebhookEvent;
  try {
    event = new Webhook(secret).verify(body, {
      "svix-id": svixId,
      "svix-timestamp": svixTimestamp,
      "svix-signature": svixSignature,
    }) as WebhookEvent;
  } catch {
    return new Response("Invalid signature", { status: 400 });
  }

  // We only forward events the backend acts on. Others are acknowledged and ignored.
  const relevant = new Set([
    "user.created",
    "user.updated",
    "user.deleted",
    "organization.created",
    "organization.updated",
    "organization.deleted",
    "organizationMembership.created",
    "organizationMembership.deleted",
  ]);

  if (relevant.has(event.type)) {
    const res = await fetch(
      `${process.env.API_BASE_URL ?? "http://localhost:8000"}/internal/clerk/sync`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-internal-secret": process.env.INTERNAL_API_SECRET ?? "",
        },
        body: JSON.stringify({ type: event.type, data: event.data }),
      },
    );

    if (!res.ok) {
      // Return non-2xx so Clerk retries with backoff instead of dropping the event.
      return new Response("Backend sync failed", { status: 502 });
    }
  }

  return new Response("ok", { status: 200 });
}
