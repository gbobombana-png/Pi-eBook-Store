import { DailyTickets } from "./types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...options,
    next: { revalidate: 3600 },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API error ${res.status}: ${err}`);
  }
  return res.json();
}

export async function getDailyPredictions(date?: string): Promise<DailyTickets> {
  const qs = date ? `?target_date=${date}` : "";
  return fetchAPI<DailyTickets>(`/api/v1/predictions/daily${qs}`);
}

export async function getUpcomingMatches() {
  return fetchAPI(`/api/v1/predictions/matches/upcoming`);
}

export async function triggerGeneration(date?: string) {
  const qs = date ? `?target_date=${date}` : "";
  return fetchAPI(`/api/v1/predictions/trigger${qs}`, { method: "GET", next: { revalidate: 0 } });
}
