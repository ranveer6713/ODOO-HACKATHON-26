"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { maintenanceApi } from "@/lib/api/endpoints";
import type { MaintenanceCreate, MaintenanceUpdate } from "@/lib/api/types";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

export function useMaintenanceList(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.maintenance.list(params),
    queryFn: () => maintenanceApi.list(params as never),
  });
}

export function useMaintenance(id: number, enabled = true) {
  return useQuery({
    queryKey: qk.maintenance.detail(id),
    queryFn: () => maintenanceApi.get(id),
    enabled: enabled && Number.isFinite(id),
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["maintenance"] });
}

export function useCreateMaintenance() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: MaintenanceCreate) => maintenanceApi.create(body),
    onSuccess: () => {
      toast.success("Request submitted", { description: "Maintenance request is pending review." });
      invalidate();
    },
    onError: (e) => toastError(e, "Could not submit request"),
  });
}

export function useUpdateMaintenance() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: MaintenanceUpdate }) =>
      maintenanceApi.update(id, body),
    onSuccess: () => {
      toast.success("Request updated");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not update request"),
  });
}

export function useMaintenanceAction() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: async ({
      id,
      action,
      value,
    }: {
      id: number;
      action: "approve" | "reject" | "assign" | "start" | "resolve" | "delete";
      value?: string;
    }) => {
      switch (action) {
        case "approve":
          return maintenanceApi.approve(id);
        case "reject":
          return maintenanceApi.reject(id, value ?? "");
        case "assign":
          return maintenanceApi.assign(id, value ?? "");
        case "start":
          return maintenanceApi.start(id);
        case "resolve":
          return maintenanceApi.resolve(id, value ?? "");
        case "delete":
          return maintenanceApi.remove(id);
      }
    },
    onSuccess: (_data, vars) => {
      const labels: Record<string, string> = {
        approve: "Request approved",
        reject: "Request rejected",
        assign: "Technician assigned",
        start: "Work started",
        resolve: "Request resolved",
        delete: "Request deleted",
      };
      toast.success(labels[vars.action]);
      invalidate();
    },
    onError: (e) => toastError(e, "Action failed"),
  });
}
