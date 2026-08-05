// Thin fetch wrapper around the gateway API. Every backend response is
// wrapped in the shared envelope {success, data, error} (see
// dvc-api/pkg/response) — this file unwraps that consistently so pages
// never touch the envelope shape directly. Mirrors salon-web/src/lib/api.ts.

// Logical OR (not ??) on purpose: an empty string in .env.production must
// also fall back, not be used as-is.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

// Identifies this deployment to iam's multi-tenant register/login (see
// dvc-api/docs/srs/platform-tenant-isolation.md) — required on register/login
// only, never on already-authenticated requests (tenant travels in the JWT
// after that).
const APP_KEY = import.meta.env.VITE_APP_KEY || "";

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

type Envelope<T> = {
  success: boolean;
  data?: T;
  error?: { code: string; message: string };
};

async function parseEnvelope<T>(res: Response): Promise<T> {
  if (res.status === 204) {
    return undefined as T;
  }
  const body = (await res.json()) as Envelope<T>;
  if (!res.ok || !body.success) {
    throw new ApiError(res.status, body.error?.code ?? "UNKNOWN", body.error?.message ?? res.statusText);
  }
  return body.data as T;
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  appKey?: boolean; // send X-App-Key — only register/login need this
};

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (opts.token) {
    headers.Authorization = `Bearer ${opts.token}`;
  }
  if (opts.appKey) {
    headers["X-App-Key"] = APP_KEY;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method: opts.method ?? "GET",
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  });

  return parseEnvelope<T>(res);
}

// ---- iam (auth) ----

export type Account = {
  id: string;
  email: string;
  phone?: string;
  full_name?: string;
  roles: string[];
  status: string;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
};

export function register(input: { email: string; password: string; full_name: string; phone?: string }) {
  return apiFetch<Account>("/api/v1/auth/register", { method: "POST", body: input, appKey: true });
}

export function login(input: { identifier: string; password: string }) {
  return apiFetch<TokenPair>("/api/v1/auth/login", { method: "POST", body: input, appKey: true });
}

export function refresh(refreshToken: string) {
  return apiFetch<TokenPair>("/api/v1/auth/refresh", { method: "POST", body: { refresh_token: refreshToken } });
}

export function logout(refreshToken: string) {
  return apiFetch<void>("/api/v1/auth/logout", { method: "POST", body: { refresh_token: refreshToken } });
}

export function getMe(token: string) {
  return apiFetch<Account>("/api/v1/users/me", { token });
}

// ---- lending domain types (match apps/lending/internal/transport/httptransport/dto.go) ----
// Full CRUD functions land in W2 (search/list) and W3 (post/interest/rating) —
// W1 only needs the shapes so future milestones don't redefine them.

export type ItemType = "lend_free" | "rent_paid" | "donate";
export type ItemStatus = "available" | "reserved" | "given_out";

export type Item = {
  id: string;
  owner_user_id: string;
  title: string;
  description: string | null;
  category: string;
  type: ItemType;
  rental_price_note: string | null;
  lat: number;
  lng: number;
  address_label: string;
  photo_keys: string[];
  status: ItemStatus;
  created_at: string;
  updated_at: string;
};

export type ItemSearchResult = Item & { distance_km: number };

// ---- lending: public search (GET /items, FR-10..FR-13) ----
// No auth, no X-App-Key — this route is intentionally public (see
// dvc-api/docs/srs/lending-platform.md FR-10 + router.go comment).
// Server applies defaults when a param is omitted: radius_km=5, status=available,
// limit=20 (max 50), offset=0 — we don't duplicate those defaults here, callers
// decide what to send.

export type ItemSearchParams = {
  lat: number;
  lng: number;
  radius_km?: number;
  category?: string;
  type?: ItemType;
  status?: ItemStatus;
  limit?: number;
  offset?: number;
};

export function searchItems(params: ItemSearchParams) {
  const qs = new URLSearchParams();
  qs.set("lat", String(params.lat));
  qs.set("lng", String(params.lng));
  if (params.radius_km !== undefined) qs.set("radius_km", String(params.radius_km));
  if (params.category) qs.set("category", params.category);
  if (params.type) qs.set("type", params.type);
  if (params.status) qs.set("status", params.status);
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  if (params.offset !== undefined) qs.set("offset", String(params.offset));
  return apiFetch<ItemSearchResult[]>(`/api/v1/lending/items?${qs.toString()}`);
}

export type Interest = {
  id: string;
  item_id: string;
  interested_user_id: string;
  contact_revealed_at: string;
  created_at: string;
};

export type Rating = {
  id: string;
  item_id: string;
  rater_user_id: string;
  rated_user_id: string;
  score: number;
  comment: string | null;
  created_at: string;
};

// ---- lending: item detail + owner CRUD (FR-2/3/5/6/7/8/9) ----

export function getItem(id: string) {
  return apiFetch<Item>(`/api/v1/lending/items/${id}`);
}

export type CreateItemInput = {
  title: string;
  description?: string;
  category: string;
  type: ItemType;
  rental_price_note?: string;
  lat: number;
  lng: number;
  address_label: string;
  photo_keys?: string[];
};

export function createItem(token: string, input: CreateItemInput) {
  return apiFetch<Item>("/api/v1/lending/items", { method: "POST", body: input, token });
}

// Partial update (FR-5) — every field optional, omit to leave unchanged.
export type UpdateItemInput = Partial<Omit<CreateItemInput, "type">>;

export function updateItem(token: string, id: string, input: UpdateItemInput) {
  return apiFetch<Item>(`/api/v1/lending/items/${id}`, { method: "PATCH", body: input, token });
}

export function deleteItem(token: string, id: string) {
  return apiFetch<void>(`/api/v1/lending/items/${id}`, { method: "DELETE", token });
}

export function updateItemStatus(token: string, id: string, status: ItemStatus) {
  return apiFetch<Item>(`/api/v1/lending/items/${id}/status`, { method: "PATCH", body: { status }, token });
}

export function listMyItems(token: string) {
  return apiFetch<Item[]>("/api/v1/lending/items/mine", { token });
}

// ---- lending: interest (FR-14/15/16/17) ----

export type ContactInfo = {
  id: string;
  email: string;
  phone: string;
  full_name: string;
};

export type ExpressInterestResult = {
  interest: Interest;
  contact: ContactInfo;
};

export function expressInterest(token: string, itemId: string) {
  return apiFetch<ExpressInterestResult>(`/api/v1/lending/items/${itemId}/interest`, { method: "POST", token });
}

// Owner-only (FR-17) — 403 for anyone else.
export function listInterests(token: string, itemId: string) {
  return apiFetch<Interest[]>(`/api/v1/lending/items/${itemId}/interests`, { token });
}

// ---- lending: ratings (FR-18/19/20/21) ----

export type SubmitRatingInput = {
  rated_user_id: string;
  score: number;
  comment?: string;
};

export function submitRating(token: string, itemId: string, input: SubmitRatingInput) {
  return apiFetch<Rating>(`/api/v1/lending/items/${itemId}/ratings`, { method: "POST", body: input, token });
}

export type UserRatingsResult = {
  ratings: Rating[];
  avg_score: number;
  count: number;
};

export function getUserRatings(userId: string) {
  return apiFetch<UserRatingsResult>(`/api/v1/lending/users/${userId}/ratings`);
}
