import { auth } from "@clerk/nextjs/server";
import Link from "next/link";
import { redirect } from "next/navigation";
import { apiFetch } from "@/lib/api";

// --- Types mirrored from the API's billing router ---
type PlanLimits = {
  plan: string;
  label: string;
  price_monthly_usd: number;
  max_channels: number;
  monthly_report: boolean;
  ai_chat: boolean;
  seats: number;
};

type SubscriptionState = {
  plan: string;
  status: string;
  active: boolean;
  current_period_end: string | null;
  limits: PlanLimits;
};

async function loadPlans(): Promise<PlanLimits[]> {
  try {
    const res = await apiFetch("/billing/plans");
    return res.ok ? ((await res.json()) as PlanLimits[]) : [];
  } catch {
    return [];
  }
}

async function loadSubscription(): Promise<SubscriptionState | null> {
  try {
    const res = await apiFetch("/billing/subscription");
    return res.ok ? ((await res.json()) as SubscriptionState) : null;
  } catch {
    return null;
  }
}

/**
 * Offline/stub completion. Real Stripe fires a webhook to activate the plan; in stub mode
 * (no Stripe key) there's no webhook, so when Checkout redirects back with ?stub=1 we
 * complete the loop server-side by forwarding a synthetic event to the backend's internal
 * sync — the same endpoint the real webhook route calls. Guarded by the internal secret.
 */
async function completeStubCheckout(orgId: string, plan: string) {
  const base = process.env.API_BASE_URL ?? "http://localhost:8000";
  try {
    await fetch(`${base}/billing/internal/stripe/sync`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-internal-secret": process.env.INTERNAL_API_SECRET ?? "",
      },
      body: JSON.stringify({
        type: "stub.checkout.completed",
        data: { organization_id: orgId, plan },
      }),
      cache: "no-store",
    });
  } catch {
    // Best-effort in dev; the user can retry from the pricing cards.
  }
}

export default async function BillingPage({
  searchParams,
}: {
  searchParams: Promise<{
    checkout?: string;
    stub?: string;
    plan?: string;
    org?: string;
    reason?: string;
  }>;
}) {
  const { userId } = await auth();
  if (!userId) redirect("/sign-in");

  const params = await searchParams;
  if (params.stub === "1" && params.org && params.plan) {
    await completeStubCheckout(params.org, params.plan);
    redirect("/dashboard/billing?checkout=success");
  }

  const [plans, subscription] = await Promise.all([loadPlans(), loadSubscription()]);
  const currentPlan = subscription?.active ? subscription.plan : "free";

  // --- Server actions: ask the backend for a redirect URL, then send the browser there ---
  async function subscribe(formData: FormData) {
    "use server";
    const plan = String(formData.get("plan"));
    const res = await apiFetch(`/billing/checkout?plan=${encodeURIComponent(plan)}`, {
      method: "POST",
    });
    if (!res.ok) redirect("/dashboard/billing?checkout=error");
    const { url } = (await res.json()) as { url: string };
    redirect(url);
  }

  async function manage() {
    "use server";
    const res = await apiFetch("/billing/portal", { method: "POST" });
    if (!res.ok) redirect("/dashboard/billing?checkout=error");
    const { url } = (await res.json()) as { url: string };
    redirect(url);
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Plans &amp; billing</h1>
          <p className="mt-1 text-sm text-slate-500">
            Choose the plan that matches how many channels you run and how deep you want the
            AI to go.
          </p>
        </div>
        <Link href="/dashboard" className="text-sm text-brand-600 hover:underline">
          ← Back to dashboard
        </Link>
      </header>

      {params.reason === "channel_limit" && (
        <p className="mb-6 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-300">
          You&apos;ve reached your plan&apos;s channel limit. Upgrade to connect more channels.
        </p>
      )}
      {params.checkout === "success" && (
        <p className="mb-6 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
          Subscription updated. Your new plan is active.
        </p>
      )}
      {params.checkout === "error" && (
        <p className="mb-6 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
          Something went wrong starting checkout. Please try again.
        </p>
      )}

      {subscription && (
        <section className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-xl border border-slate-200 p-5 dark:border-slate-800">
          <div>
            <p className="text-sm text-slate-500">Current plan</p>
            <p className="text-lg font-semibold capitalize">
              {subscription.limits.label}{" "}
              <span className="text-sm font-normal text-slate-500">
                ({subscription.active ? subscription.status : "inactive"})
              </span>
            </p>
            {subscription.current_period_end && (
              <p className="text-xs text-slate-400">
                Renews {new Date(subscription.current_period_end).toLocaleDateString()}
              </p>
            )}
          </div>
          {subscription.plan !== "free" && subscription.active && (
            <form action={manage}>
              <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium transition hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-900">
                Manage subscription
              </button>
            </form>
          )}
        </section>
      )}

      <section className="grid gap-6 md:grid-cols-3">
        {plans.map((p) => {
          const isCurrent = p.plan === currentPlan;
          const isFree = p.plan === "free";
          const highlighted = p.plan === "pro";
          return (
            <div
              key={p.plan}
              className={`flex flex-col rounded-2xl border p-6 ${
                highlighted
                  ? "border-brand-500 shadow-lg shadow-brand-500/10"
                  : "border-slate-200 dark:border-slate-800"
              }`}
            >
              <div className="mb-4">
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold">{p.label}</h2>
                  {highlighted && (
                    <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                      Popular
                    </span>
                  )}
                </div>
                <p className="mt-2 text-3xl font-bold">
                  ${p.price_monthly_usd}
                  <span className="text-sm font-normal text-slate-500">/mo</span>
                </p>
              </div>

              <ul className="mb-6 flex-1 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                <li>
                  {p.max_channels} channel{p.max_channels > 1 ? "s" : ""}
                </li>
                <li>{p.seats} team seat{p.seats > 1 ? "s" : ""}</li>
                <li className={p.ai_chat ? "" : "text-slate-400 line-through"}>
                  AI strategist chat
                </li>
                <li className={p.monthly_report ? "" : "text-slate-400 line-through"}>
                  Monthly flagship strategy report
                </li>
              </ul>

              {isCurrent ? (
                <span className="rounded-lg bg-slate-100 py-2 text-center text-sm font-medium text-slate-500 dark:bg-slate-800">
                  Current plan
                </span>
              ) : isFree ? (
                <span className="rounded-lg py-2 text-center text-sm text-slate-400">
                  Default
                </span>
              ) : (
                <form action={subscribe}>
                  <input type="hidden" name="plan" value={p.plan} />
                  <button
                    className={`w-full rounded-lg py-2 text-sm font-medium text-white transition ${
                      highlighted
                        ? "bg-brand-600 hover:bg-brand-700"
                        : "bg-slate-900 hover:bg-slate-700 dark:bg-slate-700 dark:hover:bg-slate-600"
                    }`}
                  >
                    {currentPlan === "free" ? "Subscribe" : "Switch to " + p.label}
                  </button>
                </form>
              )}
            </div>
          );
        })}
      </section>
    </main>
  );
}
