/**
 * Browser-persisted data layer for entities that have no backend module.
 *
 * The AssetFlow backend owns Booking, Maintenance, Audit, Notifications,
 * Dashboard and Reports. Assets, Departments, Employees, Categories,
 * Allocations and Transfers are external in the production contract (referenced
 * only by string id). To keep the UI fully functional end-to-end, we persist
 * them locally with a realistic seed, exposing an async, paginated API that
 * mirrors the server modules.
 */
import type {
  Allocation,
  Asset,
  AssetCategory,
  Department,
  Employee,
  Page,
  Transfer,
} from "./types";

const NS = "assetflow.local";

function nowISO(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  return d.toISOString();
}

// --------------------------------------------------------------------------
// Seed data
// --------------------------------------------------------------------------
const seedDepartments: Department[] = [
  { id: "DEP-IT", name: "Information Technology", code: "IT", manager_id: "EMP-1001", location: "HQ · Floor 4", description: "Infrastructure, endpoints and internal platforms.", created_at: nowISO(-320) },
  { id: "DEP-OPS", name: "Operations", code: "OPS", manager_id: "EMP-1002", location: "HQ · Floor 2", description: "Facilities, logistics and day-to-day operations.", created_at: nowISO(-300) },
  { id: "DEP-FIN", name: "Finance", code: "FIN", manager_id: "EMP-1005", location: "HQ · Floor 3", description: "Accounting, procurement and asset capitalization.", created_at: nowISO(-280) },
  { id: "DEP-ENG", name: "Engineering", code: "ENG", manager_id: "EMP-1006", location: "Annex · Floor 1", description: "Product engineering and R&D lab.", created_at: nowISO(-260) },
  { id: "DEP-HR", name: "People & Culture", code: "HR", manager_id: "EMP-1007", location: "HQ · Floor 1", description: "Recruitment, onboarding and workplace experience.", created_at: nowISO(-240) },
  { id: "DEP-MKT", name: "Marketing", code: "MKT", manager_id: "EMP-1008", location: "HQ · Floor 5", description: "Brand, growth and communications.", created_at: nowISO(-220) },
];

const seedEmployees: Employee[] = [
  { id: "EMP-1001", name: "Alexandra Reyes", email: "alexandra.reyes@assetflow.io", role: "admin", department_id: "DEP-IT", title: "System Administrator", phone: "+1 415 555 0101", status: "active", created_at: nowISO(-320) },
  { id: "EMP-1002", name: "Marcus Bennett", email: "marcus.bennett@assetflow.io", role: "asset_manager", department_id: "DEP-OPS", title: "Asset Manager", phone: "+1 415 555 0102", status: "active", created_at: nowISO(-315) },
  { id: "EMP-1003", name: "Priya Nair", email: "priya.nair@assetflow.io", role: "technician", department_id: "DEP-IT", title: "Maintenance Technician", phone: "+1 415 555 0103", status: "active", created_at: nowISO(-300) },
  { id: "EMP-1004", name: "Daniel Kim", email: "daniel.kim@assetflow.io", role: "employee", department_id: "DEP-OPS", title: "Operations Associate", phone: "+1 415 555 0104", status: "active", created_at: nowISO(-290) },
  { id: "EMP-1005", name: "Sofia Martinez", email: "sofia.martinez@assetflow.io", role: "asset_manager", department_id: "DEP-FIN", title: "Finance Controller", phone: "+1 415 555 0105", status: "active", created_at: nowISO(-280) },
  { id: "EMP-1006", name: "Liam O'Brien", email: "liam.obrien@assetflow.io", role: "employee", department_id: "DEP-ENG", title: "Senior Engineer", phone: "+1 415 555 0106", status: "active", created_at: nowISO(-270) },
  { id: "EMP-1007", name: "Grace Chen", email: "grace.chen@assetflow.io", role: "employee", department_id: "DEP-HR", title: "People Partner", phone: "+1 415 555 0107", status: "active", created_at: nowISO(-260) },
  { id: "EMP-1008", name: "Noah Williams", email: "noah.williams@assetflow.io", role: "employee", department_id: "DEP-MKT", title: "Marketing Lead", phone: "+1 415 555 0108", status: "active", created_at: nowISO(-250) },
  { id: "EMP-1009", name: "Emma Thompson", email: "emma.thompson@assetflow.io", role: "technician", department_id: "DEP-OPS", title: "Field Technician", phone: "+1 415 555 0109", status: "active", created_at: nowISO(-240) },
  { id: "EMP-1010", name: "Oliver Davies", email: "oliver.davies@assetflow.io", role: "employee", department_id: "DEP-ENG", title: "QA Engineer", phone: "+1 415 555 0110", status: "inactive", created_at: nowISO(-230) },
];

