import { cn } from "@/lib/utils";

/** Radial score gauge (0–100), pure SVG so it renders server-side with no chart dep. */
export function ScoreGauge({
  value,
  label,
  size = 132,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const clamped = Math.max(0, Math.min(100, value));
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped / 100);

  const color =
    clamped >= 70 ? "#10b981" : clamped >= 45 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          className="stroke-slate-200 dark:stroke-slate-800"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          stroke={color}
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
        <text
          x="50%"
          y="50%"
          dominantBaseline="central"
          textAnchor="middle"
          className="rotate-90 fill-slate-900 text-2xl font-bold dark:fill-slate-100"
          style={{ transformOrigin: "center" }}
        >
          {Math.round(clamped)}
        </text>
      </svg>
      <span className="text-sm font-medium text-slate-600 dark:text-slate-400">{label}</span>
    </div>
  );
}

/** Compact score row with a horizontal bar. */
export function ScoreBar({ value, label }: { value: number; label: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  const color =
    clamped >= 70 ? "bg-emerald-500" : clamped >= 45 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-600 dark:text-slate-400">{label}</span>
        <span className="font-semibold">{Math.round(clamped)}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
