import Link from "next/link";
import { OrganizationSwitcher, UserButton } from "@clerk/nextjs";
import { CreditCard } from "lucide-react";
import { Logo } from "@/components/Logo";
import { Aurora } from "@/components/Aurora";

/**
 * Shared chrome for every authenticated screen: cinematic backdrop + sticky
 * glass header with workspace switching. Keeps the app feeling like one product.
 */
export function AppShell({
  children,
  breadcrumb,
}: {
  children: React.ReactNode;
  breadcrumb?: React.ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <Aurora intensity="low" />
      <header className="sticky top-0 z-50 border-b hairline bg-ink-950/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3.5">
          <div className="flex min-w-0 items-center gap-4">
            <Logo href="/dashboard" />
            {breadcrumb && (
              <div className="hidden min-w-0 items-center gap-2 text-sm text-slate-400 sm:flex">
                <span className="text-slate-600">/</span>
                {breadcrumb}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2.5">
            <Link
              href="/dashboard/billing"
              className="hidden items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-slate-400 transition hover:bg-white/[0.06] hover:text-white sm:flex"
            >
              <CreditCard size={15} /> Billing
            </Link>
            <OrganizationSwitcher hidePersonal={false} />
            <UserButton />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-10">{children}</main>
    </div>
  );
}
