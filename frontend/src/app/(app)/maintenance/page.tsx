"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { KanbanSquare, List, Plus, Wrench } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { Field } from "@/components/shared/form-field";
import { MaintenanceDetailSheet } from "@/components/maintenance/maintenance-detail-sheet";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCreateMaintenance, useMaintenanceList } from "@/lib/hooks/use-maintenance";
import { useAssets } from "@/lib/hooks/use-entities";
import { MAINTENANCE_PRIORITY, MAINTENANCE_STATUS, PAGE_SIZE } from "@/lib/constants";
import { fromNow } from "@/lib/utils";
import type { Maintenance, MaintenancePriority, MaintenanceStatus } from "@/lib/api/types";

const PRIORITY_KEYS = Object.keys(MAINTENANCE_PRIORITY) as MaintenancePriority[];

const KANBAN_COLUMNS: { key: MaintenanceStatus; title: string }[] = [
  { key: "pending", title: "Pending" },
  { key: "approved", title: "Approved" },
  { key: "technician_assigned", title: "Assigned" },
  { key: "in_progress", title: "In Progress" },
  { key: "resolved", title: "Resolved" },
];

const schema = z.object({
  asset_id: z.string().min(1, "Select an asset"),
  priority: z.enum(["low", "medium", "high", "critical"]),
  issue_description: z.string().min(5, "Describe the issue"),
  photo_url: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function MaintenancePage() {
  const [status, setStatus] = useState("all");
  const [priority, setPriority] = useState("all");
  const [page, setPage] = useState(1);

  const listParams = useMemo(
    () => ({
      status: status === "all" ? undefined : status,
      priority: priority === "all" ? undefined : priority,
      page,
      page_size: PAGE_SIZE,
    }),
    [status, priority, page],
  );
  const list = useMaintenanceList(listParams);
  const kanban = useMaintenanceList({ page_size: 100 });
  const { data: assets } = useAssets({ page_size: 200 });
  const create = useCreateMaintenance();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selected, setSelected] = useState<Maintenance | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { priority: "medium" } });

  function openCreate() {
    reset({ asset_id: "", priority: "medium", issue_description: "", photo_url: "" });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    create.mutate(
      {
        asset_id: values.asset_id,
        priority: values.priority,
        issue_description: values.issue_description,
        photo_url: values.photo_url || null,
      },
      { onSuccess: () => setDialogOpen(false) },
    );
  }
  function openDetail(r: Maintenance) {
    setSelected(r);
    setDetailOpen(true);
  }

  const columns: Column<Maintenance>[] = [
    { key: "id", header: "ID", cell: (r) => <span className="font-mono text-xs">#{r.id}</span> },
    { key: "asset_id", header: "Asset", cell: (r) => <span className="font-mono text-sm">{r.asset_id}</span> },
    {
      key: "issue",
      header: "Issue",
      cell: (r) => <span className="line-clamp-1 max-w-sm">{r.issue_description}</span>,
    },
    {
      key: "priority",
      header: "Priority",
      cell: (r) => <StatusBadge meta={MAINTENANCE_PRIORITY[r.priority]} dot={false} />,
    },
    { key: "technician_id", header: "Technician", cell: (r) => r.technician_id ?? "—" },
    { key: "status", header: "Status", cell: (r) => <StatusBadge meta={MAINTENANCE_STATUS[r.status]} /> },
    { key: "created_at", header: "Age", cell: (r) => <span className="text-muted-foreground">{fromNow(r.created_at)}</span> },
  ];

  const grouped = useMemo(() => {
    const map: Record<string, Maintenance[]> = {};
    for (const col of KANBAN_COLUMNS) map[col.key] = [];
    for (const r of kanban.data?.items ?? []) {
      if (map[r.status]) map[r.status].push(r);
    }
    return map;
  }, [kanban.data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Maintenance"
        description="Track asset issues through the full repair workflow."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> Raise Request
          </Button>
        }
      />

      <Tabs defaultValue="kanban">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="kanban">
              <KanbanSquare className="size-4" /> Board
            </TabsTrigger>
            <TabsTrigger value="table">
              <List className="size-4" /> Table
            </TabsTrigger>
          </TabsList>
          <div className="flex gap-2">
            <Select value={priority} onValueChange={(v) => { setPriority(v); setPage(1); }}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All priorities</SelectItem>
                {PRIORITY_KEYS.map((p) => (
                  <SelectItem key={p} value={p}>
                    {MAINTENANCE_PRIORITY[p].label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {KANBAN_COLUMNS.map((c) => (
                  <SelectItem key={c.key} value={c.key}>
                    {c.title}
                  </SelectItem>
                ))}
                <SelectItem value="rejected">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <TabsContent value="kanban">
          {kanban.isLoading ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {KANBAN_COLUMNS.map((c) => (
                <Skeleton key={c.key} className="h-64" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {KANBAN_COLUMNS.map((col) => (
                <div key={col.key} className="rounded-xl border bg-muted/30">
                  <div className="flex items-center justify-between border-b px-3 py-2.5">
                    <span className="text-sm font-medium">{col.title}</span>
                    <span className="rounded-full bg-background px-2 text-xs font-semibold text-muted-foreground">
                      {grouped[col.key]?.length ?? 0}
                    </span>
                  </div>
                  <div className="space-y-2 p-2">
                    {(grouped[col.key] ?? []).length === 0 ? (
                      <p className="px-2 py-6 text-center text-xs text-muted-foreground">No requests</p>
                    ) : (
                      grouped[col.key].map((r) => (
                        <button
                          key={r.id}
                          onClick={() => openDetail(r)}
                          className="w-full rounded-lg border bg-card p-3 text-left shadow-sm transition-colors hover:border-primary/40"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs text-muted-foreground">#{r.id}</span>
                            <StatusBadge meta={MAINTENANCE_PRIORITY[r.priority]} dot={false} />
                          </div>
                          <p className="mt-1.5 line-clamp-2 text-sm">{r.issue_description}</p>
                          <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                            <span className="font-mono">{r.asset_id}</span>
                            <span>{fromNow(r.created_at)}</span>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="table">
          {list.isError ? (
            <ErrorState onRetry={() => list.refetch()} />
          ) : (
            <>
              <DataTable
                columns={columns}
                data={list.data?.items ?? []}
                rowKey={(r) => r.id}
                loading={list.isLoading}
                onRowClick={openDetail}
                columnToggle={false}
                empty={
                  <EmptyState
                    icon={Wrench}
                    title="No maintenance requests"
                    description="Raise a request when an asset needs attention."
                  />
                }
              />
              <Pagination meta={list.data?.meta} onPageChange={setPage} />
            </>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Raise Maintenance Request</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Asset" error={errors.asset_id?.message} required>
                <Select value={watch("asset_id")} onValueChange={(v) => setValue("asset_id", v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an asset" />
                  </SelectTrigger>
                  <SelectContent>
                    {assets?.items.map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.name} · {a.tag}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Priority" error={errors.priority?.message} required>
                <Select value={watch("priority")} onValueChange={(v) => setValue("priority", v as MaintenancePriority)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRIORITY_KEYS.map((p) => (
                      <SelectItem key={p} value={p}>
                        {MAINTENANCE_PRIORITY[p].label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            </div>
            <Field label="Issue description" error={errors.issue_description?.message} required>
              <Textarea {...register("issue_description")} rows={4} placeholder="Describe the fault…" />
            </Field>
            <Field label="Photo URL" htmlFor="photo_url" hint="Optional — link to a photo of the issue.">
              <Input id="photo_url" {...register("photo_url")} placeholder="https://…" />
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Submit request
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <MaintenanceDetailSheet request={selected} open={detailOpen} onOpenChange={setDetailOpen} />
    </div>
  );
}
