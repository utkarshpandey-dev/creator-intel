import Link from "next/link";
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs";
import {
  Brain,
  TrendingUp,
  MessageSquareText,
  Sparkles,
  Zap,
  Users,
  Youtube,
  LineChart,
  ArrowRight,
  Check,
} from "lucide-react";

const features = [
  {
    icon: TrendingUp,
    title: "Why content performs",
    body: "Go beyond views. We explain the actual reasons a video pops or flops — hook, topic, timing, audience fit — so you can repeat what works.",
  },
  {
    icon: MessageSquareText,
    title: "What your audience wants",
    body: "Thousands of comments distilled into clear themes, requests, and complaints — the signal in the noise, ranked by what matters.",
  },
  {
    icon: Sparkles,
    title: "What to make next",
    body: "Concrete, prioritized content ideas grounded in your own data and audience — not generic advice you've heard a hundred times.",
  },
  {
    icon: Brain,
    title: "Memory that compounds",
    body: "We remember every channel. Month three is smarter than month one — advice builds on your history instead of starting from scratch.",
  },
  {
    icon: Zap,
    title: "Cost-optimized analysis",
    body: "A filter → dedupe → cluster → reason pipeline means we analyze 50,000 comments for the price of a few — insight without the burn.",
  },
  {
    icon: Users,
    title: "Built for agencies too",
    body: "Manage many creators from one workspace, each isolated and secure. Solo creator or agency of fifty — it scales with you.",
  },
];

const steps = [
  {
    icon: Youtube,
    title: "Connect your channel",
    body: "Securely link YouTube in one click. We auto-import your videos, stats, and comments — no CSVs, no manual work.",
  },
  {
    icon: LineChart,
    title: "AI analyzes everything",
    body: "Performance, sentiment, and audience themes are processed into structured, explainable insight.",
  },
  {
    icon: Sparkles,
    title: "Get your strategy",
    body: "A clear report: what's working, what your audience wants, and exactly what to make next.",
  },
  {
    icon: MessageSquareText,
    title: "Chat with your data",
    body: "Ask anything about your channel and get answers grounded in your real numbers and audience.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {/* Nav */}
      <header className="sticky top-0 z-50 border-b border-slate-200/70 bg-white/80 backdrop-blur-md dark:border-slate-800/70 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <Brain className="h-5 w-5" />
            </span>
            <span className="text-lg tracking-tight">creator-intel</span>
          </Link>
          <nav className="hidden items-center gap-8 text-sm text-slate-600 dark:text-slate-300 md:flex">
            <a href="#features" className="transition hover:text-slate-900 dark:hover:text-white">
              Features
            </a>
            <a href="#how" className="transition hover:text-slate-900 dark:hover:text-white">
              How it works
            </a>
          </nav>
          <div className="flex items-center gap-3">
            <SignedOut>
              <Link
                href="/sign-in"
                className="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                Sign in
              </Link>
              <Link
                href="/sign-up"
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Get started
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Dashboard
              </Link>
              <UserButton />
            </SignedIn>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 bg-gradient-to-b from-brand-50/80 via-white to-white dark:from-brand-600/10 dark:via-slate-950 dark:to-slate-950"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-[-10rem] -z-10 h-[30rem] w-[60rem] -translate-x-1/2 rounded-full bg-brand-500/20 blur-3xl dark:bg-brand-600/20"
        />
        <div className="mx-auto max-w-4xl px-6 pb-20 pt-20 text-center sm:pt-28">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-sm font-medium text-brand-700 dark:border-brand-500/30 dark:bg-brand-500/10 dark:text-brand-500">
            <Sparkles className="h-4 w-4" />
            AI Creator Intelligence
          </span>
          <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-6xl">
            Your channel&apos;s{" "}
            <span className="bg-gradient-to-r from-brand-600 to-brand-500 bg-clip-text text-transparent">
              second brain
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 dark:text-slate-300">
            creator-intel explains <em>why</em> your content performs, what your audience
            actually wants, and exactly what to make next — and it remembers your channel so
            the advice compounds over time.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <SignedOut>
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Start free <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/sign-in"
                className="rounded-lg border border-slate-300 px-6 py-3 font-medium transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900"
              >
                Sign in
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Go to your dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            </SignedIn>
          </div>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-500 dark:text-slate-400">
            <span className="inline-flex items-center gap-1.5">
              <Check className="h-4 w-4 text-brand-600" /> Connect YouTube in one click
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Check className="h-4 w-4 text-brand-600" /> No CSVs, no manual work
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Check className="h-4 w-4 text-brand-600" /> Insight in minutes
            </span>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Analytics tells you <span className="text-slate-400">what</span>. We tell you{" "}
            <span className="text-brand-600">why</span>.
          </h2>
          <p className="mt-4 text-slate-600 dark:text-slate-300">
            The moat isn&apos;t another dashboard — it&apos;s the reasoning layer and the
            memory that make your strategy smarter every month.
          </p>
        </div>
        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="group rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-brand-300 hover:shadow-lg dark:border-slate-800 dark:bg-slate-900 dark:hover:border-brand-500/40"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600 transition group-hover:bg-brand-600 group-hover:text-white dark:bg-brand-500/10">
                <Icon className="h-6 w-6" />
              </span>
              <h3 className="mt-5 text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                {body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="border-y border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              From channel to strategy in four steps
            </h2>
            <p className="mt-4 text-slate-600 dark:text-slate-300">
              Sign up, connect, and let the AI do the heavy lifting.
            </p>
          </div>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map(({ icon: Icon, title, body }, i) => (
              <div key={title} className="relative rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
                <div className="flex items-center justify-between">
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-600 text-white">
                    <Icon className="h-6 w-6" />
                  </span>
                  <span className="text-4xl font-bold text-slate-100 dark:text-slate-800">
                    {i + 1}
                  </span>
                </div>
                <h3 className="mt-5 text-base font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
                  {body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-600 to-brand-700 px-8 py-16 text-center shadow-xl">
          <div aria-hidden className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.15),transparent_60%)]" />
          <h2 className="relative text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Ready to understand your channel?
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-brand-50">
            Connect YouTube and get your first strategy report in minutes.
          </p>
          <div className="relative mt-8 flex justify-center">
            <SignedOut>
              <Link
                href="/sign-up"
                className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 font-medium text-brand-700 shadow-sm transition hover:bg-brand-50"
              >
                Get started free <ArrowRight className="h-4 w-4" />
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 font-medium text-brand-700 shadow-sm transition hover:bg-brand-50"
              >
                Open dashboard <ArrowRight className="h-4 w-4" />
              </Link>
            </SignedIn>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 text-sm text-slate-500 dark:text-slate-400 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-600 text-white">
              <Brain className="h-4 w-4" />
            </span>
            <span className="font-medium text-slate-700 dark:text-slate-300">creator-intel</span>
          </div>
          <p>The AI strategist for YouTube &amp; Instagram creators.</p>
          <p>&copy; {new Date().getFullYear()} creator-intel</p>
        </div>
      </footer>
    </div>
  );
}
