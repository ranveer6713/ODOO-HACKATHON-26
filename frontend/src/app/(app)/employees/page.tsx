"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MoreHorizontal, Pencil, Plus, Trash2, Users } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { SearchInput } from "@/components/shared/search-input";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
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
import { useDebounce } from "@/lib/hooks/use-debounce";
import {
  useDepartments,
  useEmployeeMutations,
  useEmployees,
} from "@/lib/hooks/use-entities";
import { PAGE_SIZE } from "@/lib/constants";
import { initials } from "@/lib/utils";
import { ROLE_LABELS, type UserRole } from "@/lib/auth/session";
import type { Employee } from "@/lib/api/types";

const ROLES: UserRole[] = ["admin", "asset_manager", "technician", "employee"];

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  email: z.string().email("Valid email required"),
  title: z.string().min(2, "Title is required"),
  phone: z.string().optional(),
  role: z.enum(["admin", "asset_manager", "technician", "employee"]),
  department_id: z.string().min(1, "Department is required"),
  status: z.enum(["active", "inactive"]),
});
type FormValues = z.infer<typeof schema>;

export default function EmployeesPage() {
  const [search, setSearch] = useState("");
  const [dept, setDept] = useState<string>("all");
  const [page, setPage] = useState(1);
  const debounced = useDebounce(search);
  const params = useMemo(
    () => ({
      search: debounced || undefined,
      department_id: dept === "all" ? undefined : dept,
      page,
      page_size: PAGE_SIZE,
    }),
    [debounced, dept, page],
  );
  const { data, isLoading } = useEmployees(params);
  const { data: departments } = useDepartments({ page_size: 100 });
  const { create, update, remove } = useEmployeeMutations();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [toDelete, setToDelete] = useState<Employee | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const deptName = (id: string) => departments?.items.find((d) => d.id === id)?.name ?? id;

  function openCreate() {
    setEditing(null);
    reset({
      name: "",
      email: "",
      title: "",
      phone: "",
      role: "employee",
      department_id: departments?.items[0]?.id ?? "",
      status: "active",
    });
    setDialogOpen(true);
  }
  function openEdit(emp: Employee) {
    setEditing(emp);
    reset({
      name: emp.name,
      email: emp.email,
      title: emp.title,
      phone: emp.phone,
      role: emp.role as UserRole,
      department_id: emp.department_id,
      status: emp.status,
    });
    setDialogOpen(true);
  }

  function onSubmit(values: FormValues) {
    const body = { ...values, phone: values.phone ?? "" };
    if (editing) update.mutate({ id: editing.id, body }, { onSuccess: () => setDialogOpen(false) });
    else create.mutate(body, { onSuccess: () => setDialogOpen(false) });
  }

  const columns: Column<Employee>[] = [
    {
      key: "name",
      header: "Employee",
      sortable: true,
      cell: (e) => (
        <div className="flex items-center gap-3">
          <Avatar>
            <AvatarFallback>{initials(e.name)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{e.name}</p>
            <p className="text-xs text-muted-foreground">{e.email}</p>
          </div>
        </div>
      ),
    },
    { key: "title", header: "Title", cell: (e) => e.title },
    { key: "department", header: "Department", cell: (e) => deptName(e.department_id) },
    {
      key: "role",
      header: "Role",
      cell: (e) => <StatusBadge tone="purple" label={ROLE_LABELS[e.role as UserRole] ?? e.role} dot={false} />,
    },
    {
      key: "status",
      header: "Status",
      cell: (e) => (
        <StatusBadge tone={e.status === "active" ? "success" : "neutral"} label={e.status === "active" ? "Active" : "Inactive"} />
      ),
    },
    {
      key: "actions",
      header: "",
      headClassName: "w-10",
      cell: (e) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm" onClick={(ev) => ev.stopPropagation()}>
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => openEdit(e)}>
              <Pencil className="size-4" /> Edit
            </DropdownMenuItem>
            <DropdownMenuItem destructive onClick={() => setToDelete(e)}>
              <Trash2 className="size-4" /> Remove
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Employees"
        description="People who request, hold and maintain assets across the organization."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> Add Employee
          </Button>
        }
      />

      <Card className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <SearchInput
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(1);
          }}
          placeholder="Search by name or email…"
          className="sm:max-w-sm"
        />
        <Select
          value={dept}
          onValueChange={(v) => {
            setDept(v);
            setPage(1);
          }}
        >
          <SelectTrigger className="sm:w-56">
            <SelectValue placeholder="All departments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All departments</SelectItem>
            {departments?.items.map((d) => (
              <SelectItem key={d.id} value={d.id}>
                {d.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Card>

      <DataTable
        columns={columns}
        data={data?.items ?? []}
        rowKey={(e) => e.id}
        loading={isLoading}
        onRowClick={openEdit}
        empty={
          <EmptyState
            icon={Users}
            title="No employees found"
            description="Adjust your filters or add a new employee."
            action={
              <Button onClick={openCreate}>
                <Plus className="size-4" /> Add Employee
              </Button>
            }
          />
        }
      />
      <Pagination meta={data?.meta} onPageChange={setPage} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Employee" : "Add Employee"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Field label="Full name" htmlFor="name" error={errors.name?.message} required>
                <Input id="name" {...register("name")} />
              </Field>
              <Field label="Email" htmlFor="email" error={errors.email?.message} required>
                <Input id="email" type="email" {...register("email")} />
              </Field>
              <Field label="Job title" htmlFor="title" error={errors.title?.message} required>
                <Input id="title" {...register("title")} />
              </Field>
              <Field label="Phone" htmlFor="phone" error={errors.phone?.message}>
                <Input id="phone" {...register("phone")} />
              </Field>
              <Field label="Role" error={errors.role?.message} required>
                <Select value={watch("role")} onValueChange={(v) => setValue("role", v as UserRole)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ROLES.map((r) => (
                      <SelectItem key={r} value={r}>
                        {ROLE_LABELS[r]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Department" error={errors.department_id?.message} required>
                <Select
                  value={watch("department_id")}
                  onValueChange={(v) => setValue("department_id", v)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select department" />
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
              <Field label="Status" error={errors.status?.message} required>
                <Select value={watch("status")} onValueChange={(v) => setValue("status", v as "active" | "inactive")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </Field>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending || update.isPending}>
                {editing ? "Save changes" : "Add employee"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Remove employee?"
        description={`This removes “${toDelete?.name}” from the directory.`}
        confirmLabel="Remove"
        destructive
        loading={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id, { onSuccess: () => setToDelete(null) })}
      />
    </div>
  );
}
