"use client";

import { useState } from "react";
import {
  Check,
  Package,
  Play,
  User,
  Wrench,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/shared/status-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { Field } from "@/components/shared/form-field";
import { Label } from "@/components/ui/label";
import { useMaintenanceAction } from "@/lib/hooks/use-maintenance";
import { useEmployees } from "@/lib/hooks/use-entities";
import { MAINTENANCE_PRIORITY, MAINTENANCE_STATUS } from "@/lib/constants";
import { formatDateTime, fromNow } from "@/lib/utils";
import type { Maintenance } from "@/lib/api/types";

export function MaintenanceDetailSheet({
  request,
  open,
  onOpenChange,
}: {
  request: Maintenance | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const action = useMaintenanceAction();
  const { data: employees } = useEmployees({ page_size: 200 });
  const [confirm, setConfirm] = useState<null | "reject" | "resolve">(null);
  const [technician, setTechnician] = useState("");

  if (!request) return null;

  const technicians = employees?.items.filter((e) => e.role === "technician") ?? [];

  const run = (a: Parameters<typeof action.mutate>[0]["action"], value?: string) =>
    action.mutate({ id: request.id, action: a, value }, { onSuccess: () => setConfirm(null) });

  const timeline = [
    { label: "Raised", at: request.created_at, done: true },
    { label: "Approved", at: request.approved_at, done: !!request.approved_at },
    { label: "Technician assigned", at: request.assigned_at, done: !!request.assigned_at },
    { label: "Work started", at: request.started_at, done: !!request.started_at },
    { label: "Resolved", at: request.resolved_at, done: !!request.resolved_at },
  ];

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent side="right" className="w-full sm:max-w-md">
          <SheetHeader>
            <div className="flex items-center justify-between">
              <SheetTitle>Request #{request.id}</SheetTitle>
              <div className="flex gap-1.5">
                <StatusBadge meta={MAINTENANCE_PRIORITY[request.priority]} dot={false} />
                <StatusBadge meta={MAINTENANCE_STATUS[request.status]} />
              </div>
            </div>
            <SheetDescription>{request.issue_description}</SheetDescription>
          </SheetHeader>

          <div className="flex-1 space-y-6 overflow-y-auto p-6">
            <div className="grid gap-4">
              <Row icon={Package} label="Asset" value={request.asset_id} mono />
              <Row icon={User} label="Raised by" value={request.raised_by} />
              {request.technician_id && (
                <Row icon={Wrench} label="Technician" value={request.technician_id} />
              )}
            </div>

            {request.photo_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={request.photo_url} alt="Issue" className="w-full rounded-lg object-cover" />
            )}

            {request.rejection_reason && (
              <Callout tone="danger" title="Rejection reason" body={request.rejection_reason} />
            )}
            {request.resolution_notes && (
              <Callout tone="success" title="Resolution notes" body={request.resolution_notes} />
            )}

            {request.status === "approved" && (
              <div className="space-y-1.5">
                <Label>Assign technician</Label>
                <div className="flex gap-2">
                  <Select value={technician} onValueChange={setTechnician}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select technician" />
                    </SelectTrigger>
                    <SelectContent>
                      {technicians.map((t) => (
                        <SelectItem key={t.id} value={t.id}>
                          {t.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    disabled={!technician}
                    loading={action.isPending}
                    onClick={() => run("assign", technician)}
                  >
                    Assign
                  </Button>
                </div>
              </div>
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
            {request.status === "pending" && (
              <>
                <Button variant="outline" className="text-destructive" onClick={() => setConfirm("reject")}>
                  <X className="size-4" /> Reject
                </Button>
                <Button onClick={() => run("approve")} loading={action.isPending}>
                  <Check className="size-4" /> Approve
                </Button>
              </>
            )}
            {request.status === "technician_assigned" && (
              <Button onClick={() => run("start")} loading={action.isPending}>
                <Play className="size-4" /> Start work
              </Button>
            )}
            {request.status === "in_progress" && (
              <Button onClick={() => setConfirm("resolve")} loading={action.isPending}>
                <Check className="size-4" /> Mark resolved
              </Button>
            )}
            {(request.status === "resolved" || request.status === "rejected") && (
              <p className="text-sm text-muted-foreground">This request is closed.</p>
            )}
          </SheetFooter>
        </SheetContent>
      </Sheet>

      <ConfirmDialog
        open={confirm === "reject"}
        onOpenChange={(o) => !o && setConfirm(null)}
        title="Reject request?"
        confirmLabel="Reject"
        destructive
        reasonLabel="Rejection reason"
        reasonRequired
        loading={action.isPending}
        onConfirm={(reason) => run("reject", reason)}
      />
      <ConfirmDialog
        open={confirm === "resolve"}
        onOpenChange={(o) => !o && setConfirm(null)}
        title="Resolve request?"
        description="Record what was done to resolve the issue."
        confirmLabel="Mark resolved"
        reasonLabel="Resolution notes"
        reasonRequired
        loading={action.isPending}
        onConfirm={(notes) => run("resolve", notes)}
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

function Callout({ tone, title, body }: { tone: "danger" | "success"; title: string; body: string }) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        tone === "danger" ? "border-destructive/30 bg-destructive/5" : "border-success/30 bg-success/5"
      }`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{title}</p>
      <p className="mt-1 text-sm">{body}</p>
    </div>
  );
}
