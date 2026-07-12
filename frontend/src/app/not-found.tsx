import Link from "next/link";
import { Boxes, Home } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-center">
      <div className="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
        <Boxes className="size-7" />
      </div>
      <div className="space-y-2">
        <p className="text-6xl font-bold tracking-tight">404</p>
        <h1 className="text-xl font-semibold">Page not found</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </div>
      <Button asChild>
        <Link href="/dashboard">
          <Home className="size-4" /> Back to dashboard
        </Link>
      </Button>
    </div>
  );
}
