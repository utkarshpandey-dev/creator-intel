import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";

// Public landing page. Real marketing content lands with the Dashboard milestone;
// this proves the auth surface end-to-end.
export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-8 px-6 text-center">
      <div className="space-y-4">
        <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">
          Your channel&apos;s <span className="text-brand-600">second brain</span>.
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          creator-intel explains <em>why</em> your content performs, what your audience
          actually wants, and what to make next.
        </p>
      </div>

      <div className="flex items-center gap-4">
        <SignedOut>
          <Link
            href="/sign-up"
            className="rounded-lg bg-brand-600 px-5 py-2.5 font-medium text-white transition hover:bg-brand-700"
          >
            Get started
          </Link>
          <Link
            href="/sign-in"
            className="rounded-lg border border-slate-300 px-5 py-2.5 font-medium transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900"
          >
            Sign in
          </Link>
        </SignedOut>
        <SignedIn>
          <Link
            href="/dashboard"
            className="rounded-lg bg-brand-600 px-5 py-2.5 font-medium text-white transition hover:bg-brand-700"
          >
            Go to dashboard
          </Link>
          <UserButton />
        </SignedIn>
      </div>
    </main>
  );
}
