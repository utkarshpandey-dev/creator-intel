import { NextResponse } from "next/server";
import { apiFetch } from "@/lib/api";

/**
 * Starts the YouTube connect flow. Asks the backend for a Google authorize URL (which
 * carries a signed state binding the request to this org) and redirects the browser to it.
 * The backend's /youtube/oauth/callback handles the return trip.
 */
export async function GET() {
  const res = await apiFetch("/youtube/oauth/start");
  const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";
  if (!res.ok) {
    // 402 = channel cap reached for the current plan → send them to upgrade.
    if (res.status === 402) {
      return NextResponse.redirect(new URL("/dashboard/billing?reason=channel_limit", appUrl));
    }
    return NextResponse.redirect(new URL("/dashboard?connected=0&error=start_failed", appUrl));
  }
  const { authorize_url } = (await res.json()) as { authorize_url: string };
  return NextResponse.redirect(authorize_url);
}
