"use client";

import { useState } from "react";
import {
  CalendarClock,
  Check,
  LogIn,
  LogOut,
  Package,
  User,
  X,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { useBookingAction } from "@/lib/hooks/use-bookings";
import { BOOKING_STATUS } from "@/lib/constants";
import { formatDateTime, fromNow } from "@/lib/utils";
import type { Booking } from "@/lib/api/types";

export function BookingDetailSheet({
  booking,
  open,
  onOpenChange,
}: {
  booking: Booking | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const action = useBookingAction();
  const [confirm, setConfirm] = useState<null | "reject" | "cancel">(null);

  if (!booking) return null;

  const timeline = [
    { label: "Requested", at: booking.created_at, done: true },
    { label: "Approved", at: booking.approved_at, done: !!booking.approved_at },
    { label: "Checked out", at: booking.checked_out_at, done: !!booking.checked_out_at },
    { label: "Checked in", at: booking.checked_in_at, done: !!booking.checked_in_at },
  ];

  const run = (a: Parameters<typeof action.mutate>[0]["action"], reason?: string) =>
    action.mutate({ id: booking.id, action: a, reason }, { onSuccess: () => setConfirm(null) });

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-full sm:max-w-md">
          <SheetHeader>
            <div className="flex items-center justify-between">
              <SheetTitle>Booking #{booking.id}</SheetTitle>
              <StatusBadge meta={BOOKING_STATUS[booking.status]} />
            </div>
            <SheetDescription>{booking.purpose}</SheetDescription>
          </SheetHeader>

          <div className="flex-1 space-y-6 overflow-y-auto p-6">
            <div className="grid grid-cols-1 gap-4">
              <Row icon={Package} label="Asset" value={booking.asset_id} mono />
              <Row icon={User} label="Requested by" value={booking.requested_by} />
              <Row icon={CalendarClock} label="From" value={formatDateTime(booking.start_time)} />
              <Row icon={CalendarClock} label="To" value={formatDateTime(booking.end_time)} />
              {booking.approved_by && <Row icon={Check} label="Approved by" value={booking.approved_by} />}
            </div>

            {booking.rejection_reason && (
              <Callout tone="danger" title="Rejection reason" body={booking.rejection_reason} />
            )}
            {booking.cancellation_reason && (
              <Callout tone="neutral" title="Cancellation reason" body={booking.cancellation_reason} />
            )}

            <div>
              <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Workflow
              </p>
              <ol className="relative space-y-5 border-l pl-6">
                {timeline.map((s) => (
                  <li key={s.label} className="relative">
                    <span
                      className={`absolute -left-[27px] flex size-5 items-center justify-center rounded-full ring-2 ring-border ${
                        s.done ? "bg-primary" : "bg-background"
                      }`}
                    >
                      {s.done && <Check className="size-3 text-primary-foreground" />}
                    </span>
                    <p className={`text-sm ${s.done ? "font-medium" : "text-muted-foreground"}`}>
                      {s.label}
                    </p>
                    {s.at && (
                      <p className="text-xs text-muted-foreground">
                        {formatDateTime(s.at)} · {fromNow(s.at)}
                      </p>
                    )}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <SheetFooter className="flex-wrap">
            {booking.status === "pending" && (
              <>
                <Button variant="outline" className="text-destructive" onClick={() => setConfirm("reject")}>
                  <X className="size-4" /> Reject
                </Button>
                <Button onClick={() => run("approve")} loading={action.isPending}>
                  <Check className="size-4" /> Approve
                </Button>
              </>
            )}
            {booking.status === "approved" && (
              <>
                <Button variant="outline" onClick={() => setConfirm("cancel")}>
                  Cancel
                </Button>
                <Button onClick={() => run("checkout")} loading={action.isPending}>
                  <LogOut className="size-4" /> Check out
                </Button>
              </>
            )}
            {booking.status === "checked_out" && (
              <Button onClick={() => run("checkin")} loading={action.isPending}>
                <LogIn className="size-4" /> Check in
              </Button>
            )}
            {(booking.status === "checked_in" ||
              booking.status === "rejected" ||
              booking.status === "cancelled") && (
              <p className="text-sm text-muted-foreground">This booking is closed.</p>
            )}
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <ConfirmDialog
        open={confirm === "reject"}
        onOpenChange={(o) => !o && setConfirm(null)}
        title="Reject booking?"
        description="Provide a reason. The requester will be notified."
        confirmLabel="Reject booking"
        destructive
        reasonLabel="Rejection reason"
        reasonRequired
        loading={action.isPending}
        onConfirm={(reason) => run("reject", reason)}
      />
      <ConfirmDialog
        open={confirm === "cancel"}
        onOpenChange={(o) => !o && setConfirm(null)}
        title="Cancel booking?"
        description="You can optionally provide a reason."
        confirmLabel="Cancel booking"
        destructive
        reasonLabel="Reason (optional)"
        loading={action.isPending}
        onConfirm={(reason) => run("cancel", reason)}
      />
    </>
  );
}

function Row({
  icon: Icon,
  label,
  value,
  mono,
}: {
  icon: typeof Package;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className={mono ? "font-mono text-sm" : "text-sm font-medium"}>{value}</p>
      </div>
    </div>
  );
}

function Callout({ tone, title, body }: { tone: "danger" | "neutral"; title: string; body: string }) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        tone === "danger" ? "border-destructive/30 bg-destructive/5" : "bg-muted/50"
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <p className="mt-1 text-sm">{body}</p>
    </div>
  );
}
