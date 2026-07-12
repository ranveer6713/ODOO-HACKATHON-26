"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ClipboardCheck, Lock, Play, Plus } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuditCycles, useCreateCycle, useCycleAction } from "@/lib/hooks/use-audit";
import { useDepartments } from "@/lib/hooks/use-entities";
import { AUDIT_CYCLE_STATUS, PAGE_SIZE } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import type { AuditCycle } from "@/lib/api/types";

const schema = z
  .object({
    name: z.string().min(3, "Name is required"),
    department_id: z.string().optional(),
    location: z.string().optional(),
    start_date: z.string().min(1, "Start date required"),
    end_date: z.string().min(1, "End date required"),
  })
  .refine((v) => v.end_date >= v.start_date, {
    message: "End date must be after start",
    path: ["end_date"],
  });
type FormValues = z.infer<typeof schema>;

export default function AuditPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const params = useMemo(() => ({ page, page_size: PAGE_SIZE }), [page]);
  const { data, isLoading, isError, refetch } = useAuditCycles(params);
  const { data: departments } = useDepartments({ page_size: 100 });
  const create = useCreateCycle();
  const cycleAction = useCycleAction();

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
    reset({ name: "", department_id: "", location: "", start_date: "", end_date: "" });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    create.mutate(
      {
        name: values.name,
        department_id: values.department_id || null,
        location: values.location || null,
        start_date: values.start_date,
        end_date: values.end_date,
      },
      { onSuccess: () => setDialogOpen(false) },
    );
  }

  const columns: Column<AuditCycle>[] = [
    {
      key: "name",
      header: "Audit Cycle",
      cell: (c) => (
        <div>
          <p className="font-medium">{c.name}</p>
          <p className="text-xs text-muted-foreground">
            {formatDate(c.start_date)} → {formatDate(c.end_date)}
          </p>
        </div>
      ),
    },
    {
      key: "department",
      header: "Scope",
      cell: (c) => (
        <span className="text-sm">
          {departments?.items.find((d) => d.id === c.department_id)?.name ?? c.location ?? "Estate-wide"}
        </span>
      ),
    },
    { key: "created_by", header: "Created by", cell: (c) => c.created_by },
    { key: "status", header: "Status", cell: (c) => <StatusBadge meta={AUDIT_CYCLE_STATUS[c.status]} /> },
    {
      key: "actions",
      header: "",
      headClassName: "w-36",
      cell: (c) => (
        <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
          {c.status === "created" && (
            <Button
              variant="outline"
              size="sm"
              loading={cycleAction.isPending}
              onClick={() => cycleAction.mutate({ id: c.id, action: "start" })}
            >
              <Play className="size-4" /> Start
            </Button>
          )}
          {c.status === "active" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => cycleAction.mutate({ id: c.id, action: "close" })}
            >
              <Lock className="size-4" /> Close
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => router.push(`/audit/${c.id}`)}>
            Open
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Audit"
        description="Run physical verification cycles and surface discrepancies."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New Audit Cycle
          </Button>
        }
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          <Card className="p-0">
            <DataTable
              columns={columns}
              data={data?.items ?? []}
              rowKey={(c) => c.id}
              loading={isLoading}
              onRowClick={(c) => router.push(`/audit/${c.id}`)}
              columnToggle={false}
              empty={
                <EmptyState
                  icon={ClipboardCheck}
                  title="No audit cycles"
                  description="Create an audit cycle to begin verifying physical assets."
                  action={
                    <Button onClick={openCreate}>
                      <Plus className="size-4" /> New Audit Cycle
                    </Button>
                  }
                />
              }
            />
          </Card>
          <Pagination meta={data?.meta} onPageChange={setPage} />
        </>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Audit Cycle</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Field label="Cycle name" htmlFor="name" error={errors.name?.message} required>
              <Input id="name" {...register("name")} placeholder="Q3 2026 IT Audit" />
            </Field>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Department" htmlFor="department_id">
                <Select value={watch("department_id") || ""} onValueChange={(v) => setValue("department_id", v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Estate-wide" />
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
              <Field label="Location" htmlFor="location">
                <Input id="location" {...register("location")} placeholder="HQ · Floor 4" />
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Start date" htmlFor="start_date" error={errors.start_date?.message} required>
                <Input id="start_date" type="date" {...register("start_date")} />
              </Field>
              <Field label="End date" htmlFor="end_date" error={errors.end_date?.message} required>
                <Input id="end_date" type="date" {...register("end_date")} />
              </Field>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create cycle
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
