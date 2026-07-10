import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { ArrowLeft, RefreshCw, Sparkles, Users, Video } from "lucide-react";
import { auth } from "@clerk/nextjs/server";

import { apiFetch } from "@/lib/api";
import { getChannel, getInsight, getReports, getVideos } from "@/lib/queries";
import { AppShell } from "@/components/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreGauge, ScoreBar } from "@/components/ScoreGauge";
import { ThemeList } from "@/components/ThemeList";
import { VideoTable } from "@/components/VideoTable";
import { ReportView } from "@/components/ReportView";
import { ChatPanel } from "@/components/ChatPanel";

const ZERO = { health: 0, engagement: 0, growth: 0, consistency: 0, sentiment: 0 };

export default async function ChannelDashboard({
  params,
}: {
  params: Promise<{ channelId: string }>;
}) {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const { channelId } = await params;
  const [channel, insight, reports, videos] = await Promise.all([
    getChannel(channelId),
    getInsight(channelId),
    getReports(channelId),
    getVideos(channelId),
  ]);

  if (!channel) notFound();

  const scores = insight?.payload.scores ?? ZERO;
  const p = insight?.payload;
  const weekly = reports.find((r) => r.kind === "weekly") ?? reports[0] ?? null;

  async function generateReport(formData: FormData) {
    "use server";
    const kind = String(formData.get("kind") ?? "weekly");
    await apiFetch(`/channels/${channelId}/reports?kind=${kind}`, { method: "POST" });
    revalidatePath(`/dashboard/channels/${channelId}`);
  }

  return (
    <AppShell
      breadcrumb={<span className="truncate text-slate-300">{channel.title ?? "Channel"}</span>}
    >
      <div className="stagger">
        {/* Channel masthead */}
        <div className="mb-9 flex flex-wrap items-center justify-between gap-5">
          <div className="flex items-center gap-4">
            <Link
              href="/dashboard"
              aria-label="Back to dashboard"
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-slate-400 transition hover:border-white/25 hover:text-white"
            >
              <ArrowLeft size={17} />
            </Link>
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
                {channel.title ?? "Channel"}
              </h1>
              <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-slate-500">
                {channel.handle && <span>{channel.handle}</span>}
                <span className="inline-flex items-center gap-1.5">
                  <Users size={12} /> {(channel.subscriber_count ?? 0).toLocaleString()} subscribers
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <Video size={12} /> {(channel.video_count ?? 0).toLocaleString()} videos
                </span>
              </p>
            </div>
          </div>
          <form action={generateReport}>
            <input type="hidden" name="kind" value="monthly" />
            <button className="btn-primary">
              <Sparkles size={15} /> Generate monthly strategy
            </button>
          </form>
        </div>

        {/* Analysis in progress */}
        {!insight && (
          <div className="mb-7 flex items-center gap-4 rounded-2xl border border-brand-400/25 bg-brand-500/[0.08] px-6 py-5">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-500/15 text-brand-300">
              <RefreshCw size={17} className="animate-spin" />
            </span>
            <div>
              <p className="text-sm font-medium text-brand-200">The AI is reading your channel</p>
              <p className="mt-0.5 text-[13px] text-slate-400">
                Videos and comments are being filtered, clustered, and analyzed. Scores and
                your first report appear here shortly after import finishes.
              </p>
            </div>
          </div>
        )}

        {/* Vital signs */}
        <section className="mb-5 grid gap-5 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Vital signs</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center justify-around gap-8 py-6">
              <ScoreGauge value={scores.health} label="Health" size={150} />
              <ScoreGauge value={scores.growth} label="Growth" />
              <ScoreGauge value={scores.engagement} label="Engagement" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Signals</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-4">
              <ScoreBar value={scores.sentiment} label="Audience sentiment" />
              <ScoreBar value={scores.consistency} label="Upload consistency" />
              <div className="flex flex-wrap gap-2 pt-1">
                <Badge tone="brand">{p?.video_count ?? 0} videos analyzed</Badge>
                <Badge tone="neutral">{p?.theme_count ?? 0} audience themes</Badge>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Audience intelligence */}
        <section className="mb-5 grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Audience requests</CardTitle>
            </CardHeader>
            <CardContent>
              <ThemeList
                items={p?.audience_requests ?? []}
                tone="brand"
                emptyText="No clear requests surfaced yet — they appear as comment themes cluster."
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Audience complaints</CardTitle>
            </CardHeader>
            <CardContent>
              <ThemeList
                items={p?.audience_complaints ?? []}
                tone="negative"
                emptyText="No recurring complaints — a genuinely good sign."
              />
            </CardContent>
          </Card>
        </section>

        <section className="mb-5 grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Winning topics</CardTitle>
            </CardHeader>
            <CardContent>
              <ThemeList
                items={p?.best_topics ?? []}
                tone="positive"
                emptyText="Not enough data yet — more videos sharpen this view."
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Underperforming topics</CardTitle>
            </CardHeader>
            <CardContent>
              <ThemeList
                items={p?.worst_topics ?? []}
                tone="negative"
                emptyText="No underperforming topics flagged."
              />
            </CardContent>
          </Card>
        </section>

        {/* AI strategy report */}
        <section className="mb-5">
          <Card>
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Sparkles size={13} className="text-brand-400" /> AI strategy report
              </CardTitle>
              <form action={generateReport}>
                <input type="hidden" name="kind" value="weekly" />
                <button className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-brand-300 transition hover:bg-brand-500/10 hover:text-brand-200">
                  <RefreshCw size={12} /> Regenerate weekly
                </button>
              </form>
            </CardHeader>
            <CardContent>
              <ReportView report={weekly} />
            </CardContent>
          </Card>
        </section>

        {/* Video performance */}
        <section className="mb-5">
          <Card>
            <CardHeader>
              <CardTitle>Video performance</CardTitle>
            </CardHeader>
            <CardContent>
              <VideoTable videos={videos} />
            </CardContent>
          </Card>
        </section>

        {/* Chat */}
        <section>
          <Card className="border-brand-500/20">
            <CardHeader>
              <CardTitle>Ask your channel</CardTitle>
            </CardHeader>
            <CardContent>
              <ChatPanel channelId={channelId} />
            </CardContent>
          </Card>
        </section>
      </div>
    </AppShell>
  );
}
