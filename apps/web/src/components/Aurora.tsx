/**
 * Cinematic background: drifting light fields + faint grid, pure CSS.
 * Decorative only (aria-hidden); sits behind content via -z-10.
 */
export function Aurora({ intensity = "high" }: { intensity?: "high" | "low" }) {
  const opacity = intensity === "high" ? "opacity-100" : "opacity-50";
  return (
    <div aria-hidden className={`pointer-events-none fixed inset-0 -z-10 overflow-hidden ${opacity}`}>
      {/* base wash */}
      <div className="absolute inset-0 bg-ink-950" />
      {/* faint engineering grid */}
      <div
        className="absolute inset-0 bg-grid-faint [background-size:56px_56px]"
        style={{ maskImage: "radial-gradient(ellipse 90% 60% at 50% 0%, black 20%, transparent 75%)" }}
      />
      {/* drifting light fields */}
      <div className="absolute left-1/2 top-[-20%] h-[42rem] w-[70rem] -translate-x-1/2 animate-aurora rounded-full bg-brand-600/20 blur-[140px]" />
      <div className="absolute right-[-15%] top-[25%] h-[30rem] w-[36rem] animate-aurora-slow rounded-full bg-aiviolet/10 blur-[120px]" />
      <div className="absolute bottom-[-25%] left-[-10%] h-[32rem] w-[44rem] animate-aurora-slow rounded-full bg-electric/10 blur-[130px]" />
    </div>
  );
}
