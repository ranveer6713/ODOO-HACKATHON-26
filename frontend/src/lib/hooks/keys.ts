/** Central registry of TanStack Query keys. */
export const qk = {
  dashboard: {
    overview: ["dashboard", "overview"] as const,
    analytics: ["dashboard", "analytics"] as const,
    activity: (params: unknown) => ["dashboard", "activity", params] as const,
  },
  bookings: {
    list: (params: unknown) => ["bookings", "list", params] as const,
    detail: (id: number) => ["bookings", "detail", id] as const,
  },
  maintenance: {
    list: (params: unknown) => ["maintenance", "list", params] as const,
    detail: (id: number) => ["maintenance", "detail", id] as const,
  },
  audit: {
    cycles: (params: unknown) => ["audit", "cycles", params] as const,
    cycle: (id: number) => ["audit", "cycle", id] as const,
    items: (cycleId: number) => ["audit", "items", cycleId] as const,
    report: (cycleId: number) => ["audit", "report", cycleId] as const,
  },
  notifications: {
    list: (params: unknown) => ["notifications", "list", params] as const,
    unread: ["notifications", "unread"] as const,
  },
  activity: {
    list: (params: unknown) => ["activity", "list", params] as const,
    detail: (id: number) => ["activity", "detail", id] as const,
  },
  reports: {
    catalog: ["reports", "catalog"] as const,
    run: (type: string, params: unknown) => ["reports", type, params] as const,
  },
  entities: {
    departments: (params: unknown) => ["entities", "departments", params] as const,
    employees: (params: unknown) => ["entities", "employees", params] as const,
    categories: (params: unknown) => ["entities", "categories", params] as const,
    assets: (params: unknown) => ["entities", "assets", params] as const,
    asset: (id: string) => ["entities", "asset", id] as const,
    allocations: (params: unknown) => ["entities", "allocations", params] as const,
    transfers: (params: unknown) => ["entities", "transfers", params] as const,
  },
};
