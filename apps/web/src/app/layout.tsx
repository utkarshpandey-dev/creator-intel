import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const grotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Creator Intel — The AI operating system for creators",
  description:
    "Creator Intel explains why your content performs, what your audience wants, and what to make next — an AI command center that remembers your channel.",
};

/** Clerk widgets inherit the product's dark identity — no separate theme package. */
const clerkAppearance = {
  variables: {
    colorPrimary: "#6366f1",
    colorBackground: "#0F1219",
    colorText: "#e2e8f0",
    colorTextSecondary: "#94a3b8",
    colorInputBackground: "#161A24",
    colorInputText: "#e2e8f0",
    colorNeutral: "#e2e8f0",
    borderRadius: "0.75rem",
  },
  elements: {
    card: { boxShadow: "0 8px 32px -12px rgba(0,0,0,0.6)" },
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider appearance={clerkAppearance}>
      <html lang="en" className={`dark ${inter.variable} ${grotesk.variable}`} suppressHydrationWarning>
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
