"use client";

import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  ArrowLeft,
  CheckCircle2,
  CircleHelp,
  Lock,
  Play,
  Plus,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { StatusBadge } from "@/components/shared/status-badge";
import { EmptyState, ErrorState } from "@/components/shared/states";
import { Field } from "@/components/shared/form-field";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  useAddAuditItem,
  useAuditCycle,
  useAuditItems,
  useAuditReport,
  useCycleAction,
  useVerifyItem,
} from "@/lib/hooks/use-audit";
import { useAssets, useEmployees } from "@/lib/hooks/use-entities";
import { AUDIT_CYCLE_STATUS, AUDIT_ITEM_STATUS } from "@/lib/constants";
import { formatDate, formatDateTime } from "@/lib/utils";
import type { AuditItem, AuditItemStatus } from "@/lib/api/types";

const enrollSchema = z.object({
  asset_id: z.string().min(1, "Select an asset"),
  auditor_id: z.string().min(1, "Select an auditor"),
});
type EnrollValues = z.infer<typeof enrollSchema>;

export default function AuditCycleDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const cycleId = Number(id);
  const router = useRouter();

  const cycle = useAuditCycle(cycleId);
  const items = useAuditItems(cycleId);
  const report = useAuditReport(cycleId);
  const cycleAction = useCycleAction();
  const addItem = useAddAuditItem();
  const verify = useVerifyItem();
  const { data: assets } = useAssets({ page_size: 200 });
  const { data: employees } = useEmployees({ page_size: 200 });

  const [enrollOpen, setEnrollOpen] = useState(false);
  const [verifying, setVerifying] = useState<AuditItem | null>(null);
  const [verdict, setVerdict] = useState<AuditItemStatus>("verified");
  const [remarks, setRemarks] = useState("");

  const {
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EnrollValues>({ resolver: zodResolver(enrollSchema) });

  if (cycle.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
        <Skeleton className="h-80" />
      </div>
    );
  }
  if (cycle.isError || !cycle.data) {
    return <ErrorState title="Cycle not found" onRetry={() => cycle.refetch()} />;
  }

  const c = cycle.data;
  const summary = report.data?.summary;
  const locked = c.status === "closed";

  const auditors = employees?.items ?? [];

  function onEnroll(values: EnrollValues) {
    addItem.mutate(
      { audit_cycle_id: cycleId, asset_id: values.asset_id, auditor_id: values.auditor_id },
      { onSuccess: () => { reset(); setEnrollOpen(false); } },
    );
  }
  function submitVerdict() {
    if (!verifying) return;
    verify.mutate(
      { itemId: verifying.id, body: { status: verdict, remarks: remarks || null } },
      { onSuccess: () => { setVerifying(null); setRemarks(""); } },
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => router.push("/audit")}>
          <ArrowLeft className="size-4" /> Back to cycles
        </Button>
      </div>

      <PageHeader
        title={c.name}
        description={`${formatDate(c.start_date)} → ${formatDate(c.end_date)} · Created by ${c.created_by}`}
        actions={
          <>
            <StatusBadge meta={AUDIT_CYCLE_STATUS[c.status]} />
            {c.status === "created" && (
              <Button loading={cycleAction.isPending} onClick={() => cycleAction.mutate({ id: cycleId, action: "start" })}>
                <Play className="size-4" /> Start cycle
              </Button>
            )}
            {c.status === "active" && (
              <Button variant="outline" onClick={() => cycleAction.mutate({ id: cycleId, action: "close" })}>
                <Lock className="size-4" /> Close cycle
              </Button>
            )}
          </>
        }
      />

      {/* Summary */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Verified" value={summary?.verified ?? 0} icon={CheckCircle2} tone="success" />
        <StatCard label="Missing" value={summary?.missing ?? 0} icon={ShieldAlert} tone="danger" />
        <StatCard label="Damaged" value={summary?.damaged ?? 0} icon={TriangleAlert} tone="warning" />
        <StatCard label="Pending" value={summary?.pending ?? 0} icon={CircleHelp} tone="neutral" />
      </div>

      <Tabs defaultValue="items">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="items">Audit Items</TabsTrigger>
            <TabsTrigger value="report">Discrepancy Report</TabsTrigger>
          </TabsList>
          {c.status === "active" && (
            <Button size="sm" onClick={() => { reset(); setEnrollOpen(true); }}>
              <Plus className="size-4" /> Enroll Asset
            </Button>
          )}
        </div>

        <TabsContent value="items">
          <Card className="overflow-hidden p-0">
            {items.isLoading ? (
              <div className="p-6">
                <Skeleton className="h-40 w-full" />
              </div>
            ) : (items.data?.length ?? 0) === 0 ? (
              <EmptyState
                icon={CircleHelp}
                title="No assets enrolled"
                description={
                  c.status === "created"
                    ? "Start the cycle, then enroll assets for verification."
                    : "Enroll assets to begin verification."
                }
              />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Asset</TableHead>
                    <TableHead>Auditor</TableHead>
                    <TableHead>Verdict</TableHead>
                    <TableHead>Verified</TableHead>
                    <TableHead>Remarks</TableHead>
                    <TableHead className="w-24" />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.data?.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-mono text-sm">{item.asset_id}</TableCell>
                      <TableCell>{item.auditor_id}</TableCell>
                      <TableCell>
                        {item.status ? (
                          <StatusBadge meta={AUDIT_ITEM_STATUS[item.status]} />
                        ) : (
                          <StatusBadge tone="neutral" label="Pending" />
                        )}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {item.verified_at ? formatDateTime(item.verified_at) : "—"}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate text-sm text-muted-foreground">
                        {item.remarks ?? "—"}
                      </TableCell>
                      <TableCell>
                        {!item.status && !locked && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setVerifying(item);
                              setVerdict("verified");
                              setRemarks("");
                            }}
                          >
                            Verify
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="report">
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            <DiscrepancyList
              title="Missing Assets"
              tone="danger"
              icon={ShieldAlert}
              items={report.data?.missing_assets ?? []}
            />
            <DiscrepancyList
              title="Damaged Assets"
              tone="warning"
              icon={TriangleAlert}
              items={report.data?.damaged_assets ?? []}
            />
            <DiscrepancyList
              title="Verified Assets"
              tone="success"
              icon={CheckCircle2}
              items={report.data?.verified_assets ?? []}
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* Enroll dialog */}
      <Dialog open={enrollOpen} onOpenChange={setEnrollOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enroll Asset in Cycle</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit(onEnroll)} className="space-y-4">
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
            <Field label="Auditor" error={errors.auditor_id?.message} required>
              <Select value={watch("auditor_id")} onValueChange={(v) => setValue("auditor_id", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Assign an auditor" />
                </SelectTrigger>
                <SelectContent>
                  {auditors.map((e) => (
                    <SelectItem key={e.id} value={e.id}>
                      {e.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEnrollOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={addItem.isPending}>
                Enroll
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Verify dialog */}
      <Dialog open={!!verifying} onOpenChange={(o) => !o && setVerifying(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Verify Asset {verifying?.asset_id}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(AUDIT_ITEM_STATUS) as AuditItemStatus[]).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setVerdict(s)}
                  className={`rounded-lg border p-3 text-center text-sm font-medium transition-colors ${
                    verdict === s ? "border-primary bg-primary/5 text-primary" : "hover:bg-muted/50"
                  }`}
                >
                  {AUDIT_ITEM_STATUS[s].label}
                </button>
              ))}
            </div>
            <Field label="Remarks" hint="Optional context for this verdict.">
              <Textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} rows={3} />
            </Field>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setVerifying(null)}>
              Cancel
            </Button>
            <Button onClick={submitVerdict} loading={verify.isPending}>
              Record verdict
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DiscrepancyList({
  title,
  tone,
  icon: Icon,
  items,
}: {
  title: string;
  tone: "danger" | "warning" | "success";
  icon: typeof ShieldAlert;
  items: AuditItem[];
}) {
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-2 text-base">
          <Icon
            className={`size-4 ${
              tone === "danger" ? "text-destructive" : tone === "warning" ? "text-warning" : "text-success"
            }`}
          />
          {title}
        </CardTitle>
        <span className="rounded-full bg-muted px-2 text-xs font-semibold">{items.length}</span>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">None</p>
        ) : (
          <ul className="space-y-2">
            {items.map((item) => (
              <li key={item.id} className="rounded-lg border p-2.5">
                <p className="font-mono text-sm">{item.asset_id}</p>
                {item.remarks && <p className="text-xs text-muted-foreground">{item.remarks}</p>}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
