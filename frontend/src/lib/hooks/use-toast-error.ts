import { toast } from "sonner";
import { ApiError } from "@/lib/api/client";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}

export function toastError(error: unknown, fallback = "Action failed") {
  toast.error(fallback, { description: errorMessage(error) });
}
