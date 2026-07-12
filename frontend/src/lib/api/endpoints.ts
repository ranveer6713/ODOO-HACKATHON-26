import { api } from "./client";
import { buildQuery } from "@/lib/utils";
import type {
  ActivityLog,
  AppNotification,
  AuditCycle,
  AuditCycleCreate,
  AuditItem,
  AuditItemCreate,
  AuditItemVerify,
  AuditReport,
  Booking,
  BookingCreate,
  BookingUpdate,
  DashboardAnalytics,
  DashboardOverview,
  Maintenance,
  MaintenanceCreate,
  MaintenanceUpdate,
  MarkAllReadResult,
  Page,
  QuickAction,
  ReportCatalogEntry,
  ReportPage,
  ReportType,
  UnreadCount,
} from "./types";

type QueryParams = Record<string, string | number | boolean | null | undefined>;

// ==========================================================================
// Dashboard
// ==========================================================================
export const dashboardApi = {
  overview: () => api.get<DashboardOverview>("/api/dashboard/overview"),
  analytics: () => api.get<DashboardAnalytics>("/api/dashboard/analytics"),
  quickActions: () => api.get<QuickAction[]>("/api/dashboard/quick-actions"),
  activity: (params: QueryParams = {}) =>
    api.get<Page<import("./types").RecentActivityItem>>(
      `/api/dashboard/activity${buildQuery(params)}`,
    ),
};

// ==========================================================================
// Bookings
// ==========================================================================
export const bookingApi = {
  list: (params: QueryParams = {}) =>
    api.get<Page<Booking>>(`/api/bookings${buildQuery(params)}`),
  get: (id: number) => api.get<Booking>(`/api/bookings/${id}`),
  create: (body: BookingCreate) => api.post<Booking>("/api/bookings", body),
  update: (id: number, body: BookingUpdate) =>
    api.patch<Booking>(`/api/bookings/${id}`, body),
  remove: (id: number) => api.delete<void>(`/api/bookings/${id}`),
  approve: (id: number) => api.post<Booking>(`/api/bookings/${id}/approve`),
  reject: (id: number, reason: string) =>
    api.post<Booking>(`/api/bookings/${id}/reject`, { reason }),
  checkout: (id: number) => api.post<Booking>(`/api/bookings/${id}/checkout`),
  checkin: (id: number) => api.post<Booking>(`/api/bookings/${id}/checkin`),
  cancel: (id: number, reason?: string) =>
    api.post<Booking>(`/api/bookings/${id}/cancel`, { reason: reason ?? null }),
};

// ==========================================================================
// Maintenance
// ==========================================================================
export const maintenanceApi = {
  list: (params: QueryParams = {}) =>
    api.get<Page<Maintenance>>(`/api/maintenance${buildQuery(params)}`),
  get: (id: number) => api.get<Maintenance>(`/api/maintenance/${id}`),
  create: (body: MaintenanceCreate) =>
    api.post<Maintenance>("/api/maintenance", body),
  update: (id: number, body: MaintenanceUpdate) =>
    api.patch<Maintenance>(`/api/maintenance/${id}`, body),
  remove: (id: number) => api.delete<void>(`/api/maintenance/${id}`),
  approve: (id: number) =>
    api.post<Maintenance>(`/api/maintenance/${id}/approve`),
  reject: (id: number, reason: string) =>
    api.post<Maintenance>(`/api/maintenance/${id}/reject`, { reason }),
  assign: (id: number, technician_id: string) =>
    api.post<Maintenance>(`/api/maintenance/${id}/assign`, { technician_id }),
  start: (id: number) => api.post<Maintenance>(`/api/maintenance/${id}/start`),
  resolve: (id: number, resolution_notes: string) =>
    api.post<Maintenance>(`/api/maintenance/${id}/resolve`, {
      resolution_notes,
    }),
};

// ==========================================================================
// Asset Audit
// ==========================================================================
export const auditApi = {
  listCycles: (params: QueryParams = {}) =>
    api.get<Page<AuditCycle>>(`/api/asset-audit/cycle${buildQuery(params)}`),
  getCycle: (id: number) =>
    api.get<AuditCycle>(`/api/asset-audit/cycle/${id}`),
  createCycle: (body: AuditCycleCreate) =>
    api.post<AuditCycle>("/api/asset-audit/cycle", body),
  updateCycle: (id: number, body: Partial<AuditCycleCreate>) =>
    api.put<AuditCycle>(`/api/asset-audit/cycle/${id}`, body),
  startCycle: (id: number) =>
    api.post<AuditCycle>(`/api/asset-audit/cycle/${id}/start`),
  closeCycle: (id: number) =>
    api.post<AuditCycle>(`/api/asset-audit/cycle/${id}/close`),
  listItems: (cycleId: number) =>
    api.get<AuditItem[]>(`/api/asset-audit/cycle/${cycleId}/items`),
  addItem: (body: AuditItemCreate) =>
    api.post<AuditItem>("/api/asset-audit/item", body),
  verifyItem: (itemId: number, body: AuditItemVerify) =>
    api.put<AuditItem>(`/api/asset-audit/item/${itemId}`, body),
  report: (cycleId: number) =>
    api.get<AuditReport>(`/api/asset-audit/report/${cycleId}`),
};

// ==========================================================================
// Notifications
// ==========================================================================
export const notificationApi = {
  list: (params: QueryParams = {}) =>
    api.get<Page<AppNotification>>(`/api/notifications${buildQuery(params)}`),
  /**
   * Inbox tabs (all/unread/read/critical/archived) are served by the Reports
   * UI backend, which scopes archived vs live and supports the CRITICAL view.
   */
  listByView: (params: QueryParams = {}) =>
    api.get<Page<AppNotification>>(`/api/reports/notifications${buildQuery(params)}`),
  unreadCount: () =>
    api.get<UnreadCount>("/api/notifications/unread-count"),
  markRead: (id: number) =>
    api.post<AppNotification>(`/api/notifications/${id}/read`),
  markAllRead: () =>
    api.post<MarkAllReadResult>("/api/notifications/read-all"),
  archive: (id: number) =>
    api.post<AppNotification>(`/api/reports/notifications/${id}/archive`),
};

// ==========================================================================
// Activity Log
// ==========================================================================
export const activityLogApi = {
  list: (params: QueryParams = {}) =>
    api.get<Page<ActivityLog>>(`/api/audit${buildQuery(params)}`),
  get: (id: number) => api.get<ActivityLog>(`/api/audit/${id}`),
  flag: (id: number, reason: string) =>
    api.post<ActivityLog>(`/api/audit/${id}/flag`, { reason }),
  acknowledge: (id: number) =>
    api.post<ActivityLog>(`/api/audit/${id}/acknowledge`),
};

// ==========================================================================
// Reports
// ==========================================================================
export const reportApi = {
  catalog: () => api.get<ReportCatalogEntry[]>("/api/reports"),
  run: (type: ReportType, params: QueryParams = {}) =>
    api.get<ReportPage>(`/api/reports/${type}${buildQuery(params)}`),
  exportUrl: (type: ReportType, params: QueryParams = {}) =>
    `/api/reports/${type}/export${buildQuery(params)}`,
  exportBlob: (type: ReportType, params: QueryParams = {}) =>
    api.getBlob(`/api/reports/${type}/export${buildQuery(params)}`),
};
