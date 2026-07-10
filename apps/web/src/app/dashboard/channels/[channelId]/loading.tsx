/** Channel intelligence skeleton — mirrors the real layout for zero jank. */
export default function ChannelLoading() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <div className="mb-9 flex items-center gap-4">
        <div className="skeleton h-10 w-10 rounded-xl" />
        <div className="space-y-2.5">
          <div className="skeleton h-7 w-56" />
          <div className="skeleton h-3.5 w-72" />
        </div>
      </div>
      <div className="mb-5 grid gap-5 lg:grid-cols-3">
        <div className="skeleton h-64 rounded-2xl lg:col-span-2" />
        <div className="skeleton h-64 rounded-2xl" />
      </div>
      <div className="grid gap-5 md:grid-cols-2">
        <div className="skeleton h-48 rounded-2xl" />
        <div className="skeleton h-48 rounded-2xl" />
      </div>
    </div>
  );
}
