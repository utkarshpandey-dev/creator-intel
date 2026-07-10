import type { Video } from "@/lib/types";

function engagementRate(v: Video): number {
  const views = v.view_count ?? 0;
  if (views <= 0) return 0;
  return ((v.like_count ?? 0) + (v.comment_count ?? 0)) / views;
}

/** Video-by-video analysis, ranked by engagement, with inline performance bars. */
export function VideoTable({ videos }: { videos: Video[] }) {
  if (!videos || videos.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 px-5 py-8 text-center text-sm text-slate-500">
        No videos imported yet — they appear here automatically once your channel finishes
        syncing.
      </div>
    );
  }
  const ranked = [...videos].sort((a, b) => engagementRate(b) - engagementRate(a));
  const maxEng = Math.max(...ranked.map(engagementRate), 0.0001);

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[600px] text-sm">
        <thead>
          <tr className="border-b hairline text-left text-[11px] uppercase tracking-[0.14em] text-slate-500">
            <th className="py-2.5 pr-4 font-medium">Video</th>
            <th className="py-2.5 pr-4 text-right font-medium">Views</th>
            <th className="py-2.5 pr-4 text-right font-medium">Likes</th>
            <th className="py-2.5 pr-4 text-right font-medium">Comments</th>
            <th className="py-2.5 text-right font-medium">Engagement</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((v, i) => {
            const eng = engagementRate(v);
            return (
              <tr
                key={v.id}
                className="group border-b border-white/[0.04] transition-colors last:border-0 hover:bg-white/[0.03]"
              >
                <td className="max-w-[300px] py-3 pr-4">
                  <div className="flex items-center gap-3">
                    <span className="w-5 shrink-0 text-right font-display text-xs text-slate-600">
                      {i + 1}
                    </span>
                    <span className="truncate font-medium text-slate-200">
                      {v.title ?? "Untitled"}
                    </span>
                  </div>
                </td>
                <td className="py-3 pr-4 text-right tabular-nums text-slate-400">
                  {(v.view_count ?? 0).toLocaleString()}
                </td>
                <td className="py-3 pr-4 text-right tabular-nums text-slate-400">
                  {(v.like_count ?? 0).toLocaleString()}
                </td>
                <td className="py-3 pr-4 text-right tabular-nums text-slate-400">
                  {(v.comment_count ?? 0).toLocaleString()}
                </td>
                <td className="py-3 text-right">
                  <div className="inline-flex items-center justify-end gap-2.5">
                    <span className="h-1 w-14 overflow-hidden rounded-full bg-white/[0.07]">
                      <span
                        className="block h-full rounded-full bg-gradient-to-r from-brand-500 to-aiviolet"
                        style={{ width: `${Math.max(5, (eng / maxEng) * 100)}%` }}
                      />
                    </span>
                    <span className="w-12 font-display font-semibold tabular-nums text-white">
                      {(eng * 100).toFixed(1)}%
                    </span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
