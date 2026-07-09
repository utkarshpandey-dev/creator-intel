import type { Video } from "@/lib/types";

function engagementRate(v: Video): number {
  const views = v.view_count ?? 0;
  if (views <= 0) return 0;
  return ((v.like_count ?? 0) + (v.comment_count ?? 0)) / views;
}

/** Video-by-video analysis table, sorted by engagement rate. */
export function VideoTable({ videos }: { videos: Video[] }) {
  if (!videos || videos.length === 0) {
    return <p className="text-sm text-slate-400">No videos imported yet.</p>;
  }
  const ranked = [...videos].sort((a, b) => engagementRate(b) - engagementRate(a));

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400 dark:border-slate-800">
            <th className="py-2 pr-4 font-medium">Video</th>
            <th className="py-2 pr-4 font-medium text-right">Views</th>
            <th className="py-2 pr-4 font-medium text-right">Likes</th>
            <th className="py-2 pr-4 font-medium text-right">Comments</th>
            <th className="py-2 font-medium text-right">Engagement</th>
          </tr>
        </thead>
        <tbody>
          {ranked.map((v) => (
            <tr
              key={v.id}
              className="border-b border-slate-100 last:border-0 dark:border-slate-800/60"
            >
              <td className="max-w-[280px] truncate py-2.5 pr-4 font-medium">
                {v.title ?? "Untitled"}
              </td>
              <td className="py-2.5 pr-4 text-right tabular-nums text-slate-500">
                {(v.view_count ?? 0).toLocaleString()}
              </td>
              <td className="py-2.5 pr-4 text-right tabular-nums text-slate-500">
                {(v.like_count ?? 0).toLocaleString()}
              </td>
              <td className="py-2.5 pr-4 text-right tabular-nums text-slate-500">
                {(v.comment_count ?? 0).toLocaleString()}
              </td>
              <td className="py-2.5 text-right font-semibold tabular-nums">
                {(engagementRate(v) * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
