import { getSession } from "@/lib/auth/session";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** When true, returns the raw Response (for blob/file downloads). */
  raw?: boolean;
}

function authHeaders(): Record<string, string> {
  const session = getSession();
  if (!session) return {};
  // The backend auth seam is permissive; we forward identity hints so that a
  // wired foundation can attribute actions to the signed-in principal.
  return {
    "X-User-Id": session.id,
    "X-User-Role": session.role,
    Authorization: `Bearer ${session.token}`,
  };
}

async function parseError(res: Response): Promise<ApiError> {
  let detail: unknown;
  let message = `${res.status} ${res.statusText}`;
  try {
    const data = await res.json();
    detail = data?.detail ?? data;
    if (typeof data?.detail === "string") message = data.detail;
    else if (Array.isArray(data?.detail) && data.detail[0]?.msg)
      message = data.detail.map((d: { msg: string }) => d.msg).join(", ");
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(res.status, message, detail);
}

async function request<T>(
  method: string,
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, raw, headers, ...rest } = options;
  const init: RequestInit = {
    method,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...authHeaders(),
      ...(headers as Record<string, string>),
    },
    ...rest,
  };
  if (body !== undefined) init.body = JSON.stringify(body);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, init);
  } catch (err) {
    throw new ApiError(
      0,
      "Unable to reach the AssetFlow API. Is the backend running?",
      err,
    );
  }

  if (!res.ok) throw await parseError(res);
  if (raw) return res as unknown as T;
  if (res.status === 204) return undefined as T;

  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>("GET", path, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("POST", path, { ...options, body }),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PUT", path, { ...options, body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>("PATCH", path, { ...options, body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>("DELETE", path, options),
  /** Raw GET for file/blob downloads. */
  getBlob: async (path: string): Promise<Blob> => {
    const res = await request<Response>("GET", path, { raw: true });
    return res.blob();
  },
};
