import Link from "next/link";
import { SignedIn, SignedOut } from "@clerk/nextjs";
import {
  ArrowRight,
  Brain,
  Check,
  Filter,
  Layers,
  LineChart,
  MessageSquareText,
  Radar,
  Sparkles,
  TrendingUp,
  Youtube,
  Zap,
} from "lucide-react";
import { Aurora } from "@/components/Aurora";
import { Logo } from "@/components/Logo";

/* ----------------------------------------------------------------------------
   Content
---------------------------------------------------------------------------- */

const capabilities = [
  {
    icon: TrendingUp,
    title: "Why it performed",
    body: "Not another views chart. A reasoned explanation of why each video popped or flopped — hook, topic, timing, audience fit.",
  },
  {
    icon: Radar,
    title: "Audience intelligence",
    body: "Fifty thousand comments become a ranked map of requests, complaints, and moods. The signal, never the noise.",
  },
  {
    icon: Sparkles,
    title: "Next-move engine",
    body: "Prioritized, concrete ideas for your next uploads — derived from your data, not recycled creator advice.",
  },
  {
    icon: Brain,
    title: "Compounding memory",
    body: "The AI remembers every report, shift, and decision. Month three is measurably smarter than month one.",
  },
  {
    icon: Zap,
    title: "Cost-bounded AI",
    body: "A filter → dedupe → cluster → reason pipeline keeps deep analysis fast and affordable at any comment volume.",
  },
  {
    icon: Layers,
    title: "Agency-grade workspaces",
    body: "Every creator isolated in their own workspace. Run one channel or twenty-five from a single command center.",
  },
];

const steps = [
  { icon: Youtube, title: "Connect", body: "Link YouTube in one click. Videos, stats, and comments import automatically." },
  { icon: Filter, title: "Distill", body: "The pipeline filters spam, collapses duplicates, and clusters your audience into themes." },
  { icon: LineChart, title: "Reason", body: "Tiered AI reads the distilled signal and writes your strategy — scored, sourced, explained." },
  { icon: MessageSquareText, title: "Converse", body: "Ask anything. Answers stream from your real numbers, with full channel memory." },
];

const plans = [
  {
    name: "Free",
    price: "$0",
    tagline: "See your channel clearly.",
    features: ["1 connected channel", "Channel health scores", "Audience theme analysis", "Weekly AI reports"],
    cta: "Start free",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "$29",
    tagline: "Your full-time AI strategist.",
    features: ["3 connected channels", "AI strategist chat", "Monthly flagship strategy report", "Compounding channel memory"],
    cta: "Start with Pro",
    highlighted: true,
  },
  {
    name: "Agency",
    price: "$99",
    tagline: "Every client, one command center.",
    features: ["25 connected channels", "Team seats", "All Pro intelligence per channel", "Isolated client workspaces"],
    cta: "Scale with Agency",
    highlighted: false,
  },
];

const faqs = [
  {
    q: "How is this different from YouTube Studio?",
    a: "Studio tells you what happened — views, CTR, retention. Creator Intel explains why it happened and what to do next, then remembers the answer so future advice builds on your history.",
  },
  {
    q: "Do I need to upload anything?",
    a: "No. Connect your channel once and imports run automatically — videos, stats, and comments. No CSVs, no spreadsheets, no manual work.",
  },
  {
    q: "Is my channel data safe?",
    a: "Yes. OAuth tokens are encrypted at rest, access is read-only, and every workspace is isolated at the database level. You can disconnect at any time.",
  },
  {
    q: "How does the AI stay affordable on huge channels?",
    a: "Comments are filtered, deduplicated, and clustered before the AI ever reads them — so reasoning cost is bounded by the number of themes in your audience, not the number of comments.",
  },
];

/* ----------------------------------------------------------------------------
   Decorative product preview (illustrative sample data)
---------------------------------------------------------------------------- */

