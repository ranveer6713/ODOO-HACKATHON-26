"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { MoreHorizontal, Pencil, Plus, Tags, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { SearchInput } from "@/components/shared/search-input";
import { EmptyState } from "@/components/shared/states";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
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
import { useAssets, useCategories, useCategoryMutations } from "@/lib/hooks/use-entities";
import type { AssetCategory } from "@/lib/api/types";

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  code: z.string().min(1, "Code is required").max(8),
  depreciation_years: z.coerce.number().min(0).max(50),
  description: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function CategoriesPage() {
  const [search, setSearch] = useState("");
  const debounced = useDebounce(search);
  const params = useMemo(() => ({ search: debounced || undefined, page_size: 100 }), [debounced]);
  const { data, isLoading } = useCategories(params);
  const { data: assets } = useAssets({ page_size: 100 });
  const { create, update, remove } = useCategoryMutations();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AssetCategory | null>(null);
  const [toDelete, setToDelete] = useState<AssetCategory | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const countFor = (id: string) => assets?.items.filter((a) => a.category_id === id).length ?? 0;

  function openCreate() {
    setEditing(null);
    reset({ name: "", code: "", depreciation_years: 5, description: "" });
    setDialogOpen(true);
  }
  function openEdit(cat: AssetCategory) {
    setEditing(cat);
    reset({
      name: cat.name,
      code: cat.code,
      depreciation_years: cat.depreciation_years,
      description: cat.description,
    });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    const body = {
      name: values.name,
      code: values.code.toUpperCase(),
      depreciation_years: values.depreciation_years,
      description: values.description ?? "",
    };
    if (editing) update.mutate({ id: editing.id, body }, { onSuccess: () => setDialogOpen(false) });
    else create.mutate(body, { onSuccess: () => setDialogOpen(false) });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Categories"
        description="Classification and depreciation profiles for your asset estate."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New Category
          </Button>
        }
      />

      <Card className="p-4">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search categories…"
          className="max-w-sm"
        />
      </Card>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-5">
              <Skeleton className="size-10 rounded-lg" />
              <Skeleton className="mt-4 h-5 w-32" />
              <Skeleton className="mt-2 h-4 w-full" />
            </Card>
          ))}
        </div>
      ) : (data?.items.length ?? 0) === 0 ? (
        <EmptyState
          icon={Tags}
          title="No categories"
          description="Create categories to classify and depreciate your assets."
          action={
            <Button onClick={openCreate}>
              <Plus className="size-4" /> New Category
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data?.items.map((cat) => (
            <Card key={cat.id} className="group transition-colors hover:border-primary/40">
              <CardContent className="p-5">
                <div className="flex items-start justify-between">
                  <div className="flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Tags className="size-5" />
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon-sm" className="opacity-0 transition-opacity group-hover:opacity-100">
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => openEdit(cat)}>
                        <Pencil className="size-4" /> Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem destructive onClick={() => setToDelete(cat)}>
                        <Trash2 className="size-4" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                <h3 className="mt-4 font-semibold">{cat.name}</h3>
                <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
                  {cat.description || "No description provided."}
                </p>
                <div className="mt-4 flex items-center justify-between border-t pt-3 text-xs">
                  <span className="font-mono text-muted-foreground">{cat.code}</span>
                  <span className="text-muted-foreground">
                    <span className="font-semibold text-foreground">{countFor(cat.id)}</span> assets
                  </span>
                  <span className="text-muted-foreground">
                    <span className="font-semibold text-foreground">{cat.depreciation_years}y</span> life
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? "Edit Category" : "New Category"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <Field label="Name" htmlFor="name" error={errors.name?.message} required className="col-span-2">
                <Input id="name" {...register("name")} placeholder="Laptops" />
              </Field>
              <Field label="Code" htmlFor="code" error={errors.code?.message} required>
                <Input id="code" {...register("code")} placeholder="LAP" className="uppercase" />
              </Field>
            </div>
            <Field
              label="Depreciation (years)"
              htmlFor="depreciation_years"
              error={errors.depreciation_years?.message}
              required
            >
              <Input id="depreciation_years" type="number" min={0} {...register("depreciation_years")} />
            </Field>
            <Field label="Description" htmlFor="description">
              <Textarea id="description" {...register("description")} rows={3} />
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending || update.isPending}>
                {editing ? "Save changes" : "Create category"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!toDelete}
        onOpenChange={(o) => !o && setToDelete(null)}
        title="Delete category?"
        description={`This will permanently remove “${toDelete?.name}”.`}
        confirmLabel="Delete"
        destructive
        loading={remove.isPending}
        onConfirm={() => toDelete && remove.mutate(toDelete.id, { onSuccess: () => setToDelete(null) })}
      />
    </div>
  );
}
