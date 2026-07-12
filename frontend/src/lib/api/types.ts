/**
 * Type definitions mirroring the AssetFlow FastAPI schemas.
 * These are the single source of truth for the API contract on the client.
 */

// --------------------------------------------------------------------------
// Pagination envelope (shared by every paginated endpoint)
// --------------------------------------------------------------------------
export interface PageMeta {
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

// --------------------------------------------------------------------------
// Booking
// --------------------------------------------------------------------------
export type BookingStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "checked_out"
  | "checked_in"
  | "cancelled";

export interface Booking {
  id: number;
  asset_id: string;
  requested_by: string;
  purpose: string;
  start_time: string;
  end_time: string;
  status: BookingStatus;
  approved_by: string | null;
  rejection_reason: string | null;
  cancelled_by: string | null;
  cancellation_reason: string | null;
  approved_at: string | null;
  checked_out_at: string | null;
  checked_in_at: string | null;
  cancelled_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingCreate {
  asset_id: string;
  purpose: string;
  start_time: string;
  end_time: string;
}

export interface BookingUpdate {
  purpose?: string;
  start_time?: string;
  end_time?: string;
}

// --------------------------------------------------------------------------
// Maintenance
// --------------------------------------------------------------------------
export type MaintenancePriority = "low" | "medium" | "high" | "critical";
export type MaintenanceStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "technician_assigned"
  | "in_progress"
  | "resolved";

export interface Maintenance {
  id: number;
  asset_id: string;
  raised_by: string;
  priority: MaintenancePriority;
  issue_description: string;
  photo_url: string | null;
  status: MaintenanceStatus;
  approved_by: string | null;
  technician_id: string | null;
  rejection_reason: string | null;
  resolution_notes: string | null;
  approved_at: string | null;
  assigned_at: string | null;
  started_at: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface MaintenanceCreate {
  asset_id: string;
  priority: MaintenancePriority;
  issue_description: string;
  photo_url?: string | null;
}

export interface MaintenanceUpdate {
  priority?: MaintenancePriority;
  issue_description?: string;
  photo_url?: string | null;
}

// --------------------------------------------------------------------------
// Asset Audit
// --------------------------------------------------------------------------
export type AuditCycleStatus = "created" | "active" | "closed";
export type AuditItemStatus = "verified" | "missing" | "damaged";

export interface AuditCycle {
  id: number;
  name: string;
  department_id: string | null;
  location: string | null;
  start_date: string;
  end_date: string;
  created_by: string;
  status: AuditCycleStatus;
  started_at: string | null;
  closed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditCycleCreate {
  name: string;
  department_id?: string | null;
  location?: string | null;
  start_date: string;
  end_date: string;
}

export interface AuditItem {
  id: number;
  audit_cycle_id: number;
  asset_id: string;
  auditor_id: string;
  status: AuditItemStatus | null;
  remarks: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditItemCreate {
  audit_cycle_id: number;
  asset_id: string;
  auditor_id: string;
}

export interface AuditItemVerify {
  status: AuditItemStatus;
  remarks?: string | null;
}

export interface AuditReportSummary {
  total_items: number;
  verified: number;
  missing: number;
  damaged: number;
  pending: number;
}

export interface AuditReport {
  cycle_id: number;
  cycle_name: string;
  status: AuditCycleStatus;
  summary: AuditReportSummary;
  discrepancy_count: number;
  verified_assets: AuditItem[];
  missing_assets: AuditItem[];
  damaged_assets: AuditItem[];
}

// --------------------------------------------------------------------------
// Notifications
// --------------------------------------------------------------------------
export type NotificationType = "maintenance" | "booking" | "audit" | "system";
export type Severity = "info" | "warning" | "critical";

export interface AppNotification {
  id: number;
  recipient_id: string;
  type: NotificationType;
  severity: Severity;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  read_at: string | null;
  archived: boolean;
  archived_at: string | null;
  created_at: string;
}

export interface UnreadCount {
  unread: number;
}

export interface MarkAllReadResult {
  marked_read: number;
}

// --------------------------------------------------------------------------
// Activity Log (Audit trail)
// --------------------------------------------------------------------------
export interface ActivityLog {
  id: number;
  actor_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  description: string | null;
  severity: Severity;
  flagged: boolean;
  flagged_by: string | null;
  flag_reason: string | null;
  flagged_at: string | null;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  created_at: string;
}

// --------------------------------------------------------------------------
// Dashboard
// --------------------------------------------------------------------------
export interface AssetKpiCards {
  total: number;
  available: number;
  allocated: number;
  reserved: number;
  under_maintenance: number;
  lost: number;
  disposed: number;
  retired: number;
  other: number;
}

export interface BookingSummary {
  total: number;
  today: number;
  upcoming: number;
  active: number;
  completed: number;
  cancelled: number;
}

export interface MaintenanceSummary {
  total: number;
  pending: number;
  approved: number;
  assigned: number;
  in_progress: number;
  resolved: number;
}

export interface AuditSummary {
  audit_cycles: number;
  active_cycles: number;
  verified_assets: number;
  missing_assets: number;
  damaged_assets: number;
  pending_items: number;
}

export interface NotificationTypeCount {
  type: NotificationType;
  count: number;
}

export interface NotificationSummary {
  total: number;
  unread: number;
  today: number;
  critical_alerts: number;
  by_type: NotificationTypeCount[];
}

export interface RecentActivityItem {
  id: number;
  user: string;
  action: string;
  entity_type: string;
  entity_id: string;
  description: string | null;
  severity: Severity;
  timestamp: string;
}

export interface QuickAction {
  key: string;
  label: string;
  description: string;
  method: string;
  endpoint: string;
  required_roles: string[];
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface ChartSeries {
  name: string;
  points: ChartDataPoint[];
}

export interface DashboardAnalytics {
  asset_distribution: ChartSeries;
  department_distribution: ChartSeries;
  maintenance_trend: ChartSeries;
  booking_trend: ChartSeries;
  audit_trend: ChartSeries;
}

export interface DashboardOverview {
  generated_at: string;
  kpis: AssetKpiCards;
  bookings: BookingSummary;
  maintenance: MaintenanceSummary;
  audit: AuditSummary;
  notifications: NotificationSummary;
  recent_activity: RecentActivityItem[];
  quick_actions: QuickAction[];
}

// --------------------------------------------------------------------------
// Reports
// --------------------------------------------------------------------------
export type ReportType =
  | "asset"
  | "booking"
  | "maintenance"
  | "audit"
  | "notification"
  | "department";

export type ExportFormat = "csv" | "pdf";

export interface ReportColumn {
  key: string;
  label: string;
}

export interface ReportPage {
  report: ReportType;
  title: string;
  columns: ReportColumn[];
  items: Record<string, unknown>[];
  meta: PageMeta;
}

export interface ReportCatalogEntry {
  report: ReportType;
  title: string;
  columns: ReportColumn[];
  searchable: boolean;
  filters: string[];
  sortable: string[];
  default_sort: string;
}

// --------------------------------------------------------------------------
// Local-only entities (no backend — string-FK external contract).
// Persisted in the browser so the UI is fully functional end-to-end.
// --------------------------------------------------------------------------
export type AssetStatus =
  | "available"
  | "allocated"
  | "reserved"
  | "under_maintenance"
  | "lost"
  | "disposed"
  | "retired";

export interface Department {
  id: string;
  name: string;
  code: string;
  manager_id: string | null;
  location: string;
  description: string;
  created_at: string;
}

export interface Employee {
  id: string;
  name: string;
  email: string;
  role: string;
  department_id: string;
  title: string;
  phone: string;
  status: "active" | "inactive";
  created_at: string;
}

export interface AssetCategory {
  id: string;
  name: string;
  code: string;
  description: string;
  depreciation_years: number;
  created_at: string;
}

export interface Asset {
  id: string;
  tag: string;
  name: string;
  category_id: string;
  department_id: string | null;
  assigned_to: string | null;
  status: AssetStatus;
  serial_number: string;
  manufacturer: string;
  model: string;
  purchase_date: string;
  purchase_cost: number;
  location: string;
  image_url: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface Allocation {
  id: string;
  asset_id: string;
  employee_id: string;
  allocated_at: string;
  returned_at: string | null;
  status: "active" | "returned";
  notes: string;
}

export interface Transfer {
  id: string;
  asset_id: string;
  from_department_id: string | null;
  to_department_id: string;
  reason: string;
  status: "pending" | "approved" | "completed" | "rejected";
  requested_by: string;
  created_at: string;
}
