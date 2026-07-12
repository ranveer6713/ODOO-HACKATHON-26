"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Download, FileBarChart, FileText, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { SearchInput } from "@/components/shared/search-input";
import { Pagination } from "@/components/shared/pagination";
import { EmptyState, ErrorState, TableSkeleton } from "@/components/shared/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useReport, useReportCatalog } from "@/lib/hooks/use-reports";
import { reportApi } from "@/lib/api/endpoints";
import { useDebounce } from "@/lib/hooks/use-debounce";
import { cn, downloadBlob } from "@/lib/utils";
import type { ReportType } from "@/lib/api/types";

const REPORTS: { type: ReportType; label: string }[] = [
  { type: "asset", label: "Assets" },
  { type: "booking", label: "Bookings" },
  { type: "maintenance", label: "Maintenance" },
  { type: "audit", label: "Audit" },
  { type: "notification", label: "Notifications" },
  { type: "department", label: "Department" },
];

export default function ReportsPage() {
  const [active, setActive] = useState<ReportType>("asset");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState<"csv" | "pdf" | null>(null);
  const debounced = useDebounce(search);

  const catalog = useReportCatalog();
  const params = useMemo(
    () => ({ search: debounced || undefined, page, page_size: 15 }),
    [debounced, page],
  );
  const report = useReport(active, params);

  const meta = catalog.data?.find((c) => c.report === active);

  async function handleExport(format: "csv" | "pdf") {
    setExporting(format);
    try {
      const blob = await reportApi.exportBlob(active, { format, search: debounced || undefined });
      downloadBlob(blob, `${active}-report.${format}`);
      toast.success(`${format.toUpperCase()} exported`);
    } catch (e) {
      toast.error("Export failed", { description: (e as Error).message });
    } finally {
      setExporting(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports"
        description="Generate, filter and export operational reports across every module."
        actions={
          <>
            <Button variant="outline" onClick={() => handleExport("csv")} disabled={!!exporting}>
              {exporting === "csv" ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => handleExport("pdf")} disabled={!!exporting}>
              {exporting === "pdf" ? <Loader2 className="size-4 animate-spin" /> : <FileText className="size-4" />}
              Export PDF
            </Button>
          </>
        }
      />

      {/* Report selector */}
      <div className="flex flex-wrap gap-2">
        {REPORTS.map((r) => (
          <button
            key={r.type}
            onClick={() => { setActive(r.type); setPage(1); setSearch(""); }}
            className={cn(
              "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
              active === r.type
                ? "border-primary bg-primary/5 text-primary"
                : "hover:bg-muted/60",
            )}
          >
            <FileBarChart className="size-4" />
            {r.label}
          </button>
        ))}
      </div>

      <Card className="p-4">
        <SearchInput
          value={search}
          onChange={(v) => { setSearch(v); setPage(1); }}
          placeholder={`Search ${active} report…`}
          className="max-w-sm"
        />
      </Card>

      {report.isError ? (
        <ErrorState onRetry={() => report.refetch()} message="Reports require asset-manager access." />
      ) : report.isLoading ? (
        <TableSkeleton cols={meta?.columns.length ?? 5} />
      ) : (report.data?.items.length ?? 0) === 0 ? (
        <EmptyState icon={FileBarChart} title="No data" description="This report has no rows for the current filters." />
      ) : (
        <>
          <Card className="overflow-hidden p-0">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  {report.data?.columns.map((col) => (
                    <TableHead key={col.key}>{col.label}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {report.data?.items.map((row, i) => (
                  <TableRow key={i}>
                    {report.data!.columns.map((col) => (
                      <TableCell key={col.key} className="text-sm">
                        {formatCell(row[col.key])}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
          <Pagination meta={report.data?.meta} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