const seedCategories: AssetCategory[] = [
  { id: "CAT-LAP", name: "Laptops", code: "LAP", description: "Portable workstations and notebooks.", depreciation_years: 4, created_at: nowISO(-320) },
  { id: "CAT-MON", name: "Monitors", code: "MON", description: "External displays and panels.", depreciation_years: 6, created_at: nowISO(-320) },
  { id: "CAT-PHN", name: "Mobile Devices", code: "PHN", description: "Smartphones and tablets.", depreciation_years: 3, created_at: nowISO(-310) },
  { id: "CAT-NET", name: "Networking", code: "NET", description: "Switches, routers and access points.", depreciation_years: 7, created_at: nowISO(-300) },
  { id: "CAT-FUR", name: "Furniture", code: "FUR", description: "Desks, chairs and fixtures.", depreciation_years: 10, created_at: nowISO(-290) },
  { id: "CAT-VEH", name: "Vehicles", code: "VEH", description: "Company fleet and transport.", depreciation_years: 8, created_at: nowISO(-280) },
  { id: "CAT-LAB", name: "Lab Equipment", code: "LAB", description: "Testing and measurement instruments.", depreciation_years: 5, created_at: nowISO(-270) },
];

const assetSeedDefs: Array<Partial<Asset> & { name: string; category_id: string }> = [
  { name: "MacBook Pro 16\"", category_id: "CAT-LAP", manufacturer: "Apple", model: "A2991", purchase_cost: 2899, status: "allocated", department_id: "DEP-ENG", assigned_to: "EMP-1006" },
  { name: "Dell Latitude 7440", category_id: "CAT-LAP", manufacturer: "Dell", model: "7440", purchase_cost: 1650, status: "allocated", department_id: "DEP-OPS", assigned_to: "EMP-1004" },
  { name: "ThinkPad X1 Carbon", category_id: "CAT-LAP", manufacturer: "Lenovo", model: "Gen 11", purchase_cost: 1899, status: "available", department_id: "DEP-IT", assigned_to: null },
  { name: "Dell UltraSharp U2723QE", category_id: "CAT-MON", manufacturer: "Dell", model: "U2723QE", purchase_cost: 620, status: "allocated", department_id: "DEP-ENG", assigned_to: "EMP-1010" },
  { name: "LG 27UP850", category_id: "CAT-MON", manufacturer: "LG", model: "27UP850", purchase_cost: 449, status: "available", department_id: "DEP-IT", assigned_to: null },
  { name: "iPhone 15 Pro", category_id: "CAT-PHN", manufacturer: "Apple", model: "A3101", purchase_cost: 1099, status: "allocated", department_id: "DEP-MKT", assigned_to: "EMP-1008" },
  { name: "iPad Air", category_id: "CAT-PHN", manufacturer: "Apple", model: "5th Gen", purchase_cost: 749, status: "reserved", department_id: "DEP-OPS", assigned_to: null },
  { name: "Cisco Catalyst 9200", category_id: "CAT-NET", manufacturer: "Cisco", model: "C9200", purchase_cost: 3200, status: "available", department_id: "DEP-IT", assigned_to: null },
  { name: "Ubiquiti UniFi AP", category_id: "CAT-NET", manufacturer: "Ubiquiti", model: "U6-Pro", purchase_cost: 189, status: "under_maintenance", department_id: "DEP-IT", assigned_to: null },
  { name: "Herman Miller Aeron", category_id: "CAT-FUR", manufacturer: "Herman Miller", model: "Aeron", purchase_cost: 1395, status: "allocated", department_id: "DEP-HR", assigned_to: "EMP-1007" },
  { name: "Standing Desk Pro", category_id: "CAT-FUR", manufacturer: "Uplift", model: "V2", purchase_cost: 799, status: "available", department_id: "DEP-OPS", assigned_to: null },
  { name: "Ford Transit Van", category_id: "CAT-VEH", manufacturer: "Ford", model: "Transit 350", purchase_cost: 48000, status: "allocated", department_id: "DEP-OPS", assigned_to: "EMP-1009" },
  { name: "Oscilloscope DSOX", category_id: "CAT-LAB", manufacturer: "Keysight", model: "DSOX1204G", purchase_cost: 2100, status: "available", department_id: "DEP-ENG", assigned_to: null },
  { name: "3D Printer Prusa", category_id: "CAT-LAB", manufacturer: "Prusa", model: "MK4", purchase_cost: 1099, status: "under_maintenance", department_id: "DEP-ENG", assigned_to: null },
  { name: "Surface Pro 9", category_id: "CAT-LAP", manufacturer: "Microsoft", model: "Pro 9", purchase_cost: 1299, status: "retired", department_id: null, assigned_to: null },
  { name: "Projector EB-2250U", category_id: "CAT-LAB", manufacturer: "Epson", model: "EB-2250U", purchase_cost: 1450, status: "lost", department_id: "DEP-MKT", assigned_to: null },
];

