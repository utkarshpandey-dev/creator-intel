import * as React from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "positive" | "negative" | "brand";

const tones: Record<Tone, string> = {
  neutral: "border-white/10 bg-white/[0.05] text-slate-300",
  positive: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
  negative: "border-rose-400/25 bg-rose-400/10 text-rose-300",
  brand: "border-brand-400/30 bg-brand-500/15 text-brand-300",
};

export function Badge({
  tone = "neutral",
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
