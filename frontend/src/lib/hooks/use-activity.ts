"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { activityLogApi } from "@/lib/api/endpoints";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

export function useActivityLogs(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.activity.list(params),
    queryFn: () => activityLogApi.list(params as never),
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["activity"] });
}

export function useActivityAction() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({
      id,
      action,
      reason,
    }: {
      id: number;
      action: "flag" | "acknowledge";
      reason?: string;
    }) =>
      action === "flag"
        ? activityLogApi.flag(id, reason ?? "")
        : activityLogApi.acknowledge(id),
    onSuccess: (_d, vars) => {
      toast.success(vars.action === "flag" ? "Entry flagged" : "Entry acknowledged");
      invalidate();
    },
    onError: (e) => toastError(e, "Action failed"),
  });
}
