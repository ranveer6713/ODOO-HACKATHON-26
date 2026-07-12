"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Archive,
  Bell,
  CheckCheck,
  Check,
  TriangleAlert,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useArchiveNotification,
  useMarkAllRead,
  useMarkRead,
  useNotificationsByView,
  useUnreadCount,
} from "@/lib/hooks/use-notifications";
import { NOTIFICATION_TYPE, SEVERITY } from "@/lib/constants";
import { cn, fromNow } from "@/lib/utils";
import type { AppNotification } from "@/lib/api/types";

const TABS = [
  { value: "all", label: "All" },
  { value: "unread", label: "Unread" },
  { value: "read", label: "Read" },
  { value: "critical", label: "Critical" },
  { value: "archived", label: "Archived" },
] as const;

export default function NotificationsPage() {
  const [view, setView] = useState<(typeof TABS)[number]["value"]>("all");
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({ view, page, page_size: 15 }), [view, page]);
  const { data, isLoading, isError, refetch } = useNotificationsByView(params);
  const { data: unread } = useUnreadCount();
  const markRead = useMarkRead();
  const markAll = useMarkAllRead();
  const archive = useArchiveNotification();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        description="System alerts across bookings, maintenance, audits and operations."
        actions={
          (unread?.unread ?? 0) > 0 && (
            <Button variant="outline" onClick={() => markAll.mutate()} loading={markAll.isPending}>
              <CheckCheck className="size-4" /> Mark all read
            </Button>
          )
        }
      />

      <Tabs value={view} onValueChange={(v) => { setView(v as typeof view); setPage(1); }}>
        <TabsList>
          {TABS.map((t) => (
            <TabsTrigger key={t.value} value={t.value}>
              {t.label}
              {t.value === "unread" && (unread?.unread ?? 0) > 0 && (
                <span className="ml-1.5 rounded-full bg-primary px-1.5 text-[11px] font-semibold text-primary-foreground">
                  {unread?.unread}
                </span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-xl" />
          ))}
        </div>
      ) : (data?.items.length ?? 0) === 0 ? (
        <EmptyState
          icon={Bell}
          title="No notifications"
          description={view === "unread" ? "You're all caught up." : "Nothing to show in this view."}
        />
      ) : (
        <div className="space-y-2">
          {data?.items.map((n) => (
            <NotificationRow
              key={n.id}
              n={n}
              onRead={() => markRead.mutate(n.id)}
              onArchive={() => archive.mutate(n.id)}
              archiving={archive.isPending}
            />
          ))}
          <Pagination meta={data?.meta} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}

function NotificationRow({
  n,
  onRead,
  onArchive,
  archiving,
}: {
  n: AppNotification;
  onRead: () => void;
  onArchive: () => void;
  archiving: boolean;
}) {
  const href =
    n.entity_type === "booking"
      ? "/booking"
      : n.entity_type === "maintenance"
        ? "/maintenance"
        : n.entity_type === "audit_cycle" || n.entity_type === "audit"
          ? "/audit"
          : null;

  return (
    <Card
      className={cn(
        "flex items-start gap-4 p-4 transition-colors",
        !n.is_read && "border-primary/30 bg-primary/[0.03]",
      )}
    >
      <div
        className={cn(
          "flex size-10 shrink-0 items-center justify-center rounded-lg",
          n.severity === "critical"
            ? "bg-destructive/10 text-destructive"
            : n.severity === "warning"
              ? "bg-warning/15 text-warning"
              : "bg-primary/10 text-primary",
        )}
      >
        {n.severity === "critical" ? <TriangleAlert className="size-5" /> : <Bell className="size-5" />}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="font-medium">{n.title}</p>
          <StatusBadge meta={NOTIFICATION_TYPE[n.type]} dot={false} />
          {n.severity !== "info" && <StatusBadge meta={SEVERITY[n.severity]} dot={false} />}
          {!n.is_read && <span className="size-2 rounded-full bg-primary" />}
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{n.message}</p>
        <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
          <span>{fromNow(n.created_at)}</span>
          {href && (
            <Link href={href} className="font-medium text-primary hover:underline">
              View {n.entity_type}
            </Link>
          )}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {!n.is_read && (
          <Button variant="ghost" size="icon-sm" onClick={onRead} title="Mark read">
            <Check className="size-4" />
          </Button>
        )}
        {!n.archived && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onArchive}
            disabled={archiving}
            title="Archive"
          >
            <Archive className="size-4" />
          </Button>
        )}
      </div>
    </Card>
  );
}
