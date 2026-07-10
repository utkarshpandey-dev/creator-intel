import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import { Check, Sparkles } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { AppShell } from "@/components/AppShell";

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

const planTaglines: Record<string, string> = {
  free: "See your channel clearly.",
  pro: "Your full-time AI strategist.",
  agency: "Every client, one command center.",
};

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
    <AppShell breadcrumb={<span className="text-slate-300">Billing</span>}>
      <div className="stagger">
        <header className="mb-10 max-w-xl">
          <p className="text-[13px] font-medium uppercase tracking-[0.2em] text-brand-400">
            Plans &amp; billing
          </p>
          <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Intelligence that pays for itself
          </h1>
          <p className="mt-3 text-slate-400">
            Pick the plan that matches how many channels you run and how deep you want the AI
            to go.
          </p>
        </header>

        {params.reason === "channel_limit" && (
          <div className="mb-7 rounded-xl border border-amber-400/25 bg-amber-400/10 px-5 py-4 text-sm text-amber-300">
            You&apos;ve reached your plan&apos;s channel limit. Upgrade to connect more
            channels.
          </div>
        )}
        {params.checkout === "success" && (
          <div className="mb-7 rounded-xl border border-emerald-400/25 bg-emerald-400/10 px-5 py-4 text-sm text-emerald-300">
            Subscription updated — your new plan is active.
          </div>
        )}
        {params.checkout === "error" && (
          <div className="mb-7 rounded-xl border border-rose-400/25 bg-rose-400/10 px-5 py-4 text-sm text-rose-300">
            Something went wrong starting checkout. Please try again.
          </div>
        )}

        {subscription && (
          <section className="glass mb-10 flex flex-wrap items-center justify-between gap-5 p-6">
            <div>
              <p className="text-[13px] uppercase tracking-[0.12em] text-slate-500">Current plan</p>
              <p className="mt-1 font-display text-xl font-semibold capitalize text-white">
                {subscription.limits.label}{" "}
                <span className="text-sm font-normal text-slate-500">
                  ({subscription.active ? subscription.status : "inactive"})
                </span>
              </p>
              {subscription.current_period_end && (
                <p className="mt-0.5 text-xs text-slate-500">
                  Renews {new Date(subscription.current_period_end).toLocaleDateString()}
                </p>
              )}
            </div>
            {subscription.plan !== "free" && subscription.active && (
              <form action={manage}>
                <button className="btn-ghost">Manage subscription</button>
              </form>
            )}
          </section>
        )}

        <section className="grid gap-5 md:grid-cols-3">
          {plans.map((p) => {
            const isCurrent = p.plan === currentPlan;
            const isFree = p.plan === "free";
            const highlighted = p.plan === "pro";
            return (
              <div
                key={p.plan}
                className={`glass relative flex flex-col p-8 ${
                  highlighted ? "border-brand-500/50 shadow-glow" : "glass-hover"
                }`}
              >
                {highlighted && (
                  <span className="absolute -top-3 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-gradient-to-r from-brand-500 to-aiviolet px-3.5 py-1 text-[11px] font-semibold uppercase tracking-wider text-white shadow-glow-sm">
                    <Sparkles size={11} /> Most popular
                  </span>
                )}
                <h2 className="font-display text-lg font-semibold text-white">{p.label}</h2>
                <p className="mt-1 text-sm text-slate-500">
                  {planTaglines[p.plan] ?? ""}
                </p>
                <p className="mt-6 font-display text-5xl font-bold text-white">
                  ${p.price_monthly_usd}
                  <span className="text-base font-normal text-slate-500">/mo</span>
                </p>

                <ul className="mt-8 flex-1 space-y-3.5 text-[15px]">
                  <li className="flex items-start gap-2.5 text-slate-300">
                    <Check size={16} className="mt-0.5 shrink-0 text-brand-400" />
                    {p.max_channels} channel{p.max_channels > 1 ? "s" : ""}
                  </li>
                  <li className="flex items-start gap-2.5 text-slate-300">
                    <Check size={16} className="mt-0.5 shrink-0 text-brand-400" />
                    {p.seats} team seat{p.seats > 1 ? "s" : ""}
                  </li>
                  <li
                    className={`flex items-start gap-2.5 ${p.ai_chat ? "text-slate-300" : "text-slate-600 line-through"}`}
                  >
                    <Check
                      size={16}
                      className={`mt-0.5 shrink-0 ${p.ai_chat ? "text-brand-400" : "text-slate-700"}`}
                    />
                    AI strategist chat
                  </li>
                  <li
                    className={`flex items-start gap-2.5 ${p.monthly_report ? "text-slate-300" : "text-slate-600 line-through"}`}
                  >
                    <Check
                      size={16}
                      className={`mt-0.5 shrink-0 ${p.monthly_report ? "text-brand-400" : "text-slate-700"}`}
                    />
                    Monthly flagship strategy report
                  </li>
                </ul>

                {isCurrent ? (
                  <span className="mt-9 rounded-xl border border-white/10 bg-white/[0.05] py-2.5 text-center text-sm font-medium text-slate-400">
                    Current plan
                  </span>
                ) : isFree ? (
                  <span className="mt-9 py-2.5 text-center text-sm text-slate-600">
                    Included by default
                  </span>
                ) : (
                  <form action={subscribe} className="mt-9">
                    <input type="hidden" name="plan" value={p.plan} />
                    <button className={`${highlighted ? "btn-primary" : "btn-ghost"} w-full`}>
                      {currentPlan === "free" ? `Upgrade to ${p.label}` : `Switch to ${p.label}`}
                    </button>
                  </form>
                )}
              </div>
            );
          })}
        </section>
      </div>
    </AppShell>
  );
}
