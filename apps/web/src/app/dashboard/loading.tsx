/** Instant skeleton while server data loads — no blank screens, ever. */
export default function DashboardLoading() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-9 space-y-3">
        <div className="skeleton h-3 w-36" />
        <div className="skeleton h-9 w-72" />
      </div>
      <div className="mb-9 grid gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="skeleton h-[84px] rounded-2xl" />
        ))}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {[0, 1].map((i) => (
          <div key={i} className="skeleton h-32 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}
