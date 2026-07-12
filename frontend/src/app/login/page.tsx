"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Boxes, Eye, EyeOff, Lock, Mail, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/shared/form-field";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useSession } from "@/lib/auth/use-session";
import { authenticate, DEMO_ACCOUNTS, ROLE_LABELS } from "@/lib/auth/session";

const schema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const router = useRouter();
  const { session, login } = useSession();
  const [showPassword, setShowPassword] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (session) router.replace("/dashboard");
  }, [session, router]);

  async function onSubmit(values: FormValues) {
    setAuthError(null);
    await new Promise((r) => setTimeout(r, 500));
    const result = authenticate(values.email, values.password);
    if (!result) {
      setAuthError("Invalid email or password. Try a demo account below.");
      return;
    }
    login(result);
    router.replace("/dashboard");
  }

  function quickFill(email: string, password: string) {
    setValue("email", email);
    setValue("password", password);
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-sidebar p-12 text-sidebar-foreground lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, hsl(231 62% 60% / 0.35), transparent 45%), radial-gradient(circle at 80% 60%, hsl(199 89% 52% / 0.25), transparent 40%)",
          }}
        />
        <div className="relative flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-sidebar-accent text-white">
            <Boxes className="size-6" />
          </div>
          <div>
            <p className="text-lg font-semibold text-white">AssetFlow</p>
            <p className="text-xs text-sidebar-foreground/70">Enterprise Asset & Resource Management</p>
          </div>
        </div>

        <div className="relative space-y-6">
          <h1 className="text-4xl font-semibold leading-tight text-white">
            Every asset,
            <br />
            under control.
          </h1>
          <p className="max-w-md text-sidebar-foreground/80">
            Track assets across their full lifecycle — allocation, booking, maintenance and audit —
            with a single, unified operations platform.
          </p>
          <ul className="space-y-3 text-sm text-sidebar-foreground/80">
            {[
              "Real-time asset distribution & KPIs",
              "Booking approvals with conflict detection",
              "Maintenance workflow with technician assignment",
              "Physical audit cycles & discrepancy reports",
            ].map((f) => (
              <li key={f} className="flex items-center gap-2.5">
                <ShieldCheck className="size-4 text-sidebar-accent" />
                {f}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative text-xs text-sidebar-foreground/50">
          © 2026 AssetFlow. All rights reserved.
        </p>
      </div>

      {/* Form panel */}
      <div className="flex w-full flex-col lg:w-1/2">
        <div className="flex justify-end p-4">
          <ThemeToggle />
        </div>
        <div className="flex flex-1 items-center justify-center px-6 pb-16">
          <div className="w-full max-w-sm">
            <div className="mb-8 flex items-center gap-3 lg:hidden">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
                <Boxes className="size-5" />
              </div>
              <span className="text-lg font-semibold">AssetFlow</span>
            </div>

            <div className="mb-6 space-y-1">
              <h2 className="text-2xl font-semibold tracking-tight">Welcome back</h2>
              <p className="text-sm text-muted-foreground">
                Sign in to your AssetFlow workspace to continue.
              </p>
            </div>

            {authError && (
              <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
                {authError}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <Field label="Email address" htmlFor="email" error={errors.email?.message} required>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="you@company.com"
                    className="pl-9"
                    {...register("email")}
                  />
                </div>
              </Field>

              <Field label="Password" htmlFor="password" error={errors.password?.message} required>
                <div className="relative">
                  <Lock className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    className="px-9"
                    {...register("password")}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((s) => !s)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </Field>

              <Button type="submit" className="w-full" loading={isSubmitting}>
                Sign in
              </Button>
            </form>

            <div className="mt-8">
              <div className="relative mb-4">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-background px-2 text-xs uppercase tracking-wide text-muted-foreground">
                    Demo accounts
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {DEMO_ACCOUNTS.map((a) => (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => quickFill(a.email, a.password)}
                    className="rounded-lg border px-3 py-2 text-left transition-colors hover:border-primary hover:bg-primary/5"
                  >
                    <p className="text-xs font-semibold">{ROLE_LABELS[a.role]}</p>
                    <p className="truncate text-[11px] text-muted-foreground">{a.email}</p>
                  </button>
                ))}
              </div>
              <p className="mt-3 text-center text-xs text-muted-foreground">
                Click a role to autofill, then press <span className="font-medium">Sign in</span>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
