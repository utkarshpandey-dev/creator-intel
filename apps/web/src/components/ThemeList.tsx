import { Badge } from "@/components/ui/badge";
import type { ThemeRef, TopicRef } from "@/lib/types";

type Item = ThemeRef | TopicRef;

/** Renders a ranked list of audience themes (requests, complaints, best/worst topics). */
export function ThemeList({
  items,
  emptyText,
  tone = "neutral",
}: {
  items: Item[];
  emptyText: string;
  tone?: "neutral" | "positive" | "negative" | "brand";
}) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-slate-400">{emptyText}</p>;
  }
  return (
    <ul className="space-y-2.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start justify-between gap-3">
          <span className="text-sm text-slate-700 dark:text-slate-300">
            {item.label ?? "Untitled theme"}
          </span>
          {item.size != null && (
            <Badge tone={tone} className="shrink-0">
              {item.size.toLocaleString()}
            </Badge>
          )}
        </li>
      ))}
    </ul>
  );
}
