"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CornerDownLeft, Package, Search } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { NAV_SECTIONS } from "@/lib/nav";
import { localStore } from "@/lib/api/local-store";
import { cn } from "@/lib/utils";

interface Result {
  label: string;
  sub?: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

export function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const router = useRouter();

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const results = useMemo<Result[]>(() => {
    const q = query.trim().toLowerCase();
    const nav: Result[] = NAV_SECTIONS.flatMap((s) => s.items).map((i) => ({
      label: i.label,
      sub: "Page",
      href: i.href,
      icon: i.icon,
    }));
    const navMatches = q ? nav.filter((n) => n.label.toLowerCase().includes(q)) : nav;

    let assetMatches: Result[] = [];
    if (q.length >= 2 && typeof window !== "undefined") {
      assetMatches = localStore.assets
        .all()
        .filter(
          (a) =>
            a.name.toLowerCase().includes(q) ||
            a.tag.toLowerCase().includes(q) ||
            a.serial_number.toLowerCase().includes(q),
        )
        .slice(0, 5)
        .map((a) => ({
          label: a.name,
          sub: `${a.tag} · Asset`,
          href: `/assets/${a.id}`,
          icon: Package,
        }));
    }
    return [...navMatches.slice(0, 6), ...assetMatches];
  }, [query]);

  useEffect(() => setActive(0), [query]);

  function go(href: string) {
    setOpen(false);
    setQuery("");
    router.push(href);
  }

  return (
    <>
      <Button
        variant="outline"
        className="hidden h-9 w-64 justify-start gap-2 px-3 text-muted-foreground md:flex"
        onClick={() => setOpen(true)}
      >
        <Search className="size-4" />
        <span className="flex-1 text-left text-sm">Search…</span>
        <kbd className="pointer-events-none hidden select-none items-center gap-0.5 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium lg:inline-flex">
          ⌘K
        </kbd>
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={() => setOpen(true)}
        aria-label="Search"
      >
        <Search className="size-4.5" />
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent hideClose className="max-w-xl gap-0 overflow-hidden p-0">
          <div className="flex items-center gap-2 border-b px-4">
            <Search className="size-4 text-muted-foreground" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") {
                  e.preventDefault();
                  setActive((a) => Math.min(a + 1, results.length - 1));
                } else if (e.key === "ArrowUp") {
                  e.preventDefault();
                  setActive((a) => Math.max(a - 1, 0));
                } else if (e.key === "Enter" && results[active]) {
                  go(results[active].href);
                }
              }}
              placeholder="Search pages, assets…"
              className="h-12 flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
          <div className="max-h-80 overflow-y-auto p-2">
            {results.length === 0 ? (
              <p className="px-3 py-8 text-center text-sm text-muted-foreground">
                No results for “{query}”
              </p>
            ) : (
              results.map((r, i) => (
                <button
                  key={`${r.href}-${i}`}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => go(r.href)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors",
                    i === active ? "bg-accent text-accent-foreground" : "hover:bg-muted/60",
                  )}
                >
                  <r.icon className="size-4 text-muted-foreground" />
                  <span className="flex-1">
                    <span className="font-medium">{r.label}</span>
                    {r.sub && <span className="ml-2 text-xs text-muted-foreground">{r.sub}</span>}
                  </span>
                  {i === active && <CornerDownLeft className="size-3.5 text-muted-foreground" />}
                </button>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
