/** @type {import('next').NextConfig} */

// Baseline security headers applied to every response. Kept conservative so they don't
// break Clerk's hosted widgets or Stripe Checkout redirects.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
];

const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // NOTE: API_BASE_URL is intentionally NOT declared under `env` here. Doing so inlines it
  // at build time, freezing whatever value was present during the build (e.g. localhost).
  // It is only ever read server-side (apiFetch, webhook routes), so leaving it out lets
  // those reads pick up the real Vercel runtime value on every request.
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
