/**
 * Client-side session management.
 *
 * The backend auth seam is a permissive stub (no login endpoint), so AssetFlow
 * authenticates against a small directory of demo principals and persists the
 * signed-in identity in localStorage. Every API request forwards the identity
 * so a future wired foundation can attribute actions correctly.
 */

export type UserRole = "admin" | "asset_manager" | "technician" | "employee";

export interface Session {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  title: string;
  token: string;
}

const STORAGE_KEY = "assetflow.session";

export interface DemoAccount {
  id: string;
  name: string;
  email: string;
  password: string;
  role: UserRole;
  title: string;
}

export const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    id: "EMP-1001",
    name: "Alexandra Reyes",
    email: "admin@assetflow.io",
    password: "admin123",
    role: "admin",
    title: "System Administrator",
  },
  {
    id: "EMP-1002",
    name: "Marcus Bennett",
    email: "manager@assetflow.io",
    password: "manager123",
    role: "asset_manager",
    title: "Asset Manager",
  },
  {
    id: "EMP-1003",
    name: "Priya Nair",
    email: "tech@assetflow.io",
    password: "tech123",
    role: "technician",
    title: "Maintenance Technician",
  },
  {
    id: "EMP-1004",
    name: "Daniel Kim",
    email: "employee@assetflow.io",
    password: "employee123",
    role: "employee",
    title: "Operations Associate",
  },
];

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function setSession(session: Session): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  window.dispatchEvent(new Event("assetflow:session"));
}

export function clearSession(): void {
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new Event("assetflow:session"));
}

export function authenticate(
  email: string,
  password: string,
): Session | null {
  const account = DEMO_ACCOUNTS.find(
    (a) => a.email.toLowerCase() === email.trim().toLowerCase(),
  );
  if (!account || account.password !== password) return null;
  const session: Session = {
    id: account.id,
    name: account.name,
    email: account.email,
    role: account.role,
    title: account.title,
    token: `demo.${account.id}.${account.role}`,
  };
  return session;
}

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Administrator",
  asset_manager: "Asset Manager",
  technician: "Technician",
  employee: "Employee",
};
