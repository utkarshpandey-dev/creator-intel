import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Routes that are always public. Everything else requires an authenticated session.
const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/webhooks/(.*)", // Clerk/Stripe webhooks authenticate via signature, not session
]);

export default clerkMiddleware(async (auth, req) => {
  if (!isPublicRoute(req)) {
    // Redirects unauthenticated users to sign-in; enforces org selection downstream.
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next internals and static files, run on everything else.
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpg|jpeg|png|gif|svg|ico|woff2?)).*)",
    "/(api|trpc)(.*)",
    "/__clerk/:path*", // Clerk auto-proxy path (v2 CLI convention)
  ],
};
