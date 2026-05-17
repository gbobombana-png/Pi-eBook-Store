const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  // Matches
  listMatches: (params?: { status?: string; competition?: string; limit?: number }) => {
    const q = new URLSearchParams(params as Record<string, string>).toString();
    return request<import("./types").DashboardMatchCard[]>(`/matches${q ? `?${q}` : ""}`);
  },
  getMatch: (id: number) => request<import("./types").MatchOut>(`/matches/${id}`),
  getOddsHistory: (id: number) => request<import("./types").OddsDataPoint[]>(`/matches/${id}/odds`),

  // Analysis
  analyzeMatch: (matchId: number, body: unknown) =>
    request<import("./types").FullAnalysisResponse>(`/analysis/match/${matchId}`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  quickAnalyze: (body: unknown) =>
    request<import("./types").FullAnalysisResponse>("/analysis/quick", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};

export function createMatchWebSocket(matchId: number | "global", onMessage: (d: unknown) => void) {
  const wsBase = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1");
  const url =
    matchId === "global"
      ? `${wsBase}/live/ws/dashboard/global`
      : `${wsBase}/live/ws/${matchId}`;

  const ws = new WebSocket(url);
  ws.onmessage = (e) => {
    try { onMessage(JSON.parse(e.data)); } catch {}
  };
  // Heartbeat
  const ping = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send("ping");
  }, 30_000);
  ws.onclose = () => clearInterval(ping);
  return ws;
}
