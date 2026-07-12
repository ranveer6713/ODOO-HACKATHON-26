"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PackageCheck, Undo2, UserCog } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Field } from "@/components/shared/form-field";
import { StatCard } from "@/components/shared/stat-card";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import { useAllocationMutations, useAllocations, useAssets, useEmployees } from "@/lib/hooks/use-entities";
import { useLookups } from "@/lib/hooks/use-lookups";
import { PAGE_SIZE } from "@/lib/constants";
import { formatDate, initials } from "@/lib/utils";
import type { Allocation } from "@/lib/api/types";

const schema = z.object({
  asset_id: z.string().min(1, "Select an asset"),
  employee_id: z.string().min(1, "Select an employee"),
  notes: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function AllocationPage() {
  const [tab, setTab] = useState<"all" | "active" | "returned">("active");
  const [page, setPage] = useState(1);
  const params = useMemo(
    () => ({ status: tab === "all" ? undefined : tab, page, page_size: PAGE_SIZE }),
    [tab, page],
  );
  const { data, isLoading } = useAllocations(params);
  const { data: allActive } = useAllocations({ status: "active", page_size: 200 });
  const { data: assets } = useAssets({ page_size: 200 });
  const { data: employees } = useEmployees({ page_size: 200 });
  const lookups = useLookups();
  const { create, returnAsset } = useAllocationMutations();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [toReturn, setToReturn] = useState<Allocation | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const availableAssets = assets?.items.filter((a) => a.status === "available") ?? [];

  function openCreate() {
    reset({ asset_id: "", employee_id: "", notes: "" });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    create.mutate(
      { asset_id: values.asset_id, employee_id: values.employee_id, notes: values.notes ?? "" },
      { onSuccess: () => setDialogOpen(false) },
    );
  }

  const columns: Column<Allocation>[] = [
    {
      key: "asset",
      header: "Asset",
      cell: (a) => (
        <div>
          <p className="font-medium">{lookups.assetName(a.asset_id)}</p>
          <p className="font-mono text-xs text-muted-foreground">{lookups.assetTag(a.asset_id)}</p>
        </div>
      ),
    },
    {
      key: "employee",
      header: "Assigned to",
      cell: (a) => (
        <div className="flex items-center gap-2.5">
          <Avatar className="size-8">
            <AvatarFallback>{initials(lookups.employeeName(a.employee_id))}</AvatarFallback>
          </Avatar>
          <span className="text-sm">{lookups.employeeName(a.employee_id)}</span>
        </div>
      ),
    },
    { key: "allocated_at", header: "Allocated", cell: (a) => formatDate(a.allocated_at) },
    {
      key: "returned_at",
      header: "Returned",
      cell: (a) => (a.returned_at ? formatDate(a.returned_at) : "—"),
    },
    {
      key: "status",
      header: "Status",
      cell: (a) => (
        <StatusBadge tone={a.status === "active" ? "primary" : "success"} label={a.status === "active" ? "Active" : "Returned"} />
      ),
    },
    {
      key: "actions",
      header: "",
      headClassName: "w-24",
      cell: (a) =>
        a.status === "active" ? (
          <Button variant="outline" size="sm" onClick={() => setToReturn(a)}>
            <Undo2 className="size-4" /> Return
          </Button>
        ) : null,
    },
  ];

  const activeCount = allActive?.meta.total ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Allocation"
        description="Assign assets to employees and track returns."
        actions={
          <Button onClick={openCreate}>
            <PackageCheck className="size-4" /> Allocate Asset
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard label="Active Allocations" value={activeCount} icon={PackageCheck} tone="primary" />
        <StatCard label="Available Assets" value={availableAssets.length} icon={UserCog} tone="success" />
        <StatCard label="Total Employees" value={employees?.meta.total ?? 0} icon={UserCog} tone="info" />
      </div>

      <Card className="p-4">
        <Tabs value={tab} onValueChange={(v) => { setTab(v as typeof tab); setPage(1); }}>
          <TabsList>
            <TabsTrigger value="active">Active</TabsTrigger>
            <TabsTrigger value="returned">Returned</TabsTrigger>
            <TabsTrigger value="all">All</TabsTrigger>
          </TabsList>
        </Tabs>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        rowKey={(a) => a.id}
        loading={isLoading}
        columnToggle={false}
        empty={
          <EmptyState
            icon={PackageCheck}
            title="No allocations"
            description="Allocate an available asset to an employee to get started."
            action={
              <Button onClick={openCreate}>
                <PackageCheck className="size-4" /> Allocate Asset
              </Button>
            }
          />
        }
      />
      <Pagination meta={data?.meta} onPageChange={setPage} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Allocate Asset</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Field label="Asset" error={errors.asset_id?.message} required>
              <Select value={watch("asset_id")} onValueChange={(v) => setValue("asset_id", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select an available asset" />
                </SelectTrigger>
                <SelectContent>
                  {availableAssets.length === 0 ? (
                    <div className="px-3 py-2 text-sm text-muted-foreground">No available assets</div>
                  ) : (
                    availableAssets.map((a) => (
                      <SelectItem key={a.id} value={a.id}>
                        {a.name} · {a.tag}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Employee" error={errors.employee_id?.message} required>
              <Select value={watch("employee_id")} onValueChange={(v) => setValue("employee_id", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select an employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees?.items.map((e) => (
                    <SelectItem key={e.id} value={e.id}>
                      {e.name} — {e.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <Field label="Notes" htmlFor="notes">
              <Textarea id="notes" {...register("notes")} rows={2} placeholder="Handover notes…" />
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Allocate
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toReturn}
        onOpenChange={(o) => !o && setToReturn(null)}
        title="Return asset?"
        description={`This marks “${lookups.assetName(toReturn?.asset_id)}” as returned and available.`}
        confirmLabel="Confirm return"
        loading={returnAsset.isPending}
        onConfirm={() => toReturn && returnAsset.mutate(toReturn.id, { onSuccess: () => setToReturn(null) })}
      />
    </div>
  );
}
