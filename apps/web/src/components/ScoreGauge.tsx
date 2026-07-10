import type { CSSProperties } from "react";

/**
 * Radial score gauge (0–100). Pure SVG, server-rendered, with a CSS-driven
 * sweep animation on load. Gradient stroke shifts hue with the score band.
 */
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
  const gid = `gauge-${label.replace(/\W/g, "")}`;

  // Score band → gradient endpoints (rose → amber → brand/violet)
  const [from, to] =
    clamped >= 70 ? ["#5EA2FF", "#A78BFA"] : clamped >= 45 ? ["#f59e0b", "#fbbf24"] : ["#f43f5e", "#fb7185"];

  return (
    <div className="flex flex-col items-center gap-2.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            strokeWidth={stroke}
            className="stroke-white/[0.07]"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            strokeWidth={stroke}
            stroke={`url(#${gid})`}
            strokeDasharray={c}
            strokeLinecap="round"
            className="animate-gauge-fill"
            style={{ "--gauge-circ": c, "--gauge-offset": offset, filter: `drop-shadow(0 0 6px ${from}66)` } as CSSProperties}
          />
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={from} />
              <stop offset="100%" stopColor={to} />
            </linearGradient>
          </defs>
        </svg>
        <span className="absolute inset-0 flex items-center justify-center font-display text-3xl font-bold text-white">
          {Math.round(clamped)}
        </span>
      </div>
      <span className="text-[13px] font-medium text-slate-400">{label}</span>
    </div>
  );
}

/** Compact score row with an animated horizontal bar. */
export function ScoreBar({ value, label }: { value: number; label: string }) {
  const clamped = Math.max(0, Math.min(100, value));
  const gradient =
    clamped >= 70
      ? "from-electric to-aiviolet"
      : clamped >= 45
        ? "from-amber-500 to-amber-300"
        : "from-rose-500 to-rose-400";
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="font-display font-semibold text-white">{Math.round(clamped)}</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.07]">
        <div
          className={`h-full animate-bar-fill rounded-full bg-gradient-to-r ${gradient}`}
          style={{ "--bar-w": `${clamped}%` } as CSSProperties}
        />
      </div>
    </div>
  );
}
