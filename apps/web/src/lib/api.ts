import { auth } from "@clerk/nextjs/server";

/**
 * Server-side helper to call the FastAPI backend on behalf of the signed-in user.
 *
 * It forwards the Clerk session token as a Bearer JWT. FastAPI verifies that token
 * against Clerk's JWKS and derives (user_id, org_id) from it — so the backend never
 * trusts a client-supplied identity. Always call this from Server Components / route
 * handlers, never the browser (the token must not be exposed).
 */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const { getToken } = await auth();
  const token = await getToken();

  const base = process.env.API_BASE_URL ?? "http://localhost:8000";
  const headers = new Headers(init.headers);
  if (token) headers.set("authorization", `Bearer ${token}`);
  headers.set("content-type", "application/json");

  return fetch(`${base}${path}`, { ...init, headers, cache: "no-store" });
}
