import type {
  Asset,
  DiscoveredAssetInput,
  Incident,
  IncidentCreateInput,
  Token,
} from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}) as { detail?: string });
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function login(email: string, password: string): Promise<Token> {
  const body = new URLSearchParams({ username: email, password });
  return request<Token>("/api/v1/auth/login", { method: "POST", body });
}

export function register(email: string, password: string, orgName: string): Promise<void> {
  return request("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, org_name: orgName }),
  });
}

export function listIncidents(token: string): Promise<Incident[]> {
  return request<Incident[]>("/api/v1/incidents", {}, token);
}

export function createIncident(token: string, payload: IncidentCreateInput): Promise<Incident> {
  return request<Incident>(
    "/api/v1/incidents",
    { method: "POST", body: JSON.stringify(payload) },
    token
  );
}

export function listAssets(token: string): Promise<Asset[]> {
  return request<Asset[]>("/api/v1/assets", {}, token);
}

export function createAsset(token: string, payload: DiscoveredAssetInput): Promise<Asset> {
  return request<Asset>("/api/v1/assets", { method: "POST", body: JSON.stringify(payload) }, token);
}
