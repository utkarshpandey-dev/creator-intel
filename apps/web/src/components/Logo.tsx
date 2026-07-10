import Link from "next/link";
import { cn } from "@/lib/utils";

/** Wordmark: gradient orbital mark + display-type name. */
export function Logo({ href = "/", compact = false }: { href?: string; compact?: boolean }) {
  return (
    <Link href={href} className="group flex items-center gap-2.5">
      <span className="relative flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-aiviolet shadow-glow-sm transition-shadow group-hover:shadow-glow">
        {/* orbital mark */}
        <svg viewBox="0 0 24 24" className="h-[18px] w-[18px] text-white" fill="none">
          <circle cx="12" cy="12" r="3.2" fill="currentColor" />
          <ellipse cx="12" cy="12" rx="9" ry="4.5" stroke="currentColor" strokeWidth="1.4" transform="rotate(-24 12 12)" />
        </svg>
      </span>
      {!compact && (
        <span className={cn("font-display text-[17px] font-semibold tracking-tight text-white")}>
          Creator<span className="text-gradient"> Intel</span>
        </span>
      )}
    </Link>
  );
}
