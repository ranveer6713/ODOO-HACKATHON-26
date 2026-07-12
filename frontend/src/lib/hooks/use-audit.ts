"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { auditApi } from "@/lib/api/endpoints";
import type {
  AuditCycleCreate,
  AuditItemCreate,
  AuditItemVerify,
} from "@/lib/api/types";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

export function useAuditCycles(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.audit.cycles(params),
    queryFn: () => auditApi.listCycles(params as never),
  });
}

export function useAuditCycle(id: number, enabled = true) {
  return useQuery({
    queryKey: qk.audit.cycle(id),
    queryFn: () => auditApi.getCycle(id),
    enabled: enabled && Number.isFinite(id),
  });
}

export function useAuditItems(cycleId: number, enabled = true) {
  return useQuery({
    queryKey: qk.audit.items(cycleId),
    queryFn: () => auditApi.listItems(cycleId),
    enabled: enabled && Number.isFinite(cycleId),
  });
}

export function useAuditReport(cycleId: number, enabled = true) {
  return useQuery({
    queryKey: qk.audit.report(cycleId),
    queryFn: () => auditApi.report(cycleId),
    enabled: enabled && Number.isFinite(cycleId),
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["audit"] });
}

export function useCreateCycle() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: AuditCycleCreate) => auditApi.createCycle(body),
    onSuccess: () => {
      toast.success("Audit cycle created");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not create cycle"),
  });
}

export function useCycleAction() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: "start" | "close" }) =>
      action === "start" ? auditApi.startCycle(id) : auditApi.closeCycle(id),
    onSuccess: (_d, vars) => {
      toast.success(vars.action === "start" ? "Cycle activated" : "Cycle closed");
      invalidate();
    },
    onError: (e) => toastError(e, "Action failed"),
  });
}

export function useAddAuditItem() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (body: AuditItemCreate) => auditApi.addItem(body),
    onSuccess: () => {
      toast.success("Asset enrolled in cycle");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not enroll asset"),
  });
}

export function useVerifyItem() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: ({ itemId, body }: { itemId: number; body: AuditItemVerify }) =>
      auditApi.verifyItem(itemId, body),
    onSuccess: () => {
      toast.success("Verification recorded");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not record verification"),
  });
}
