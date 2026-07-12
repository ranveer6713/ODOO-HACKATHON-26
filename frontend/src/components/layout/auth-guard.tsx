"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Boxes } from "lucide-react";
import { useSession } from "@/lib/auth/use-session";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { session, loading } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !session) router.replace("/login");
  }, [loading, session, router]);

  if (loading || !session) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <div className="flex size-12 animate-pulse items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Boxes className="size-6" />
          </div>
          <p className="text-sm text-muted-foreground">Loading AssetFlow…</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
