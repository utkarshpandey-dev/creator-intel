import * as React from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "positive" | "negative" | "brand";

const tones: Record<Tone, string> = {
  neutral: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
  positive: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  negative: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300",
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-700/20 dark:text-brand-500",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
