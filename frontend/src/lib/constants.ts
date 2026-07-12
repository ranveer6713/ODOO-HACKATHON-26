import type {
  AssetStatus,
  AuditCycleStatus,
  AuditItemStatus,
  BookingStatus,
  MaintenancePriority,
  MaintenanceStatus,
  NotificationType,
  Severity,
} from "@/lib/api/types";

/** Visual tone applied by StatusBadge / chips. */
export type Tone =
  | "neutral"
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "purple";

export interface StatusMeta {
  label: string;
  tone: Tone;
}

export const BOOKING_STATUS: Record<BookingStatus, StatusMeta> = {
  pending: { label: "Pending", tone: "warning" },
  approved: { label: "Approved", tone: "info" },
  rejected: { label: "Rejected", tone: "danger" },
  checked_out: { label: "Checked Out", tone: "primary" },
  checked_in: { label: "Checked In", tone: "success" },
  cancelled: { label: "Cancelled", tone: "neutral" },
};

export const MAINTENANCE_STATUS: Record<MaintenanceStatus, StatusMeta> = {
  pending: { label: "Pending", tone: "warning" },
  approved: { label: "Approved", tone: "info" },
  rejected: { label: "Rejected", tone: "danger" },
  technician_assigned: { label: "Assigned", tone: "purple" },
  in_progress: { label: "In Progress", tone: "primary" },
  resolved: { label: "Resolved", tone: "success" },
};

export const MAINTENANCE_PRIORITY: Record<MaintenancePriority, StatusMeta> = {
  low: { label: "Low", tone: "neutral" },
  medium: { label: "Medium", tone: "info" },
  high: { label: "High", tone: "warning" },
  critical: { label: "Critical", tone: "danger" },
};

export const AUDIT_CYCLE_STATUS: Record<AuditCycleStatus, StatusMeta> = {
  created: { label: "Created", tone: "neutral" },
  active: { label: "Active", tone: "primary" },
  closed: { label: "Closed", tone: "success" },
};

export const AUDIT_ITEM_STATUS: Record<AuditItemStatus, StatusMeta> = {
  verified: { label: "Verified", tone: "success" },
  missing: { label: "Missing", tone: "danger" },
  damaged: { label: "Damaged", tone: "warning" },
};

export const ASSET_STATUS: Record<AssetStatus, StatusMeta> = {
  available: { label: "Available", tone: "success" },
  allocated: { label: "Allocated", tone: "primary" },
  reserved: { label: "Reserved", tone: "info" },
  under_maintenance: { label: "Under Maintenance", tone: "warning" },
  lost: { label: "Lost", tone: "danger" },
  disposed: { label: "Disposed", tone: "neutral" },
  retired: { label: "Retired", tone: "neutral" },
};

export const SEVERITY: Record<Severity, StatusMeta> = {
  info: { label: "Info", tone: "info" },
  warning: { label: "Warning", tone: "warning" },
  critical: { label: "Critical", tone: "danger" },
};

export const NOTIFICATION_TYPE: Record<NotificationType, StatusMeta> = {
  maintenance: { label: "Maintenance", tone: "warning" },
  booking: { label: "Booking", tone: "info" },
  audit: { label: "Audit", tone: "purple" },
  system: { label: "System", tone: "neutral" },
};

export const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-muted text-muted-foreground ring-border",
  primary: "bg-primary/10 text-primary ring-primary/20",
  success: "bg-success/10 text-success ring-success/20",
  warning: "bg-warning/15 text-warning-foreground dark:text-warning ring-warning/25",
  danger: "bg-destructive/10 text-destructive ring-destructive/20",
  info: "bg-blue-500/10 text-blue-600 dark:text-blue-400 ring-blue-500/20",
  purple: "bg-violet-500/10 text-violet-600 dark:text-violet-400 ring-violet-500/20",
};

export const CHART_COLORS = [
  "hsl(231 62% 58%)",
  "hsl(152 58% 45%)",
  "hsl(38 92% 52%)",
  "hsl(199 89% 52%)",
  "hsl(280 60% 60%)",
  "hsl(0 72% 58%)",
  "hsl(174 62% 42%)",
  "hsl(24 90% 55%)",
];

export const PAGE_SIZE = 10;
