import Link from "next/link";
import { notFound } from "next/navigation";
import { revalidatePath } from "next/cache";
import { ArrowLeft, RefreshCw, Sparkles } from "lucide-react";
import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";

import { apiFetch } from "@/lib/api";
import { getChannel, getInsight, getReports, getVideos } from "@/lib/queries";
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
    <main className="mx-auto max-w-6xl px-6 py-8">
      {/* Header */}
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
          >
            <ArrowLeft size={16} />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{channel.title ?? "Channel"}</h1>
            <p className="text-sm text-slate-500">
              {channel.handle ? `${channel.handle} · ` : ""}
              {(channel.subscriber_count ?? 0).toLocaleString()} subscribers ·{" "}
              {(channel.video_count ?? 0).toLocaleString()} videos
            </p>
          </div>
        </div>
        <form action={generateReport}>
          <input type="hidden" name="kind" value="monthly" />
          <button className="flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700">
            <Sparkles size={15} /> Generate monthly strategy
          </button>
        </form>
      </div>

      {!insight && (
        <Card className="mb-8">
          <CardContent className="flex items-center gap-3 py-6 text-sm text-slate-500">
            <RefreshCw size={16} className="animate-spin" />
            Analysis is being generated. Scores and reports will appear here shortly after your
            channel finishes importing.
          </CardContent>
        </Card>
      )}

      {/* Scores */}
      <section className="mb-6 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Channel Health</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center justify-around gap-6">
            <ScoreGauge value={scores.health} label="Health Score" size={148} />
            <ScoreGauge value={scores.growth} label="Growth" />
            <ScoreGauge value={scores.engagement} label="Engagement" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Signals</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5 pt-4">
            <ScoreBar value={scores.sentiment} label="Audience Sentiment" />
            <ScoreBar value={scores.consistency} label="Upload Consistency" />
            <div className="flex gap-2 pt-1">
              <Badge tone="brand">{p?.video_count ?? 0} videos analyzed</Badge>
              <Badge tone="neutral">{p?.theme_count ?? 0} themes</Badge>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Audience */}
      <section className="mb-6 grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Audience Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeList items={p?.audience_requests ?? []} tone="brand" emptyText="No clear requests yet." />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Audience Complaints</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeList items={p?.audience_complaints ?? []} tone="negative" emptyText="No recurring complaints — nice." />
          </CardContent>
        </Card>
      </section>

      <section className="mb-6 grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Best Performing Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeList items={p?.best_topics ?? []} tone="positive" emptyText="Not enough data yet." />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Worst Performing Topics</CardTitle>
          </CardHeader>
          <CardContent>
            <ThemeList items={p?.worst_topics ?? []} tone="negative" emptyText="No underperforming topics flagged." />
          </CardContent>
        </Card>
      </section>

      {/* AI report */}
      <section className="mb-6">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>AI Strategy Report</CardTitle>
            <form action={generateReport}>
              <input type="hidden" name="kind" value="weekly" />
              <button className="flex items-center gap-1.5 text-xs font-medium text-brand-600 hover:text-brand-700">
                <RefreshCw size={13} /> Regenerate weekly
              </button>
            </form>
          </CardHeader>
          <CardContent>
            <ReportView report={weekly} />
          </CardContent>
        </Card>
      </section>

      {/* Video-by-video */}
      <section className="mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Video-by-Video Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <VideoTable videos={videos} />
          </CardContent>
        </Card>
      </section>

      {/* Chat */}
      <section>
        <Card>
          <CardHeader>
            <CardTitle>Ask your channel</CardTitle>
          </CardHeader>
          <CardContent>
            <ChatPanel channelId={channelId} />
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
