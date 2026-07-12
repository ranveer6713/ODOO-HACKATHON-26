"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Building2,
  CalendarClock,
  CircleDollarSign,
  Hash,
  MapPin,
  Package,
  Pencil,
  Tag,
  User,
  Wrench,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { QrCode } from "@/components/shared/qr-code";
import { AssetFormSheet } from "@/components/assets/asset-form-sheet";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/shared/states";
import { useAsset } from "@/lib/hooks/use-entities";
import { useLookups } from "@/lib/hooks/use-lookups";
import { ASSET_STATUS } from "@/lib/constants";
import { formatDate, formatDateTime, formatNumber, fromNow } from "@/lib/utils";

export default function AssetDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { data: asset, isLoading, isError, refetch } = useAsset(id);
  const lookups = useLookups();
  const [editOpen, setEditOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-64" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Skeleton className="h-80 lg:col-span-2" />
          <Skeleton className="h-80" />
        </div>
      </div>
    );
  }

  if (isError || !asset) {
    return (
      <ErrorState
        title="Asset not found"
        message="This asset may have been deleted or the id is invalid."
        onRetry={() => refetch()}
      />
    );
  }

  const timeline = buildTimeline(asset);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={() => router.push("/assets")}>
          <ArrowLeft className="size-4" /> Back to assets
        </Button>
      </div>

      <PageHeader
        title={asset.name}
        description={`${asset.manufacturer} ${asset.model} · ${asset.tag}`}
        actions={
          <>
            <StatusBadge meta={ASSET_STATUS[asset.status]} />
            <Button variant="outline" onClick={() => setEditOpen(true)}>
              <Pencil className="size-4" /> Edit
            </Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2">
                <Detail icon={Tag} label="Category" value={lookups.categoryName(asset.category_id)} />
                <Detail icon={Hash} label="Serial number" value={asset.serial_number} mono />
                <Detail icon={Building2} label="Department" value={lookups.departmentName(asset.department_id)} />
                <Detail icon={User} label="Assigned to" value={lookups.employeeName(asset.assigned_to)} />
                <Detail icon={MapPin} label="Location" value={asset.location || "—"} />
                <Detail icon={CircleDollarSign} label="Purchase cost" value={`$${formatNumber(asset.purchase_cost)}`} />
                <Detail icon={CalendarClock} label="Purchased" value={formatDate(asset.purchase_date)} />
                <Detail icon={Package} label="Asset ID" value={asset.id} mono />
              </dl>
              {asset.notes && (
                <div className="mt-6 rounded-lg bg-muted/50 p-4">
                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Notes</p>
                  <p className="mt-1 text-sm">{asset.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Lifecycle & History</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="timeline">
                <TabsList>
                  <TabsTrigger value="timeline">Timeline</TabsTrigger>
                  <TabsTrigger value="related">Related Activity</TabsTrigger>
                </TabsList>
                <TabsContent value="timeline">
                  <ol className="relative space-y-6 border-l pl-6">
                    {timeline.map((event, i) => (
                      <li key={i} className="relative">
                        <span className="absolute -left-[27px] flex size-5 items-center justify-center rounded-full bg-background ring-2 ring-border">
                          <span className="size-2 rounded-full bg-primary" />
                        </span>
                        <p className="text-sm font-medium">{event.title}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatDateTime(event.at)} · {fromNow(event.at)}
                        </p>
                        {event.detail && (
                          <p className="mt-0.5 text-sm text-muted-foreground">{event.detail}</p>
                        )}
                      </li>
                    ))}
                  </ol>
                </TabsContent>
                <TabsContent value="related">
                  <div className="flex flex-col gap-2">
                    <Button variant="outline" asChild className="justify-start">
                      <Link href={`/booking?asset=${asset.id}`}>
                        <CalendarClock className="size-4" /> View bookings for this asset
                      </Link>
                    </Button>
                    <Button variant="outline" asChild className="justify-start">
                      <Link href={`/maintenance?asset=${asset.id}`}>
                        <Wrench className="size-4" /> View maintenance history
                      </Link>
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardContent className="flex flex-col items-center gap-4 p-6">
              {asset.image_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={asset.image_url}
                  alt={asset.name}
                  className="h-40 w-full rounded-lg object-cover"
                />
              ) : (
                <div className="flex h-40 w-full items-center justify-center rounded-lg bg-muted text-muted-foreground">
                  <Package className="size-10" />
                </div>
              )}
              <QrCode value={asset.tag} size={140} />
              <p className="font-mono text-sm text-muted-foreground">{asset.tag}</p>
              <Button variant="outline" size="sm" className="w-full" onClick={() => window.print()}>
                Print asset label
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Depreciation</CardTitle>
            </CardHeader>
            <CardContent>
              <DepreciationBar
                cost={asset.purchase_cost}
                purchaseDate={asset.purchase_date}
                years={lookups.categories.get(asset.category_id)?.depreciation_years ?? 5}
              />
            </CardContent>
          </Card>
        </div>
      </div>

      <AssetFormSheet open={editOpen} onOpenChange={setEditOpen} asset={asset} />
    </div>
  );
}

function Detail({
  icon: Icon,
  label,
  value,
  mono,
}: {
  icon: typeof Tag;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <dt className="text-xs text-muted-foreground">{label}</dt>
        <dd className={mono ? "font-mono text-sm" : "text-sm font-medium"}>{value}</dd>
      </div>
    </div>
  );
}

function DepreciationBar({
  cost,
  purchaseDate,
  years,
}: {
  cost: number;
  purchaseDate: string;
  years: number;
}) {
  const ageMs = Date.now() - new Date(purchaseDate).getTime();
  const ageYears = Math.max(0, ageMs / (1000 * 60 * 60 * 24 * 365));
  const depreciated = Math.min(1, ageYears / years);
  const bookValue = Math.max(0, cost * (1 - depreciated));
  return (
    <div className="space-y-3">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs text-muted-foreground">Current book value</p>
          <p className="text-2xl font-semibold">${formatNumber(Math.round(bookValue))}</p>
        </div>
        <p className="text-sm text-muted-foreground">{Math.round(depreciated * 100)}% depreciated</p>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${depreciated * 100}%` }} />
      </div>
      <p className="text-xs text-muted-foreground">
        Straight-line over {years} years · {ageYears.toFixed(1)} years in service
      </p>
    </div>
  );
}

function buildTimeline(asset: {
  created_at: string;
  updated_at: string;
  status: string;
  assigned_to: string | null;
  purchase_date: string;
}) {
  const events: { title: string; at: string; detail?: string }[] = [
    { title: "Asset acquired", at: asset.purchase_date, detail: "Added to the procurement ledger." },
    { title: "Registered in AssetFlow", at: asset.created_at },
  ];
  if (asset.assigned_to) {
    events.push({ title: "Allocated to employee", at: asset.updated_at, detail: `Assigned to ${asset.assigned_to}.` });
  }
  events.push({
    title: `Status: ${ASSET_STATUS[asset.status as keyof typeof ASSET_STATUS]?.label ?? asset.status}`,
    at: asset.updated_at,
    detail: "Last recorded status change.",
  });
  return events.sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());
}
