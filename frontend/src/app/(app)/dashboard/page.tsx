"use client";

import Link from "next/link";
import {
  Activity,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Package,
  PackageCheck,
  TriangleAlert,
  Wrench,
} from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { StatCard } from "@/components/shared/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  ChartCard,
  ColumnChart,
  DonutChart,
  MultiColumnChart,
  TrendChart,
} from "@/components/shared/charts";
import { CardsSkeleton, ChartSkeleton, ErrorState } from "@/components/shared/states";
import {
  useDashboardAnalytics,
  useDashboardOverview,
} from "@/lib/hooks/use-dashboard";
import { SEVERITY } from "@/lib/constants";
import { fromNow, titleCase } from "@/lib/utils";

export default function DashboardPage() {
  const overview = useDashboardOverview();
  const analytics = useDashboardAnalytics();

  const kpis = overview.data?.kpis;
  const bookings = overview.data?.bookings;
  const maintenance = overview.data?.maintenance;
  const audit = overview.data?.audit;
  const notifications = overview.data?.notifications;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Operational overview of assets, bookings, maintenance and audits across your organization."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link href="/reports">View reports</Link>
            </Button>
            <Button asChild>
              <Link href="/assets">
                <Package className="size-4" /> Register asset
              </Link>
            </Button>
          </>
        }
      />

      {/* KPI cards */}
      {overview.isLoading ? (
        <CardsSkeleton count={4} />
      ) : overview.isError ? (
        <ErrorState message={(overview.error as Error)?.message} onRetry={() => overview.refetch()} />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Total Assets"
            value={kpis?.total ?? 0}
            icon={Package}
            tone="primary"
            hint={`${kpis?.available ?? 0} available`}
          />
          <StatCard
            label="Allocated"
            value={kpis?.allocated ?? 0}
            icon={PackageCheck}
            tone="info"
            hint={`${kpis?.reserved ?? 0} reserved`}
          />
          <StatCard
            label="Under Maintenance"
            value={kpis?.under_maintenance ?? 0}
            icon={Wrench}
            tone="warning"
            hint={`${maintenance?.pending ?? 0} pending requests`}
          />
          <StatCard
            label="Critical Alerts"
            value={notifications?.critical_alerts ?? 0}
            icon={TriangleAlert}
            tone="danger"
            hint={`${notifications?.unread ?? 0} unread notifications`}
          />
        </div>
      )}

      {/* Secondary summary row */}
      {!overview.isLoading && !overview.isError && (
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <MiniStat icon={CalendarClock} label="Active Bookings" value={bookings?.active ?? 0} sub={`${bookings?.upcoming ?? 0} upcoming`} href="/booking" />
          <MiniStat icon={Wrench} label="In Progress" value={maintenance?.in_progress ?? 0} sub={`${maintenance?.resolved ?? 0} resolved`} href="/maintenance" />
          <MiniStat icon={ClipboardCheck} label="Active Audits" value={audit?.active_cycles ?? 0} sub={`${audit?.pending_items ?? 0} pending items`} href="/audit" />
          <MiniStat icon={TriangleAlert} label="Discrepancies" value={(audit?.missing_assets ?? 0) + (audit?.damaged_assets ?? 0)} sub={`${audit?.missing_assets ?? 0} missing · ${audit?.damaged_assets ?? 0} damaged`} href="/audit" />
        </div>
      )}

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {analytics.data ? (
          <>
            <ChartCard title="Asset Distribution" description="By operational status">
              <DonutChart data={analytics.data.asset_distribution.points} />
            </ChartCard>
            <ChartCard
              title="Department Allocation"
              description="Assets assigned per department"
              className="lg:col-span-2"
            >
              <MultiColumnChart data={analytics.data.department_distribution.points} />
            </ChartCard>
          </>
        ) : analytics.isError ? (
          <ErrorState
            className="lg:col-span-3"
            message={(analytics.error as Error)?.message}
            onRetry={() => analytics.refetch()}
          />
        ) : (
          <>
            <ChartSkeleton />
            <ChartSkeleton className="lg:col-span-2" />
          </>
        )}
      </div>

      {/* Charts row 2 — trends */}
      {analytics.data && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <ChartCard title="Booking Trend" description="Bookings over time">
            <TrendChart data={analytics.data.booking_trend.points} name="Bookings" />
          </ChartCard>
          <ChartCard title="Maintenance Trend" description="Requests raised over time">
            <ColumnChart
              data={analytics.data.maintenance_trend.points}
              name="Requests"
              color="hsl(38 92% 52%)"
            />
          </ChartCard>
          <ChartCard title="Audit Trend" description="Items verified over time">
            <TrendChart
              data={analytics.data.audit_trend.points}
              name="Verified"
              color="hsl(152 58% 45%)"
            />
          </ChartCard>
        </div>
      )}

      {/* Activity + quick actions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="size-4 text-muted-foreground" /> Recent Activity
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/activity">
                View all <ArrowRight className="size-3.5" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {overview.isLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="h-12 animate-pulse rounded-lg bg-muted" />
                ))}
              </div>
            ) : (overview.data?.recent_activity.length ?? 0) === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">No recent activity.</p>
            ) : (
              <ul className="space-y-1">
                {overview.data?.recent_activity.slice(0, 7).map((item) => (
                  <li
                    key={item.id}
                    className="flex items-start gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-muted/50"
                  >
                    <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-xs font-semibold text-muted-foreground">
                      {item.user.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm">
                        <span className="font-medium">{item.user}</span>{" "}
                        <span className="text-muted-foreground">
                          {titleCase(item.action)} {item.entity_type.toLowerCase()}
                        </span>{" "}
                        <span className="font-mono text-xs text-muted-foreground">
                          #{item.entity_id}
                        </span>
                      </p>
                      {item.description && (
                        <p className="truncate text-xs text-muted-foreground">{item.description}</p>
                      )}
                    </div>
                    <div className="flex shrink-0 flex-col items-end gap-1">
                      {item.severity !== "info" && (
                        <StatusBadge meta={SEVERITY[item.severity]} dot={false} />
                      )}
                      <span className="text-[11px] text-muted-foreground">
                        {fromNow(item.timestamp)}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="size-4 text-muted-foreground" /> Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {QUICK_LINKS.map((q) => (
              <Link
                key={q.href}
                href={q.href}
                className="flex items-center gap-3 rounded-lg border p-3 transition-colors hover:border-primary hover:bg-primary/5"
              >
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <q.icon className="size-4.5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{q.label}</p>
                  <p className="truncate text-xs text-muted-foreground">{q.description}</p>
                </div>
                <ArrowRight className="size-4 text-muted-foreground" />
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MiniStat({
  icon: Icon,
  label,
  value,
  sub,
  href,
}: {
  icon: typeof Package;
  label: string;
  value: number;
  sub: string;
  href: string;
}) {
  return (
    <Link href={href}>
      <Card className="p-4 transition-colors hover:border-primary/40">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Icon className="size-4" />
          <span className="text-xs font-medium">{label}</span>
        </div>
        <p className="mt-2 text-2xl font-semibold">{value}</p>
        <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>
      </Card>
    </Link>
  );
}

const QUICK_LINKS = [
  { label: "New Booking", description: "Reserve an asset or resource", href: "/booking", icon: CalendarClock },
  { label: "Raise Maintenance", description: "Report an asset issue", href: "/maintenance", icon: Wrench },
  { label: "Start Audit Cycle", description: "Verify physical assets", href: "/audit", icon: ClipboardCheck },
  { label: "Register Asset", description: "Add a new asset to the estate", href: "/assets", icon: Package },
];
