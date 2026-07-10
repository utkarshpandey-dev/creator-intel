import { SignIn } from "@clerk/nextjs";
import { Aurora } from "@/components/Aurora";
import { Logo } from "@/components/Logo";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 py-12">
      <Aurora />
      <Logo />
      <SignIn />
      <p className="max-w-xs text-center text-[13px] leading-relaxed text-slate-500">
        Your AI command center is waiting on the other side.
      </p>
    </main>
  );
}