function ProductPreview() {
  return (
    <div aria-hidden className="glass relative mx-auto mt-16 w-full max-w-4xl overflow-hidden p-0 shadow-glow-sm">
      {/* window chrome */}
      <div className="flex items-center gap-1.5 border-b hairline px-4 py-3">
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
        <span className="ml-3 rounded-md bg-white/[0.05] px-2.5 py-0.5 text-[11px] text-slate-500">
          creator-intel · command center
        </span>
      </div>
      <div className="grid gap-4 p-5 sm:grid-cols-3">
        {/* gauge */}
        <div className="glass flex flex-col items-center justify-center gap-2 p-5">
          <svg viewBox="0 0 100 100" className="h-24 w-24 -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" strokeWidth="9" className="stroke-white/10" />
            <circle
              cx="50" cy="50" r="42" fill="none" strokeWidth="9" strokeLinecap="round"
              stroke="url(#pg)" strokeDasharray="264" strokeDashoffset="66"
            />
            <defs>
              <linearGradient id="pg" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#5EA2FF" />
                <stop offset="100%" stopColor="#A78BFA" />
              </linearGradient>
            </defs>
          </svg>
          <p className="-mt-16 font-display text-2xl font-bold text-white">75</p>
          <p className="mt-9 text-[11px] uppercase tracking-widest text-slate-500">Health score</p>
        </div>
        {/* audience mood */}
        <div className="glass flex flex-col gap-3 p-5">
          <p className="text-[11px] uppercase tracking-widest text-slate-500">Audience is asking for</p>
          {["Longer deep-dives", "Behind the scenes", "Beginner series"].map((t, i) => (
            <div key={t} className="flex items-center justify-between gap-2">
              <span className="text-[13px] text-slate-300">{t}</span>
              <span className="h-1.5 rounded-full bg-gradient-to-r from-brand-500 to-aiviolet" style={{ width: `${56 - i * 14}px` }} />
            </div>
          ))}
        </div>
        {/* AI insight */}
        <div className="glass flex flex-col gap-2.5 p-5">
          <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-widest text-slate-500">
            <Sparkles size={12} className="text-brand-400" /> AI insight
          </p>
          <p className="text-[13px] leading-relaxed text-slate-300">
            Your tutorial uploads outperform vlogs 3.2× on retention. Double down on the
            &ldquo;explained in 10 minutes&rdquo; format this month.
          </p>
          <span className="mt-auto inline-flex w-fit items-center gap-1 rounded-full border border-brand-400/30 bg-brand-500/15 px-2 py-0.5 text-[11px] text-brand-300">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-brand-400" /> live analysis
          </span>
        </div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------------
   Page
---------------------------------------------------------------------------- */

export default function Home() {
  return (
    <div className="min-h-screen overflow-x-clip">
      <Aurora />

      {/* Nav */}
      <header className="sticky top-0 z-50 border-b hairline bg-ink-950/60 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <nav className="hidden items-center gap-8 text-sm text-slate-400 md:flex">
            <a href="#product" className="transition hover:text-white">Product</a>
            <a href="#pipeline" className="transition hover:text-white">How it works</a>
            <a href="#pricing" className="transition hover:text-white">Pricing</a>
            <a href="#faq" className="transition hover:text-white">FAQ</a>
          </nav>
          <div className="flex items-center gap-2.5">
            <SignedOut>
              <Link href="/sign-in" className="rounded-lg px-3.5 py-2 text-sm text-slate-300 transition hover:bg-white/[0.06] hover:text-white">
                Sign in
              </Link>
              <Link href="/sign-up" className="btn-primary !px-4 !py-2">
                Get started
              </Link>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn-primary !px-4 !py-2">
                Open command center
              </Link>
            </SignedIn>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative mx-auto max-w-6xl px-6 pb-24 pt-20 text-center sm:pt-28">
        <div className="stagger mx-auto max-w-3xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-400/25 bg-brand-500/10 px-4 py-1.5 text-[13px] font-medium text-brand-300">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-brand-400" />
            The AI operating system for creators
          </span>
          <h1 className="mt-8 font-display text-5xl font-bold leading-[1.05] tracking-tight text-white sm:text-7xl">
            Know your channel
            <br />
            <span className="text-gradient">better than you do.</span>
          </h1>
          <p className="mx-auto mt-7 max-w-xl text-lg leading-relaxed text-slate-400">
            Creator Intel reads every video, every comment, every trend — then tells you why
            it happened, what your audience wants, and exactly what to make next.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <SignedOut>
              <Link href="/sign-up" className="btn-primary !px-7 !py-3 !text-base">
                Start free <ArrowRight size={17} />
              </Link>
              <Link href="/sign-in" className="btn-ghost !px-7 !py-3 !text-base">
                Sign in
              </Link>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn-primary !px-7 !py-3 !text-base">
                Open your command center <ArrowRight size={17} />
              </Link>
            </SignedIn>
          </div>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-x-7 gap-y-2 text-[13px] text-slate-500">
            {["One-click YouTube connect", "No manual uploads", "Free to start"].map((t) => (
              <span key={t} className="inline-flex items-center gap-1.5">
                <Check size={14} className="text-brand-400" /> {t}
              </span>
            ))}
          </div>
        </div>
        <ProductPreview />
      </section>

      {/* Capabilities */}
      <section id="product" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-[13px] font-medium uppercase tracking-[0.2em] text-brand-400">Intelligence, not analytics</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
            Dashboards show <span className="text-slate-500">what</span>.
            <br />We explain <span className="text-gradient">why</span>.
          </h2>
        </div>
        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {capabilities.map(({ icon: Icon, title, body }) => (
            <div key={title} className="glass glass-hover group p-7">
              <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-brand-400/20 bg-brand-500/10 text-brand-300 transition-colors group-hover:border-brand-400/40 group-hover:text-brand-200">
                <Icon size={20} strokeWidth={1.8} />
              </span>
              <h3 className="mt-5 font-display text-lg font-semibold text-white">{title}</h3>
              <p className="mt-2.5 text-[15px] leading-relaxed text-slate-400">{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pipeline */}
      <section id="pipeline" className="border-y hairline bg-ink-900/60">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-[13px] font-medium uppercase tracking-[0.2em] text-brand-400">How it works</p>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
              From raw channel to living strategy
            </h2>
            <p className="mt-5 text-slate-400">
              Four stages, fully automatic. You connect once — the system does the rest, forever.
            </p>
          </div>
          <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map(({ icon: Icon, title, body }, i) => (
              <div key={title} className="glass relative p-7">
                <span className="absolute right-5 top-5 font-display text-5xl font-bold text-white/[0.06]">
                  {i + 1}
                </span>
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-aiviolet text-white shadow-glow-sm">
                  <Icon size={20} strokeWidth={1.8} />
                </span>
                <h3 className="mt-5 font-display text-base font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-400">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="mx-auto max-w-6xl px-6 py-24">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-[13px] font-medium uppercase tracking-[0.2em] text-brand-400">Pricing</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
            Costs less than one sponsored post
          </h2>
          <p className="mt-5 text-slate-400">Start free. Upgrade when the insights pay for themselves.</p>
        </div>
        <div className="mt-16 grid gap-5 lg:grid-cols-3">
          {plans.map((p) => (
            <div
              key={p.name}
              className={`glass relative flex flex-col p-8 ${
                p.highlighted ? "border-brand-500/50 shadow-glow" : "glass-hover"
              }`}
            >
              {p.highlighted && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gradient-to-r from-brand-500 to-aiviolet px-3.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-white shadow-glow-sm">
                  Most popular
                </span>
              )}
              <h3 className="font-display text-lg font-semibold text-white">{p.name}</h3>
              <p className="mt-1 text-sm text-slate-500">{p.tagline}</p>
              <p className="mt-6 font-display text-5xl font-bold text-white">
                {p.price}
                <span className="text-base font-normal text-slate-500">/mo</span>
              </p>
              <ul className="mt-8 flex-1 space-y-3.5">
                {p.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-[15px] text-slate-300">
                    <Check size={16} className="mt-0.5 shrink-0 text-brand-400" /> {f}
                  </li>
                ))}
              </ul>
              <Link
                href="/sign-up"
                className={`${p.highlighted ? "btn-primary" : "btn-ghost"} mt-9 w-full`}
              >
                {p.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="border-t hairline bg-ink-900/60">
        <div className="mx-auto max-w-3xl px-6 py-24">
          <h2 className="text-center font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Questions, answered
          </h2>
          <div className="mt-12 space-y-4">
            {faqs.map(({ q, a }) => (
              <details key={q} className="glass group p-6 open:border-brand-500/30">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium text-white [&::-webkit-details-marker]:hidden">
                  {q}
                  <span className="text-slate-500 transition-transform duration-300 group-open:rotate-45">+</span>
                </summary>
                <p className="mt-4 text-[15px] leading-relaxed text-slate-400">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="glass relative overflow-hidden p-12 text-center sm:p-20">
          <div aria-hidden className="absolute left-1/2 top-0 h-64 w-[40rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-600/25 blur-[100px]" />
          <h2 className="relative font-display text-3xl font-bold tracking-tight text-white sm:text-5xl">
            Your channel has been trying
            <br />to tell you something.
          </h2>
          <p className="relative mx-auto mt-5 max-w-md text-slate-400">
            Connect it, and hear what fifty thousand comments have been saying all along.
          </p>
          <div className="relative mt-9 flex justify-center">
            <SignedOut>
              <Link href="/sign-up" className="btn-primary !px-8 !py-3.5 !text-base">
                Start free <ArrowRight size={17} />
              </Link>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn-primary !px-8 !py-3.5 !text-base">
                Open command center <ArrowRight size={17} />
              </Link>
            </SignedIn>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t hairline">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-5 px-6 py-10 text-sm text-slate-500 sm:flex-row">
          <Logo compact />
          <p>The AI operating system for YouTube &amp; Instagram creators.</p>
          <p>&copy; {new Date().getFullYear()} Creator Intel</p>
        </div>
      </footer>
    </div>
  );
}
