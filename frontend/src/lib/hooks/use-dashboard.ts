"use client";

import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "@/lib/api/endpoints";
import { qk } from "./keys";

export function useDashboardOverview() {
  return useQuery({
    queryKey: qk.dashboard.overview,
    queryFn: dashboardApi.overview,
  });
}

export function useDashboardAnalytics() {
  return useQuery({
    queryKey: qk.dashboard.analytics,
    queryFn: dashboardApi.analytics,
  });
}

export function useDashboardActivity(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.dashboard.activity(params),
    queryFn: () => dashboardApi.activity(params as never),
  });
}
