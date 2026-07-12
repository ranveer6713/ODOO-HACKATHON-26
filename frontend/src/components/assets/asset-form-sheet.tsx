"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { FileText, ImagePlus, Upload } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Field } from "@/components/shared/form-field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAssetMutations, useCategories, useDepartments, useEmployees } from "@/lib/hooks/use-entities";
import { toDatetimeLocal } from "@/lib/utils";
import { ASSET_STATUS } from "@/lib/constants";
import type { Asset, AssetStatus } from "@/lib/api/types";

const schema = z.object({
  name: z.string().min(2, "Name is required"),
  category_id: z.string().min(1, "Category is required"),
  status: z.string().min(1),
  serial_number: z.string().min(1, "Serial number is required"),
  manufacturer: z.string().optional(),
  model: z.string().optional(),
  department_id: z.string().optional(),
  assigned_to: z.string().optional(),
  location: z.string().optional(),
  purchase_cost: z.coerce.number().min(0),
  purchase_date: z.string().optional(),
  image_url: z.string().optional(),
  notes: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

interface AssetFormSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  asset?: Asset | null;
}

const STATUS_KEYS = Object.keys(ASSET_STATUS) as AssetStatus[];

export function AssetFormSheet({ open, onOpenChange, asset }: AssetFormSheetProps) {
  const { data: categories } = useCategories({ page_size: 100 });
  const { data: departments } = useDepartments({ page_size: 100 });
  const { data: employees } = useEmployees({ page_size: 100 });
  const { create, update } = useAssetMutations();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  useEffect(() => {
    if (!open) return;
    reset({
      name: asset?.name ?? "",
      category_id: asset?.category_id ?? categories?.items[0]?.id ?? "",
      status: asset?.status ?? "available",
      serial_number: asset?.serial_number ?? "",
      manufacturer: asset?.manufacturer ?? "",
      model: asset?.model ?? "",
      department_id: asset?.department_id ?? "",
      assigned_to: asset?.assigned_to ?? "",
      location: asset?.location ?? "",
      purchase_cost: asset?.purchase_cost ?? 0,
      purchase_date: toDatetimeLocal(asset?.purchase_date) || "",
      image_url: asset?.image_url ?? "",
      notes: asset?.notes ?? "",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, asset]);

  function onSubmit(values: FormValues) {
    const body = {
      name: values.name,
      category_id: values.category_id,
      status: values.status as AssetStatus,
      serial_number: values.serial_number,
      manufacturer: values.manufacturer ?? "",
      model: values.model ?? "",
      department_id: values.department_id || null,
      assigned_to: values.assigned_to || null,
      location: values.location ?? "",
      purchase_cost: values.purchase_cost,
      purchase_date: values.purchase_date
        ? new Date(values.purchase_date).toISOString()
        : new Date().toISOString(),
      image_url: values.image_url || null,
      notes: values.notes ?? "",
    };
    if (asset) update.mutate({ id: asset.id, body }, { onSuccess: () => onOpenChange(false) });
    else create.mutate(body, { onSuccess: () => onOpenChange(false) });
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>{asset ? "Edit Asset" : "Register Asset"}</SheetTitle>
          <SheetDescription>
            {asset ? `Update details for ${asset.tag}.` : "Add a new asset to the estate."}
          </SheetDescription>
        </SheetHeader>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="flex flex-1 flex-col overflow-hidden"
          id="asset-form"
        >
          <div className="flex-1 space-y-4 overflow-y-auto p-6">
            {/* Image upload */}
            <div className="flex items-center gap-4 rounded-xl border border-dashed p-4">
              <div className="flex size-16 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <ImagePlus className="size-6" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium">Asset image</p>
                <p className="text-xs text-muted-foreground">Paste an image URL or upload a photo.</p>
                <Input
                  className="mt-2"
                  placeholder="https://…"
                  {...register("image_url")}
                />
              </div>
            </div>

            <Field label="Asset name" htmlFor="name" error={errors.name?.message} required>
              <Input id="name" {...register("name")} placeholder={'MacBook Pro 16"'} />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Category" error={errors.category_id?.message} required>
                <Select value={watch("category_id")} onValueChange={(v) => setValue("category_id", v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories?.items.map((c) => (
                      <SelectItem key={c.id} value={c.id}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
              <Field label="Status" error={errors.status?.message} required>
                <Select value={watch("status")} onValueChange={(v) => setValue("status", v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_KEYS.map((s) => (
                      <SelectItem key={s} value={s}>
                        {ASSET_STATUS[s].label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Manufacturer" htmlFor="manufacturer">
                <Input id="manufacturer" {...register("manufacturer")} />
              </Field>
              <Field label="Model" htmlFor="model">
                <Input id="model" {...register("model")} />
              </Field>
            </div>

            <Field label="Serial number" htmlFor="serial_number" error={errors.serial_number?.message} required>
              <Input id="serial_number" {...register("serial_number")} className="font-mono" />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Department" htmlFor="department_id">
                <Select value={watch("department_id") || ""} onValueChange={(v) => setValue("department_id", v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Unassigned" />
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
              <Field label="Assigned to" htmlFor="assigned_to">
                <Select value={watch("assigned_to") || ""} onValueChange={(v) => setValue("assigned_to", v)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Unassigned" />
                  </SelectTrigger>
                  <SelectContent>
                    {employees?.items.map((e) => (
                      <SelectItem key={e.id} value={e.id}>
                        {e.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            </div>

            <Field label="Location" htmlFor="location">
              <Input id="location" {...register("location")} placeholder="HQ · Floor 4" />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label="Purchase cost (USD)" htmlFor="purchase_cost" error={errors.purchase_cost?.message}>
                <Input id="purchase_cost" type="number" min={0} step="0.01" {...register("purchase_cost")} />
              </Field>
              <Field label="Purchase date" htmlFor="purchase_date">
                <Input id="purchase_date" type="datetime-local" {...register("purchase_date")} />
              </Field>
            </div>

            <Field label="Notes" htmlFor="notes">
              <Textarea id="notes" {...register("notes")} rows={2} />
            </Field>

            {/* Document upload */}
            <div className="flex items-center justify-between rounded-lg border border-dashed p-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="size-4" /> Attach purchase documents
              </div>
              <Button type="button" variant="outline" size="sm">
                <Upload className="size-4" /> Upload
              </Button>
            </div>
          </div>

          <SheetFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" form="asset-form" loading={create.isPending || update.isPending}>
              {asset ? "Save changes" : "Register asset"}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