function seedAssets(): Asset[] {
  return assetSeedDefs.map((d, i) => {
    const n = i + 1;
    const tagNum = String(n).padStart(4, "0");
    return {
      id: `AST-${tagNum}`,
      tag: `AF-${tagNum}`,
      name: d.name,
      category_id: d.category_id,
      department_id: d.department_id ?? null,
      assigned_to: d.assigned_to ?? null,
      status: (d.status as Asset["status"]) ?? "available",
      serial_number: `SN-${d.model?.replace(/\s+/g, "").toUpperCase()}-${1000 + n}`,
      manufacturer: d.manufacturer ?? "Generic",
      model: d.model ?? "—",
      purchase_date: nowISO(-(60 + i * 17)),
      purchase_cost: d.purchase_cost ?? 0,
      location: seedDepartments.find((x) => x.id === d.department_id)?.location ?? "Warehouse",
      image_url: null,
      notes: "",
      created_at: nowISO(-(60 + i * 17)),
      updated_at: nowISO(-i),
    };
  });
}

function seedAllocations(assets: Asset[]): Allocation[] {
  return assets
    .filter((a) => a.assigned_to)
    .map((a, i) => ({
      id: `ALC-${String(i + 1).padStart(4, "0")}`,
      asset_id: a.id,
      employee_id: a.assigned_to!,
      allocated_at: nowISO(-(30 + i * 5)),
      returned_at: null,
      status: "active" as const,
      notes: "Standard issue on assignment.",
    }));
}

const seedTransfers: Transfer[] = [
  { id: "TRF-0001", asset_id: "AST-0003", from_department_id: "DEP-IT", to_department_id: "DEP-ENG", reason: "Reassigned to R&D lab.", status: "pending", requested_by: "EMP-1002", created_at: nowISO(-3) },
  { id: "TRF-0002", asset_id: "AST-0005", from_department_id: "DEP-IT", to_department_id: "DEP-MKT", reason: "New workstation setup.", status: "approved", requested_by: "EMP-1002", created_at: nowISO(-6) },
  { id: "TRF-0003", asset_id: "AST-0011", from_department_id: "DEP-OPS", to_department_id: "DEP-HR", reason: "Office relocation.", status: "completed", requested_by: "EMP-1005", created_at: nowISO(-14) },
];

// --------------------------------------------------------------------------
// Store engine
// --------------------------------------------------------------------------
function read<T>(key: string, seed: () => T[]): T[] {
  if (typeof window === "undefined") return seed();
  const raw = window.localStorage.getItem(`${NS}.${key}`);
  if (raw) {
    try {
      return JSON.parse(raw) as T[];
    } catch {
      /* fall through to reseed */
    }
  }
  const data = seed();
  window.localStorage.setItem(`${NS}.${key}`, JSON.stringify(data));
  return data;
}

function write<T>(key: string, data: T[]): void {
  window.localStorage.setItem(`${NS}.${key}`, JSON.stringify(data));
}

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 180));
}

interface ListParams {
  search?: string;
  page?: number;
  page_size?: number;
  [key: string]: unknown;
}

function paginate<T>(rows: T[], page = 1, pageSize = 20): Page<T> {
  const total = rows.length;
  const start = (page - 1) * pageSize;
  return {
    items: rows.slice(start, start + pageSize),
    meta: {
      total,
      page,
      page_size: pageSize,
      pages: Math.max(1, Math.ceil(total / pageSize)),
    },
  };
}

function genId(prefix: string, existing: { id: string }[]): string {
  const max = existing.reduce((m, r) => {
    const n = parseInt(r.id.split("-")[1] ?? "0", 10);
    return Number.isNaN(n) ? m : Math.max(m, n);
  }, 0);
  return `${prefix}-${String(max + 1).padStart(4, "0")}`;
}

