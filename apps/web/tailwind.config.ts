import type { Config } from "tailwindcss";

/**
 * creator-intel design system — dark-first, cinematic, AI-native.
 *
 * Tokens:
 *  - ink.*   deep graphite surface scale (page → raised surfaces)
 *  - brand.* electric indigo accent scale (interactive + AI identity)
 *  - font-display for hero/section headings, font-sans for UI/body
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#04050A", // page background
          900: "#0A0C13", // section background
          800: "#0F1219", // card surface
          700: "#161A24", // raised surface / hover
          600: "#1F2430", // subtle borders on light-glass
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
        },
        electric: "#5EA2FF",
        aiviolet: "#A78BFA",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 24px -6px rgba(99,102,241,0.5)",
        "glow-sm": "0 0 16px -8px rgba(99,102,241,0.55)",
        card: "0 1px 0 0 rgba(255,255,255,0.04) inset, 0 8px 32px -12px rgba(0,0,0,0.6)",
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        aurora: {
          "0%, 100%": { transform: "translate(0,0) scale(1)" },
          "33%": { transform: "translate(4%, -6%) scale(1.08)" },
          "66%": { transform: "translate(-5%, 4%) scale(0.96)" },
        },
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
        "pulse-dot": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
        "gauge-fill": {
          from: { strokeDashoffset: "var(--gauge-circ)" },
          to: { strokeDashoffset: "var(--gauge-offset)" },
        },
        "bar-fill": { from: { width: "0%" }, to: { width: "var(--bar-w)" } },
      },
      animation: {
        "fade-up": "fade-up 0.7s cubic-bezier(0.16,1,0.3,1) both",
        "fade-in": "fade-in 0.6s ease-out both",
        aurora: "aurora 18s ease-in-out infinite",
        "aurora-slow": "aurora 26s ease-in-out infinite reverse",
        shimmer: "shimmer 2.2s linear infinite",
        "pulse-dot": "pulse-dot 1.2s ease-in-out infinite",
        "gauge-fill": "gauge-fill 1.4s cubic-bezier(0.16,1,0.3,1) both",
        "bar-fill": "bar-fill 1.2s cubic-bezier(0.16,1,0.3,1) both",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
