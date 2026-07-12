"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Boxes, MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { SearchInput } from "@/components/shared/search-input";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState } from "@/components/shared/states";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Card } from "@/components/ui/card";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { useDepartmentMutations, useDepartments, useEmployees } from "@/lib/hooks/use-entities";
import { PAGE_SIZE } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import type { Department } from "@/lib/api/types";

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  code: z.string().min(1, "Code is required").max(8, "Max 8 characters"),
  manager_id: z.string().optional(),
  location: z.string().min(1, "Location is required"),
  description: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function DepartmentsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebounce(search);
  const params = useMemo(
    () => ({ search: debounced || undefined, page, page_size: PAGE_SIZE }),
    [debounced, page],
  );
  const { data, isLoading } = useDepartments(params);
  const { data: employees } = useEmployees({ page_size: 100 });
  const { create, update, remove } = useDepartmentMutations();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);
  const [toDelete, setToDelete] = useState<Department | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  function openCreate() {
    setEditing(null);
    reset({ name: "", code: "", manager_id: "", location: "", description: "" });
    setDialogOpen(true);
  }
  function openEdit(dep: Department) {
    setEditing(dep);
    reset({
      name: dep.name,
      code: dep.code,
      manager_id: dep.manager_id ?? "",
      location: dep.location,
      description: dep.description,
    });
    setDialogOpen(true);
  }

  function onSubmit(values: FormValues) {
    const body = {
      name: values.name,
      code: values.code.toUpperCase(),
      manager_id: values.manager_id || null,
      location: values.location,
      description: values.description ?? "",
    };
    if (editing) {
      update.mutate({ id: editing.id, body }, { onSuccess: () => setDialogOpen(false) });
    } else {
      create.mutate(body, { onSuccess: () => setDialogOpen(false) });
    }
  }

  const managerName = (id: string | null) =>
    employees?.items.find((e) => e.id === id)?.name ?? "Unassigned";

  const columns: Column<Department>[] = [
    {
      key: "name",
      header: "Department",
      sortable: true,
      cell: (d) => (
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Boxes className="size-4.5" />
          </div>
          <div>
            <p className="font-medium">{d.name}</p>
            <p className="text-xs text-muted-foreground">{d.code}</p>
          </div>
        </div>
      ),
    },
    { key: "location", header: "Location", cell: (d) => d.location },
    { key: "manager", header: "Manager", cell: (d) => managerName(d.manager_id) },
    {
      key: "created_at",
      header: "Created",
      sortable: true,
      cell: (d) => <span className="text-muted-foreground">{formatDate(d.created_at)}</span>,
    },
    {
      key: "actions",
      header: "",
      headClassName: "w-10",
      cell: (d) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" onClick={(e) => e.stopPropagation()}>
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openEdit(d)}>
              <Pencil className="size-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem destructive onClick={() => setToDelete(d)}>
              <Trash2 className="size-4" /> Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Departments"
        description="Organizational units that own and operate assets."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New Department
          </Button>
        }
      />

      <Card className="p-4">
        <SearchInput
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(1);
          }}
          placeholder="Search departments…"
          className="max-w-sm"
        />
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        rowKey={(d) => d.id}
        loading={isLoading}
        onRowClick={openEdit}
        empty={
          <EmptyState
            icon={Boxes}
            title="No departments"
            description="Create your first department to organize assets and people."
            action={
              <Button onClick={openCreate}>
                <Plus className="size-4" /> New Department
              </Button>
            }
          />
        }
      />
      <Pagination meta={data?.meta} onPageChange={setPage} />

      {/* Create / edit dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Department" : "New Department"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <Field label="Name" htmlFor="name" error={errors.name?.message} required className="col-span-2">
                <Input id="name" {...register("name")} placeholder="Engineering" />
              </Field>
              <Field label="Code" htmlFor="code" error={errors.code?.message} required>
                <Input id="code" {...register("code")} placeholder="ENG" className="uppercase" />
              </Field>
            </div>
            <Field label="Location" htmlFor="location" error={errors.location?.message} required>
              <Input id="location" {...register("location")} placeholder="HQ · Floor 4" />
            </Field>
            <Field label="Manager" error={errors.manager_id?.message}>
              <Select value={watch("manager_id") || ""} onValueChange={(v) => setValue("manager_id", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a manager" />
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
            <Field label="Description" htmlFor="description">
              <Textarea id="description" {...register("description")} rows={3} placeholder="What this department does…" />
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending || update.isPending}>
                {editing ? "Save changes" : "Create department"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete department?"
        description={`This will permanently remove “${toDelete?.name}”. Assets referencing it will keep their id.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() =>
          toDelete && remove.mutate(toDelete.id, { onSuccess: () => setToDelete(null) })
        }
      />
    </div>
  );
}
