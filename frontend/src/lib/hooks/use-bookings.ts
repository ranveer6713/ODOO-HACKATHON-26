"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { bookingApi } from "@/lib/api/endpoints";
import type { BookingCreate, BookingUpdate } from "@/lib/api/types";
import { qk } from "./keys";
import { toastError } from "./use-toast-error";

export function useBookings(params: Record<string, unknown> = {}) {
  return useQuery({
    queryKey: qk.bookings.list(params),
    queryFn: () => bookingApi.list(params as never),
  });
}

export function useBooking(id: number, enabled = true) {
  return useQuery({
    queryKey: qk.bookings.detail(id),
    queryFn: () => bookingApi.get(id),
    enabled: enabled && Number.isFinite(id),
  });
}

function useInvalidateBookings() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries({ queryKey: ["bookings"] });
}

export function useCreateBooking() {
  const invalidate = useInvalidateBookings();
  return useMutation({
    mutationFn: (body: BookingCreate) => bookingApi.create(body),
    onSuccess: () => {
      toast.success("Booking created", { description: "Your request is pending approval." });
      invalidate();
    },
    onError: (e) => toastError(e, "Could not create booking"),
  });
}

export function useUpdateBooking() {
  const invalidate = useInvalidateBookings();
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: BookingUpdate }) =>
      bookingApi.update(id, body),
    onSuccess: () => {
      toast.success("Booking updated");
      invalidate();
    },
    onError: (e) => toastError(e, "Could not update booking"),
  });
}

export function useBookingAction() {
  const invalidate = useInvalidateBookings();
  return useMutation({
    mutationFn: async ({
      id,
      action,
      reason,
    }: {
      id: number;
      action: "approve" | "reject" | "checkout" | "checkin" | "cancel" | "delete";
      reason?: string;
    }) => {
      switch (action) {
        case "approve":
          return bookingApi.approve(id);
        case "reject":
          return bookingApi.reject(id, reason ?? "");
        case "checkout":
          return bookingApi.checkout(id);
        case "checkin":
          return bookingApi.checkin(id);
        case "cancel":
          return bookingApi.cancel(id, reason);
        case "delete":
          return bookingApi.remove(id);
      }
    },
    onSuccess: (_data, vars) => {
      const labels: Record<string, string> = {
        approve: "Booking approved",
        reject: "Booking rejected",
        checkout: "Asset checked out",
        checkin: "Asset checked in",
        cancel: "Booking cancelled",
        delete: "Booking deleted",
      };
      toast.success(labels[vars.action]);
      invalidate();
    },
    onError: (e) => toastError(e, "Action failed"),
  });
}