// --------------------------------------------------------------------------
// Public store API
// --------------------------------------------------------------------------
export const localStore = {
  reset() {
    ["departments", "employees", "categories", "assets", "allocations", "transfers"].forEach(
      (k) => window.localStorage.removeItem(`${NS}.${k}`),
    );
  },

  // ---- Departments ------------------------------------------------------
  departments: {
    all: () => read("departments", () => seedDepartments),
    list(params: ListParams = {}) {
      let rows = read<Department>("departments", () => seedDepartments);
      if (params.search) {
        const q = String(params.search).toLowerCase();
        rows = rows.filter(
          (r) => r.name.toLowerCase().includes(q) || r.code.toLowerCase().includes(q),
        );
      }
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<Department, "id" | "created_at">) {
      const rows = read<Department>("departments", () => seedDepartments);
      const row: Department = { ...input, id: genId("DEP", rows), created_at: nowISO() };
      write("departments", [row, ...rows]);
      return delay(row);
    },
    update(id: string, patch: Partial<Department>) {
      const rows = read<Department>("departments", () => seedDepartments);
      const next = rows.map((r) => (r.id === id ? { ...r, ...patch } : r));
      write("departments", next);
      return delay(next.find((r) => r.id === id)!);
    },
    remove(id: string) {
      const rows = read<Department>("departments", () => seedDepartments).filter((r) => r.id !== id);
      write("departments", rows);
      return delay({ ok: true });
    },
  },

  // ---- Employees --------------------------------------------------------
  employees: {
    all: () => read("employees", () => seedEmployees),
    list(params: ListParams = {}) {
      let rows = read<Employee>("employees", () => seedEmployees);
      if (params.department_id)
        rows = rows.filter((r) => r.department_id === params.department_id);
      if (params.status) rows = rows.filter((r) => r.status === params.status);
      if (params.search) {
        const q = String(params.search).toLowerCase();
        rows = rows.filter(
          (r) => r.name.toLowerCase().includes(q) || r.email.toLowerCase().includes(q),
        );
      }
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<Employee, "id" | "created_at">) {
      const rows = read<Employee>("employees", () => seedEmployees);
      const row: Employee = { ...input, id: genId("EMP", rows), created_at: nowISO() };
      write("employees", [row, ...rows]);
      return delay(row);
    },
    update(id: string, patch: Partial<Employee>) {
      const rows = read<Employee>("employees", () => seedEmployees);
      const next = rows.map((r) => (r.id === id ? { ...r, ...patch } : r));
      write("employees", next);
      return delay(next.find((r) => r.id === id)!);
    },
    remove(id: string) {
      const rows = read<Employee>("employees", () => seedEmployees).filter((r) => r.id !== id);
      write("employees", rows);
      return delay({ ok: true });
    },
  },

  // ---- Categories -------------------------------------------------------
  categories: {
    all: () => read("categories", () => seedCategories),
    list(params: ListParams = {}) {
      let rows = read<AssetCategory>("categories", () => seedCategories);
      if (params.search) {
        const q = String(params.search).toLowerCase();
        rows = rows.filter((r) => r.name.toLowerCase().includes(q));
      }
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<AssetCategory, "id" | "created_at">) {
      const rows = read<AssetCategory>("categories", () => seedCategories);
      const row: AssetCategory = { ...input, id: genId("CAT", rows), created_at: nowISO() };
      write("categories", [row, ...rows]);
      return delay(row);
    },
    update(id: string, patch: Partial<AssetCategory>) {
      const rows = read<AssetCategory>("categories", () => seedCategories);
      const next = rows.map((r) => (r.id === id ? { ...r, ...patch } : r));
      write("categories", next);
      return delay(next.find((r) => r.id === id)!);
    },
    remove(id: string) {
      const rows = read<AssetCategory>("categories", () => seedCategories).filter((r) => r.id !== id);
      write("categories", rows);
      return delay({ ok: true });
    },
  },

  // ---- Assets -----------------------------------------------------------
  assets: {
    all: () => read("assets", seedAssets),
    get(id: string) {
      return delay(read<Asset>("assets", seedAssets).find((r) => r.id === id) ?? null);
    },
    list(params: ListParams = {}) {
      let rows = read<Asset>("assets", seedAssets);
      if (params.status) rows = rows.filter((r) => r.status === params.status);
      if (params.category_id) rows = rows.filter((r) => r.category_id === params.category_id);
      if (params.department_id) rows = rows.filter((r) => r.department_id === params.department_id);
      if (params.search) {
        const q = String(params.search).toLowerCase();
        rows = rows.filter(
          (r) =>
            r.name.toLowerCase().includes(q) ||
            r.tag.toLowerCase().includes(q) ||
            r.serial_number.toLowerCase().includes(q),
        );
      }
      if (params.sort_by) {
        const key = params.sort_by as keyof Asset;
        const dir = params.order === "asc" ? 1 : -1;
        rows = [...rows].sort((a, b) =>
          (a[key] ?? "") > (b[key] ?? "") ? dir : (a[key] ?? "") < (b[key] ?? "") ? -dir : 0,
        );
      }
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<Asset, "id" | "tag" | "created_at" | "updated_at">) {
      const rows = read<Asset>("assets", seedAssets);
      const id = genId("AST", rows);
      const tag = `AF-${id.split("-")[1]}`;
      const row: Asset = { ...input, id, tag, created_at: nowISO(), updated_at: nowISO() };
      write("assets", [row, ...rows]);
      return delay(row);
    },
    update(id: string, patch: Partial<Asset>) {
      const rows = read<Asset>("assets", seedAssets);
      const next = rows.map((r) => (r.id === id ? { ...r, ...patch, updated_at: nowISO() } : r));
      write("assets", next);
      return delay(next.find((r) => r.id === id)!);
    },
    remove(id: string) {
      const rows = read<Asset>("assets", seedAssets).filter((r) => r.id !== id);
      write("assets", rows);
      return delay({ ok: true });
    },
  },

  // ---- Allocations ------------------------------------------------------
  allocations: {
    list(params: ListParams = {}) {
      let rows = read<Allocation>("allocations", () => seedAllocations(seedAssets()));
      if (params.status) rows = rows.filter((r) => r.status === params.status);
      if (params.asset_id) rows = rows.filter((r) => r.asset_id === params.asset_id);
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<Allocation, "id" | "allocated_at" | "returned_at" | "status">) {
      const rows = read<Allocation>("allocations", () => seedAllocations(seedAssets()));
      const row: Allocation = {
        ...input,
        id: genId("ALC", rows),
        allocated_at: nowISO(),
        returned_at: null,
        status: "active",
      };
      write("allocations", [row, ...rows]);
      // reflect on asset
      localStore.assets.update(input.asset_id, {
        assigned_to: input.employee_id,
        status: "allocated",
      });
      return delay(row);
    },
    returnAsset(id: string) {
      const rows = read<Allocation>("allocations", () => seedAllocations(seedAssets()));
      const target = rows.find((r) => r.id === id);
      const next = rows.map((r) =>
        r.id === id ? { ...r, status: "returned" as const, returned_at: nowISO() } : r,
      );
      write("allocations", next);
      if (target)
        localStore.assets.update(target.asset_id, { assigned_to: null, status: "available" });
      return delay(next.find((r) => r.id === id)!);
    },
  },

  // ---- Transfers --------------------------------------------------------
  transfers: {
    list(params: ListParams = {}) {
      let rows = read<Transfer>("transfers", () => seedTransfers);
      if (params.status) rows = rows.filter((r) => r.status === params.status);
      return delay(paginate(rows, params.page, params.page_size));
    },
    create(input: Omit<Transfer, "id" | "created_at" | "status">) {
      const rows = read<Transfer>("transfers", () => seedTransfers);
      const row: Transfer = { ...input, id: genId("TRF", rows), created_at: nowISO(), status: "pending" };
      write("transfers", [row, ...rows]);
      return delay(row);
    },
    setStatus(id: string, status: Transfer["status"]) {
      const rows = read<Transfer>("transfers", () => seedTransfers);
      const target = rows.find((r) => r.id === id);
      const next = rows.map((r) => (r.id === id ? { ...r, status } : r));
      write("transfers", next);
      if (status === "completed" && target)
        localStore.assets.update(target.asset_id, { department_id: target.to_department_id });
      return delay(next.find((r) => r.id === id)!);
    },
  },
};

// Convenient synchronous lookups for label resolution in tables.
export function lookupMaps() {
  return {
    departments: new Map(localStore.departments.all().map((d) => [d.id, d])),
    employees: new Map(localStore.employees.all().map((e) => [e.id, e])),
    categories: new Map(localStore.categories.all().map((c) => [c.id, c])),
    assets: new Map(localStore.assets.all().map((a) => [a.id, a])),
  };
}
