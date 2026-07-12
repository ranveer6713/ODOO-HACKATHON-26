"use client";

import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CalendarClock, CalendarDays, List, Plus, TriangleAlert } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { DataTable, type Column } from "@/components/shared/data-table";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { StatusBadge } from "@/components/shared/status-badge";
import { Field } from "@/components/shared/form-field";
import { BookingCalendar } from "@/components/booking/booking-calendar";
import { BookingDetailSheet } from "@/components/booking/booking-detail-sheet";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
import { useBookings, useCreateBooking } from "@/lib/hooks/use-bookings";
import { useAssets } from "@/lib/hooks/use-entities";
import { BOOKING_STATUS, PAGE_SIZE } from "@/lib/constants";
import { formatDateTime } from "@/lib/utils";
import type { Booking, BookingStatus } from "@/lib/api/types";

const STATUS_KEYS = Object.keys(BOOKING_STATUS) as BookingStatus[];

const schema = z
  .object({
    asset_id: z.string().min(1, "Select an asset"),
    purpose: z.string().min(3, "Describe the purpose"),
    start_time: z.string().min(1, "Start time required"),
    end_time: z.string().min(1, "End time required"),
  })
  .refine((v) => new Date(v.end_time) > new Date(v.start_time), {
    message: "End must be after start",
    path: ["end_time"],
  });
type FormValues = z.infer<typeof schema>;

export default function BookingPage() {
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(1);
  const params = useMemo(
    () => ({
      status: status === "all" ? undefined : status,
      page,
      page_size: PAGE_SIZE,
      sort_by: "start_time",
      order: "desc",
    }),
    [status, page],
  );
  const { data, isLoading, isError, refetch } = useBookings(params);
  const { data: calendarData } = useBookings({ page_size: 100, sort_by: "start_time", order: "asc" });
  const { data: assets } = useAssets({ page_size: 200 });
  const create = useCreateBooking();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selected, setSelected] = useState<Booking | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const watchAsset = watch("asset_id");
  const watchStart = watch("start_time");
  const watchEnd = watch("end_time");

  // Conflict detection against existing active bookings for the same asset.
  const conflict = useMemo(() => {
    if (!watchAsset || !watchStart || !watchEnd) return null;
    const s = new Date(watchStart).getTime();
    const e = new Date(watchEnd).getTime();
    return (calendarData?.items ?? []).find((b) => {
      if (b.asset_id !== watchAsset) return false;
      if (["rejected", "cancelled", "checked_in"].includes(b.status)) return false;
      const bs = new Date(b.start_time).getTime();
      const be = new Date(b.end_time).getTime();
      return s < be && e > bs;
    });
  }, [watchAsset, watchStart, watchEnd, calendarData]);

  function openCreate() {
    reset({ asset_id: "", purpose: "", start_time: "", end_time: "" });
    setDialogOpen(true);
  }
  function onSubmit(values: FormValues) {
    create.mutate(
      {
        asset_id: values.asset_id,
        purpose: values.purpose,
        start_time: new Date(values.start_time).toISOString(),
        end_time: new Date(values.end_time).toISOString(),
      },
      { onSuccess: () => setDialogOpen(false) },
    );
  }

  function openDetail(b: Booking) {
    setSelected(b);
    setDetailOpen(true);
  }

  const columns: Column<Booking>[] = [
    { key: "id", header: "ID", cell: (b) => <span className="font-mono text-xs">#{b.id}</span> },
    { key: "asset_id", header: "Asset", cell: (b) => <span className="font-mono text-sm">{b.asset_id}</span> },
    { key: "purpose", header: "Purpose", cell: (b) => <span className="line-clamp-1 max-w-xs">{b.purpose}</span> },
    { key: "requested_by", header: "Requested by", cell: (b) => b.requested_by },
    { key: "start_time", header: "From", cell: (b) => <span className="text-sm">{formatDateTime(b.start_time)}</span> },
    { key: "end_time", header: "To", cell: (b) => <span className="text-sm">{formatDateTime(b.end_time)}</span> },
    { key: "status", header: "Status", cell: (b) => <StatusBadge meta={BOOKING_STATUS[b.status]} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Resource Booking"
        description="Reserve assets and resources with an approval and check-in/out workflow."
        actions={
          <Button onClick={openCreate}>
            <Plus className="size-4" /> New Booking
          </Button>
        }
      />

      <Tabs defaultValue="list">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <TabsList>
            <TabsTrigger value="list">
              <List className="size-4" /> List
            </TabsTrigger>
            <TabsTrigger value="calendar">
              <CalendarDays className="size-4" /> Calendar
            </TabsTrigger>
          </TabsList>
          <Select value={status} onValueChange={(v) => { setStatus(v); setPage(1); }}>
            <SelectTrigger className="sm:w-52">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              {STATUS_KEYS.map((s) => (
                <SelectItem key={s} value={s}>
                  {BOOKING_STATUS[s].label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <TabsContent value="list">
          {isError ? (
            <ErrorState message={(refetch as never) && "Could not load bookings."} onRetry={() => refetch()} />
          ) : (
            <>
              <DataTable
                columns={columns}
                data={data?.items ?? []}
                rowKey={(b) => b.id}
                loading={isLoading}
                onRowClick={openDetail}
                columnToggle={false}
                empty={
                  <EmptyState
                    icon={CalendarClock}
                    title="No bookings"
                    description="Create a booking to reserve an asset."
                    action={
                      <Button onClick={openCreate}>
                        <Plus className="size-4" /> New Booking
                      </Button>
                    }
                  />
                }
              />
              <Pagination meta={data?.meta} onPageChange={setPage} />
            </>
          )}
        </TabsContent>

        <TabsContent value="calendar">
          <BookingCalendar bookings={calendarData?.items ?? []} onSelect={openDetail} />
        </TabsContent>
      </Tabs>

      {/* New booking dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New Booking</DialogTitle>
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
            <div className="grid grid-cols-2 gap-4">
              <Field label="Start" htmlFor="start_time" error={errors.start_time?.message} required>
                <Input id="start_time" type="datetime-local" {...register("start_time")} />
              </Field>
              <Field label="End" htmlFor="end_time" error={errors.end_time?.message} required>
                <Input id="end_time" type="datetime-local" {...register("end_time")} />
              </Field>
            </div>
            <Field label="Purpose" error={errors.purpose?.message} required>
              <Textarea {...register("purpose")} rows={3} placeholder="What is this booking for?" />
            </Field>

            {conflict && (
              <div className="flex items-start gap-2.5 rounded-lg border border-warning/30 bg-warning/10 p-3">
                <TriangleAlert className="mt-0.5 size-4 shrink-0 text-warning" />
                <div className="text-sm">
                  <p className="font-medium text-warning-foreground dark:text-warning">Scheduling conflict</p>
                  <p className="text-muted-foreground">
                    Booking #{conflict.id} ({BOOKING_STATUS[conflict.status].label}) overlaps this window:{" "}
                    {formatDateTime(conflict.start_time)} – {formatDateTime(conflict.end_time)}.
                  </p>
                </div>
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create booking
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <BookingDetailSheet booking={selected} open={detailOpen} onOpenChange={setDetailOpen} />
    </div>
  );
}
