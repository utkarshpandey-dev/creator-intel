import Stripe from "stripe";
import { headers } from "next/headers";

/**
 * Stripe -> our system sync.
 *
 * Same trust model as the Clerk webhook: the browser never writes subscription state. Stripe
 * signs each event; we verify the signature against the raw body here, then forward the
 * validated event to the FastAPI backend (which owns persistence) over an internal shared
 * secret. Only events that change entitlements are forwarded; the rest are acked and ignored.
 *
 * Requires the raw request body, so this route must not be parsed/cached by a body parser —
 * `req.text()` on the App Router gives us the raw payload.
 */

const RELEVANT = new Set([
  "checkout.session.completed",
  "customer.subscription.created",
  "customer.subscription.updated",
  "customer.subscription.deleted",
]);

export async function POST(req: Request) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const apiKey = process.env.STRIPE_SECRET_KEY;
  if (!secret || !apiKey) {
    // Stub/dev mode has no Stripe webhooks; the billing page completes the loop instead.
    return new Response("Stripe not configured", { status: 200 });
  }

  const sig = (await headers()).get("stripe-signature");
  if (!sig) return new Response("Missing signature", { status: 400 });

  const body = await req.text();
  const stripe = new Stripe(apiKey);

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, secret);
  } catch {
    return new Response("Invalid signature", { status: 400 });
  }

  if (RELEVANT.has(event.type)) {
    const res = await fetch(
      `${process.env.API_BASE_URL ?? "http://localhost:8000"}/billing/internal/stripe/sync`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-internal-secret": process.env.INTERNAL_API_SECRET ?? "",
        },
        // Forward the event object (subscription or checkout.session) for the backend to parse.
        body: JSON.stringify({
          type: event.type,
          data: event.data.object,
        }),
      },
    );

    if (!res.ok) {
      // Non-2xx → Stripe retries with backoff instead of dropping the event.
      return new Response("Backend sync failed", { status: 502 });
    }
  }

  return new Response("ok", { status: 200 });
}
