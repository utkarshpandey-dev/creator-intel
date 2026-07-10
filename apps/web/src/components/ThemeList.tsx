import { Badge } from "@/components/ui/badge";
import type { ThemeRef, TopicRef } from "@/lib/types";

type Item = ThemeRef | TopicRef;
type Tone = "neutral" | "positive" | "negative" | "brand";

const barTone: Record<Tone, string> = {
  neutral: "from-slate-500 to-slate-400",
  positive: "from-emerald-500 to-emerald-300",
  negative: "from-rose-500 to-rose-400",
  brand: "from-brand-500 to-aiviolet",
};

/**
 * Ranked audience themes with proportional weight bars — the size of each
 * theme is visible at a glance, not just a number.
 */
export function ThemeList({
  items,
  emptyText,
  tone = "neutral",
}: {
  items: Item[];
  emptyText: string;
  tone?: Tone;
}) {
  if (!items || items.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-white/10 px-5 py-6 text-center text-sm text-slate-500">
        {emptyText}
      </div>
    );
  }
  const max = Math.max(...items.map((i) => i.size ?? 0), 1);

  return (
    <ul className="space-y-3.5">
      {items.map((item, i) => {
        const width = Math.max(6, Math.round(((item.size ?? 0) / max) * 100));
        return (
          <li key={i} className="space-y-1.5">
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm text-slate-200">{item.label ?? "Untitled theme"}</span>
              {item.size != null && (
                <Badge tone={tone} className="shrink-0">
                  {item.size.toLocaleString()}
                </Badge>
              )}
            </div>
            <div className="h-1 w-full overflow-hidden rounded-full bg-white/[0.05]">
              <div
                className={`h-full rounded-full bg-gradient-to-r ${barTone[tone]} opacity-70`}
                style={{ width: `${width}%` }}
              />
            </div>
          </li>
        );
      })}
    </ul>
  );
}
