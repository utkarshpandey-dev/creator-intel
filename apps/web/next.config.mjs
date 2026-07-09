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
  // The FastAPI base URL is read at runtime by server components / route handlers.
  env: {
    API_BASE_URL: process.env.API_BASE_URL ?? "http://localhost:8000",
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
