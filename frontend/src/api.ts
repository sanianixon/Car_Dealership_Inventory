/**
 * The single place that talks to the API.
 *
 * Every call goes through request(), so the bearer token, the error envelope
 * and the 401-means-signed-out rule are each handled once rather than in every
 * component.
 */

import type { SearchFilters, User, Vehicle } from "./types";

const TOKEN_KEY = "dealership.token";

interface FieldError {
  path: string;
  message: string;
}

/**
 * An error the API reported, carrying its status and any per-field messages.
 * The backend always answers failures as {"error": {message, details}}.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly details: FieldError[];

  constructor(message: string, status: number, details: FieldError[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }

  /** The message for one field, for showing errors next to the input. */
  fieldError(path: string): string | undefined {
    return this.details.find((detail) => detail.path === path)?.message;
  }
}

// localStorage is wrapped because it throws in private windows and when site
// data is blocked. A missing token simply means signed out.
export function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function writeToken(token: string | null): void {
  try {
    if (token === null) localStorage.removeItem(TOKEN_KEY);
    else localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Not fatal: the session still works, it just will not survive a reload.
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const token = readToken();
  const response = await fetch(`/api${path}`, {
    method,
    headers: {
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (response.status === 204) return undefined as T;

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const envelope = payload?.error;
    throw new ApiError(
      envelope?.message ?? `Request failed with status ${response.status}`,
      response.status,
      envelope?.details ?? [],
    );
  }

  return payload as T;
}

/** Drop blank filters so an empty search box widens results instead of narrowing them. */
function searchQuery(filters: SearchFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value.trim() !== "") params.set(key, value.trim());
  }
  const query = params.toString();
  return query === "" ? "" : `?${query}`;
}

export const api = {
  register: (email: string, password: string, adminCode?: string) =>
    request<{ user: User }>("POST", "/auth/register", {
      email,
      password,
      ...(adminCode ? { adminCode } : {}),
    }),

  login: (email: string, password: string) =>
    request<{ token: string; user: User }>("POST", "/auth/login", { email, password }),

  me: () => request<{ user: User }>("GET", "/auth/me"),

  listVehicles: () => request<{ vehicles: Vehicle[] }>("GET", "/vehicles"),

  searchVehicles: (filters: SearchFilters) =>
    request<{ vehicles: Vehicle[] }>("GET", `/vehicles/search${searchQuery(filters)}`),

  createVehicle: (vehicle: Omit<Vehicle, "id" | "createdAt" | "updatedAt">) =>
    request<{ vehicle: Vehicle }>("POST", "/vehicles", vehicle),

  updateVehicle: (id: string, changes: Partial<Vehicle>) =>
    request<{ vehicle: Vehicle }>("PUT", `/vehicles/${id}`, changes),

  deleteVehicle: (id: string) => request<void>("DELETE", `/vehicles/${id}`),

  purchase: (id: string, quantity = 1) =>
    request<{ vehicle: Vehicle; purchased: number }>("POST", `/vehicles/${id}/purchase`, {
      quantity,
    }),

  restock: (id: string, quantity: number) =>
    request<{ vehicle: Vehicle; restocked: number }>("POST", `/vehicles/${id}/restock`, {
      quantity,
    }),
};
