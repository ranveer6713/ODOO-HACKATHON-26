"use client";

import { useMemo, useState } from "react";
import { Activity, Check, Flag, ShieldCheck } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Pagination } from "@/components/shared/pagination";
import { SearchInput } from "@/components/shared/search-input";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import { useActivityAction, useActivityLogs } from "@/lib/hooks/use-activity";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { SEVERITY } from "@/lib/constants";
import { formatDateTime, fromNow, titleCase } from "@/lib/utils";
import type { ActivityLog, Severity } from "@/lib/api/types";

export default function ActivityLogsPage() {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("all");
  const [actor, setActor] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebounce(search);
  const debouncedActor = useDebounce(actor);

  const params = useMemo(
    () => ({
      search: debounced || undefined,
      severity: severity === "all" ? undefined : severity,
      actor_id: debouncedActor || undefined,
      date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
      date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
      page,
      page_size: 15,
    }),
    [debounced, severity, debouncedActor, dateFrom, dateTo, page],
  );

  const { data, isLoading, isError, refetch } = useActivityLogs(params);
  const action = useActivityAction();
  const [flagging, setFlagging] = useState<ActivityLog | null>(null);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity Logs"
        description="A complete, tamper-evident trail of every action across the platform."
      />

      <Card className="grid grid-cols-1 gap-3 p-4 md:grid-cols-5">
        <SearchInput
          value={search}
          onChange={(v) => { setSearch(v); setPage(1); }}
          placeholder="Search action / entity…"
          className="md:col-span-2"
        />
        <Input
          placeholder="Filter by user id"
          value={actor}
          onChange={(e) => { setActor(e.target.value); setPage(1); }}
        />
        <Select value={severity} onValueChange={(v) => { setSeverity(v); setPage(1); }}>
          <SelectTrigger>
            <SelectValue placeholder="Severity" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All severities</SelectItem>
            {(["info", "warning", "critical"] as Severity[]).map((s) => (
              <SelectItem key={s} value={s}>
                {SEVERITY[s].label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex gap-2">
          <Input
            type="date"
            value={dateFrom}
            onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
            aria-label="From date"
          />
          <Input
            type="date"
            value={dateTo}
            onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
            aria-label="To date"
          />
        </div>
      </Card>

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      ) : (data?.items.length ?? 0) === 0 ? (
        <EmptyState icon={Activity} title="No activity" description="No log entries match your filters." />
      ) : (
        <Card className="p-6">
          <ol className="relative space-y-6 border-l pl-6">
            {data?.items.map((log) => (
              <li key={log.id} className="relative">
                <span
                  className={`absolute -left-[27px] flex size-5 items-center justify-center rounded-full ring-2 ring-border ${
                    log.severity === "critical"
                      ? "bg-destructive"
                      : log.severity === "warning"
                        ? "bg-warning"
                        : "bg-primary"
                  }`}
                >
                  <span className="size-2 rounded-full bg-white" />
                </span>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="text-sm">
                      <span className="font-medium">{log.actor_id}</span>{" "}
                      <span className="text-muted-foreground">{titleCase(log.action)}</span>{" "}
                      <span className="font-medium">{log.entity_type}</span>{" "}
                      <span className="font-mono text-xs text-muted-foreground">#{log.entity_id}</span>
                    </p>
                    {log.description && (
                      <p className="mt-0.5 text-sm text-muted-foreground">{log.description}</p>
                    )}
                    <div className="mt-1.5 flex flex-wrap items-center gap-2">
                      <span className="text-xs text-muted-foreground" title={formatDateTime(log.created_at)}>
                        {fromNow(log.created_at)}
                      </span>
                      {log.severity !== "info" && <StatusBadge meta={SEVERITY[log.severity]} dot={false} />}
                      {log.flagged && <StatusBadge tone="danger" label="Flagged" dot={false} />}
                      {log.acknowledged && <StatusBadge tone="success" label="Acknowledged" dot={false} />}
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon-sm">
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      {!log.flagged && (
                        <DropdownMenuItem onClick={() => setFlagging(log)}>
                          <Flag className="size-4" /> Flag entry
                        </DropdownMenuItem>
                      )}
                      {!log.acknowledged && (
                        <DropdownMenuItem
                          onClick={() => action.mutate({ id: log.id, action: "acknowledge" })}
                        >
                          <Check className="size-4" /> Acknowledge
                        </DropdownMenuItem>
                      )}
                      {log.flagged && log.acknowledged && (
                        <DropdownMenuItem disabled>
                          <ShieldCheck className="size-4" /> No actions
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-2">
            <Pagination meta={data?.meta} onPageChange={setPage} />
          </div>
        </Card>
      )}

      <ConfirmDialog
        open={!!flagging}
        onOpenChange={(o) => !o && setFlagging(null)}
        title="Flag activity entry?"
        description="Flagged entries are escalated for review."
        confirmLabel="Flag entry"
        destructive
        reasonLabel="Reason"
        reasonRequired
        loading={action.isPending}
        onConfirm={(reason) =>
          flagging &&
          action.mutate({ id: flagging.id, action: "flag", reason }, { onSuccess: () => setFlagging(null) })
        }
      />
    </div>
  );
}
