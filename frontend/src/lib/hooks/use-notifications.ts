"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { notificationApi } from "@/lib/api/endpoints";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

export function useNotifications(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.notifications.list(params),
    queryFn: () => notificationApi.list(params as never),
  });
}

export function useNotificationsByView(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.notifications.list(["view", params]),
    queryFn: () => notificationApi.listByView(params as never),
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: qk.notifications.unread,
    queryFn: notificationApi.unreadCount,
    refetchInterval: 60_000,
  });
}

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["notifications"] });
}

export function useMarkRead() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: number) => notificationApi.markRead(id),
    onSuccess: invalidate,
    onError: (e) => toastError(e, "Could not mark as read"),
  });
}

export function useMarkAllRead() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: () => notificationApi.markAllRead(),
    onSuccess: (res) => {
      toast.success(`Marked ${res.marked_read} as read`);
      invalidate();
    },
    onError: (e) => toastError(e, "Could not mark all as read"),
  });
}

export function useArchiveNotification() {
  const invalidate = useInvalidate();
  return useMutation({
    mutationFn: (id: number) => notificationApi.archive(id),
    onSuccess: () => {
      toast.success("Notification archived");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not archive"),
  });
}
