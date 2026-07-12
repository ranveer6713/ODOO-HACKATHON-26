"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ArrowLeftRight, ArrowRight, Check, Plus, X } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAssets, useDepartments, useTransferMutations, useTransfers } from "@/lib/hooks/use-entities";
import { useLookups } from "@/lib/hooks/use-lookups";
import { useSession } from "@/lib/auth/use-session";
import { PAGE_SIZE, type Tone } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import type { Transfer } from "@/lib/api/types";

const schema = z.object({
  asset_id: z.string().min(1, "Select an asset"),
  to_department_id: z.string().min(1, "Select a destination"),
  reason: z.string().min(3, "Reason is required"),
});
type FormValues = z.infer<typeof schema>;

const STATUS_TONE: Record<Transfer["status"], { tone: Tone; label: string }> = {
  pending: { tone: "warning", label: "Pending" },
  approved: { tone: "info", label: "Approved" },
  completed: { tone: "success", label: "Completed" },
  rejected: { tone: "danger", label: "Rejected" },
};

export default function TransfersPage() {
  const [tab, setTab] = useState<"all" | Transfer["status"]>("all");
  const [page, setPage] = useState(1);
  const params = useMemo(
    () => ({ status: tab === "all" ? undefined : tab, page, page_size: PAGE_SIZE }),
    [tab, page],
  );
  const { data, isLoading } = useTransfers(params);
  const { data: assets } = useAssets({ page_size: 200 });
  const { data: departments } = useDepartments({ page_size: 100 });
  const lookups = useLookups();
  const { session } = useSession();
  const { create, setStatus } = useTransferMutations();

  const [dialogOpen, setDialogOpen] = useState(false);
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  function openCreate() {
    reset({ asset_id: "", to_department_id: "", reason: "" });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    const asset = assets?.items.find((a) => a.id === values.asset_id);
    create.mutate(
      {
        asset_id: values.asset_id,
        from_department_id: asset?.department_id ?? null,
        to_department_id: values.to_department_id,
        reason: values.reason,
        requested_by: session?.id ?? "EMP-1002",
      },
      { onSuccess: () => setDialogOpen(false) },
    );
  }

  const columns: Column<Transfer>[] = [
    {
      key: "asset",
      header: "Asset",
      cell: (t) => (
        <div>
          <p className="font-medium">{lookups.assetName(t.asset_id)}</p>
          <p className="font-mono text-xs text-muted-foreground">{lookups.assetTag(t.asset_id)}</p>
        </div>
      ),
    },
    {
      key: "route",
      header: "Route",
      cell: (t) => (
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">{lookups.departmentName(t.from_department_id)}</span>
          <ArrowRight className="size-3.5 text-muted-foreground" />
          <span className="font-medium">{lookups.departmentName(t.to_department_id)}</span>
        </div>
      ),
    },
    { key: "reason", header: "Reason", cell: (t) => <span className="line-clamp-1 max-w-xs">{t.reason}</span> },
    { key: "requested_by", header: "Requested by", cell: (t) => lookups.employeeName(t.requested_by) },
    { key: "created_at", header: "Date", cell: (t) => formatDate(t.created_at) },
    {
      key: "status",
      header: "Status",
      cell: (t) => <StatusBadge {...STATUS_TONE[t.status]} />,
    },
    {
      key: "actions",
      header: "",
      headClassName: "w-40",
      cell: (t) => (
        <div className="flex items-center gap-1.5">
          {t.status === "pending" && (
            <>
              <Button variant="outline" size="sm" onClick={() => setStatus.mutate({ id: t.id, status: "approved" })}>
                <Check className="size-4" /> Approve
              </Button>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-destructive"
                onClick={() => setStatus.mutate({ id: t.id, status: "rejected" })}
              >
                <X className="size-4" />
              </Button>
            </>
          )}
          {t.status === "approved" && (
            <Button variant="outline" size="sm" onClick={() => setStatus.mutate({ id: t.id, status: "completed" })}>
              <Check className="size-4" /> Complete
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Transfers"
        description="Move assets between departments with an approval workflow."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New Transfer
          </Button>
        }
      />

      <Card className="p-4">
        <Tabs value={tab} onValueChange={(v) => { setTab(v as typeof tab); setPage(1); }}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="approved">Approved</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
        </Tabs>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        rowKey={(t) => t.id}
        loading={isLoading}
        columnToggle={false}
        empty={
          <EmptyState
            icon={ArrowLeftRight}
            title="No transfers"
            description="Request a transfer to move an asset between departments."
            action={
              <Button onClick={openCreate}>
                <Plus className="size-4" /> New Transfer
              </Button>
            }
          />
        }
      />
      <Pagination meta={data?.meta} onPageChange={setPage} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Transfer Request</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
            <Field label="Destination department" error={errors.to_department_id?.message} required>
              <Select value={watch("to_department_id")} onValueChange={(v) => setValue("to_department_id", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select destination" />
                </SelectTrigger>
                <SelectContent>
                  {departments?.items.map((d) => (
                    <SelectItem key={d.id} value={d.id}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Reason" error={errors.reason?.message} required>
              <Textarea {...register("reason")} rows={3} placeholder="Why is this transfer needed?" />
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Request transfer
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
