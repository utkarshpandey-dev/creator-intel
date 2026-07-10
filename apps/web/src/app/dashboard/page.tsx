import Link from "next/link";
import { redirect } from "next/navigation";
import { auth, currentUser } from "@clerk/nextjs/server";
import {
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  Circle,
  Plus,
  RefreshCw,
  Sparkles,
  Users,
  Video,
  Youtube,
} from "lucide-react";
import { getChannels } from "@/lib/queries";
import type { Channel } from "@/lib/types";
import { AppShell } from "@/components/AppShell";
import { Badge } from "@/components/ui/badge";

/* ---------------------------------------------------------------------------- */

function StatTile({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Users;
  label: string;
  value: string;
}) {
  return (
    <div className="glass flex items-center gap-4 p-5">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-brand-400/20 bg-brand-500/10 text-brand-300">
        <Icon size={18} strokeWidth={1.8} />
      </span>
      <div className="min-w-0">
        <p className="truncate font-display text-2xl font-bold text-white">{value}</p>
        <p className="text-[13px] text-slate-500">{label}</p>
      </div>
    </div>
  );
}

function ChannelCard({ c }: { c: Channel }) {
  const synced = Boolean(c.last_synced_at);
  return (
    <Link href={`/dashboard/channels/${c.id}`} className="glass glass-hover group flex flex-col p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3.5">
          {c.thumbnail_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={c.thumbnail_url}
              alt=""
              className="h-12 w-12 rounded-full border border-white/10 object-cover"
            />
          ) : (
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-brand-500/30 to-aiviolet/30 text-brand-200">
              <Youtube size={20} />
            </span>
          )}
          <div className="min-w-0">
            <p className="truncate font-display text-base font-semibold text-white">
              {c.title ?? "Untitled channel"}
            </p>
            {c.handle && <p className="truncate text-[13px] text-slate-500">{c.handle}</p>}
          </div>
        </div>
        <ArrowUpRight size={17} className="shrink-0 text-slate-600 transition group-hover:text-brand-300" />
      </div>
      <div className="mt-5 flex items-center gap-5 text-[13px] text-slate-400">
        <span className="inline-flex items-center gap-1.5">
          <Users size={13} className="text-slate-600" />
          {c.subscriber_count?.toLocaleString() ?? "—"}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Video size={13} className="text-slate-600" />
          {c.video_count?.toLocaleString() ?? "—"}
        </span>
        <span className="ml-auto">
          {synced ? (
            <Badge tone="positive">analyzed</Badge>
          ) : (
            <Badge tone="brand">
              <RefreshCw size={11} className="mr-1 animate-spin" /> importing
            </Badge>
          )}
        </span>
      </div>
    </Link>
  );
}

/** First-run experience: educates instead of a blank screen. */
function Onboarding() {
  const items = [
    { done: true, label: "Create your workspace" },
    { done: false, label: "Connect your YouTube channel" },
    { done: false, label: "Let the AI analyze videos & comments" },
    { done: false, label: "Get your first strategy report" },
  ];
  return (
    <div className="glass relative overflow-hidden p-10 sm:p-14">
      <div aria-hidden className="absolute right-0 top-0 h-56 w-96 translate-x-1/4 -translate-y-1/3 rounded-full bg-brand-600/20 blur-[90px]" />
      <div className="relative grid items-center gap-10 lg:grid-cols-2">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-400/25 bg-brand-500/10 px-3.5 py-1 text-xs font-medium text-brand-300">
            <Sparkles size={13} /> Mission start
          </span>
          <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-white">
            Connect a channel and watch it come alive
          </h2>
          <p className="mt-3.5 leading-relaxed text-slate-400">
            One click starts the import. Within minutes the AI has read your videos and
            comments, scored your channel&apos;s health, and written your first strategy
            report.
          </p>
          <Link href="/connect/youtube" className="btn-primary mt-7 !px-6 !py-3">
            <Youtube size={17} /> Connect YouTube <ArrowRight size={16} />
          </Link>
        </div>
        <ul className="space-y-3.5">
          {items.map(({ done, label }) => (
            <li key={label} className="glass flex items-center gap-3.5 px-5 py-4 text-[15px]">
              {done ? (
                <CheckCircle2 size={19} className="shrink-0 text-brand-400" />
              ) : (
                <Circle size={19} className="shrink-0 text-slate-600" />
              )}
              <span className={done ? "text-slate-500 line-through" : "text-slate-200"}>{label}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------------- */

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ connected?: string; error?: string }>;
}) {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in"); // middleware backstop

  const user = await currentUser();
  const { connected, error } = await searchParams;
  const channels = await getChannels();

  const totalSubs = channels.reduce((n, c) => n + (c.subscriber_count ?? 0), 0);
  const totalVideos = channels.reduce((n, c) => n + (c.video_count ?? 0), 0);
  const firstName = user?.firstName ?? "Creator";

  return (
    <AppShell>
      <div className="stagger">
        {/* Greeting */}
        <header className="mb-9 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-[13px] font-medium uppercase tracking-[0.2em] text-brand-400">
              Command center
            </p>
            <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Welcome back, {firstName}
            </h1>
          </div>
          {channels.length > 0 && (
            <Link href="/connect/youtube" className="btn-primary">
              <Plus size={16} /> Connect channel
            </Link>
          )}
        </header>

        {/* Status toasts */}
        {connected === "1" && (
          <div className="mb-7 flex items-center gap-3 rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-5 py-4 text-sm text-emerald-300">
            <RefreshCw size={15} className="animate-spin" />
            Channel connected — importing videos and comments in the background. First
            insights land in a few minutes.
          </div>
        )}
        {connected === "0" && (
          <div className="mb-7 rounded-xl border border-rose-400/25 bg-rose-400/10 px-5 py-4 text-sm text-rose-300">
            Connection failed{error ? `: ${error}` : ""}. Please try again.
          </div>
        )}

        {channels.length === 0 ? (
          <Onboarding />
        ) : (
          <>
            {/* Fleet stats */}
            <section className="mb-9 grid gap-4 sm:grid-cols-3">
              <StatTile icon={Youtube} label="Connected channels" value={String(channels.length)} />
              <StatTile icon={Users} label="Total audience reach" value={totalSubs.toLocaleString()} />
              <StatTile icon={Video} label="Videos under analysis" value={totalVideos.toLocaleString()} />
            </section>

            {/* Channels */}
            <section>
              <h2 className="mb-4 text-[13px] font-medium uppercase tracking-[0.12em] text-slate-500">
                Your channels
              </h2>
              <div className="grid gap-4 sm:grid-cols-2">
                {channels.map((c) => (
                  <ChannelCard key={c.id} c={c} />
                ))}
              </div>
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
