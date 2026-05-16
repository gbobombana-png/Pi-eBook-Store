import { DailyTickets } from "./types";
import { getToken } from "./auth";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

async function fetchAPI<T>(path: string, options?: RequestInit & { auth?: boolean }): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> ?? {}),
  };

  if (options?.auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const { auth: _auth, ...rest } = options ?? {};
  const res = await fetch(`${API}${path}`, {
    ...rest,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail ?? `Erreur ${res.status}`);
  }
  return res.json();
}

export async function getDailyPredictions(date?: string): Promise<DailyTickets> {
  const qs = date ? `?target_date=${date}` : "";
  return fetchAPI<DailyTickets>(`/api/v1/predictions/daily${qs}`);
}

export async function getUpcomingMatches(): Promise<unknown[]> {
  return fetchAPI<unknown[]>(`/api/v1/predictions/matches/upcoming`);
}

export async function triggerGeneration(date?: string): Promise<unknown> {
  const qs = date ? `?target_date=${date}` : "";
  return fetchAPI<unknown>(`/api/v1/predictions/trigger${qs}`, { method: "GET", auth: true });
}
