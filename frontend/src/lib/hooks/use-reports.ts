"use client";

import { useQuery } from "@tanstack/react-query";
import { reportApi } from "@/lib/api/endpoints";
import type { ReportType } from "@/lib/api/types";
import { qk } from "./keys";

export function useReportCatalog() {
  return useQuery({
    queryKey: qk.reports.catalog,
    queryFn: reportApi.catalog,
    staleTime: 5 * 60_000,
  });
}

export function useReport(type: ReportType, params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.reports.run(type, params),
    queryFn: () => reportApi.run(type, params as never),
  });
}
