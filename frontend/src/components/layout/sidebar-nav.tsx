"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Boxes } from "lucide-react";
import { NAV_SECTIONS } from "@/lib/nav";
import { useUnreadCount } from "@/lib/hooks/use-notifications";
import { cn } from "@/lib/utils";

interface SidebarNavProps {
  onNavigate?: () => void;
}

export function SidebarNav({ onNavigate }: SidebarNavProps) {
  const pathname = usePathname();
  const { data: unread } = useUnreadCount();

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      {/* Brand */}
      <div className="flex h-16 items-center gap-2.5 border-b border-sidebar-border px-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-sidebar-accent text-white shadow-sm">
          <Boxes className="size-5" />
        </div>
        <div className="leading-tight">
          <p className="text-sm font-semibold text-white">AssetFlow</p>
          <p className="text-[11px] text-sidebar-foreground/70">Enterprise Suite</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="no-scrollbar flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title}>
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-sidebar-foreground/50">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active =
                  pathname === item.href || pathname.startsWith(`${item.href}/`);
                const badge =
                  item.badgeKey === "notifications" && unread?.unread
                    ? unread.unread
                    : null;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onNavigate}
                      className={cn(
                        "group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                        active
                          ? "bg-sidebar-accent/15 text-white"
                          : "text-sidebar-foreground/80 hover:bg-white/5 hover:text-white",
                      )}
                    >
                      <item.icon
                        className={cn(
                          "size-4.5 shrink-0 transition-colors",
                          active ? "text-sidebar-accent" : "text-sidebar-foreground/60 group-hover:text-white",
                        )}
                      />
                      <span className="flex-1 truncate">{item.label}</span>
                      {badge != null && (
                        <span className="inline-flex min-w-5 items-center justify-center rounded-full bg-sidebar-accent px-1.5 text-[11px] font-semibold text-white">
                          {badge > 99 ? "99+" : badge}
                        </span>
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-sidebar-border px-5 py-4">
        <p className="text-[11px] text-sidebar-foreground/50">v1.0.0 · © 2026 AssetFlow</p>
      </div>
    </div>
  );
}
