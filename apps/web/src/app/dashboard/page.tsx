import { auth, currentUser } from "@clerk/nextjs/server";
import { OrganizationSwitcher, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api";

type Channel = {
  id: string;
  title: string | null;
  handle: string | null;
  thumbnail_url: string | null;
  subscriber_count: number | null;
  video_count: number | null;
  last_synced_at: string | null;
};

async function loadChannels(): Promise<Channel[]> {
  try {
    const res = await apiFetch("/youtube/channels");
    if (!res.ok) return [];
    return (await res.json()) as Channel[];
  } catch {
    // Backend may be down in local dev; the shell still renders.
    return [];
  }
}

// Protected shell. Real dashboard sections arrive in the Dashboard milestone.
// Here we prove: session is enforced, org context is resolved, and multi-tenant
// identity (user + org) is available server-side to scope every API call.
export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ connected?: string; error?: string }>;
}) {
  const { userId, orgId, orgRole } = await auth();

  // middleware already guarantees a session; this is defense-in-depth.
  if (!userId) redirect("/sign-in");

  const user = await currentUser();
  const { connected, error } = await searchParams;
  const channels = await loadChannels();

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard/billing"
            className="text-sm font-medium text-slate-600 hover:text-brand-600 dark:text-slate-300"
          >
            Plans &amp; billing
          </Link>
          {/* Lets agencies switch between the creators (orgs) they manage. */}
          <OrganizationSwitcher hidePersonal={false} />
          <UserButton />
        </div>
      </header>

      <section className="rounded-xl border border-slate-200 p-6 dark:border-slate-800">
        <p className="text-sm text-slate-500">Signed in as</p>
        <p className="text-lg font-medium">
          {user?.firstName ?? user?.emailAddresses[0]?.emailAddress ?? "Creator"}
        </p>
        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-slate-500">User ID</dt>
            <dd className="font-mono text-xs">{userId}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Active organization</dt>
            <dd className="font-mono text-xs">{orgId ?? "— (personal workspace)"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Role</dt>
            <dd>{orgRole ?? "owner"}</dd>
          </div>
        </dl>
      </section>

      {connected === "1" && (
        <p className="mt-6 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
          Channel connected. We&apos;re importing your videos and comments in the
          background — this can take a few minutes.
        </p>
      )}
      {connected === "0" && (
        <p className="mt-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          Connection failed{error ? `: ${error}` : ""}. Please try again.
        </p>
      )}

      <section className="mt-8">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Connected channels</h2>
          <Link
            href="/connect/youtube"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            + Connect YouTube
          </Link>
        </div>

        {channels.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700">
            No channels connected yet. Connect a YouTube channel to start your analysis.
          </div>
        ) : (
          <ul className="space-y-3">
            {channels.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/dashboard/channels/${c.id}`}
                  className="flex items-center justify-between rounded-xl border border-slate-200 p-4 transition hover:border-brand-500 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-900"
                >
                  <div>
                    <p className="font-medium">{c.title ?? "Untitled channel"}</p>
                    <p className="text-sm text-slate-500">
                      {c.handle ? `${c.handle} · ` : ""}
                      {c.subscriber_count?.toLocaleString() ?? "—"} subscribers ·{" "}
                      {c.video_count?.toLocaleString() ?? "—"} videos
                    </p>
                  </div>
                  <span className="text-xs text-slate-400">
                    {c.last_synced_at
                      ? `Synced ${new Date(c.last_synced_at).toLocaleDateString()}`
                      : "Import pending…"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
