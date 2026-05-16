"use client";

import { useEffect, useState } from "react";
import { Activity, AlertTriangle, RefreshCw } from "lucide-react";
import { getUpcomingMatches } from "@/lib/api";
import { formatDate, formatTime } from "@/lib/utils";

interface Match {
  fixture_id: number;
  home_team: string;
  away_team: string;
  league: string;
  match_time: string;
  venue?: string;
  home_odds?: number;
  draw_odds?: number;
  away_odds?: number;
}

const leagueColors: Record<string, string> = {
  "Premier League": "bg-purple-500/20 text-purple-400",
  "La Liga": "bg-red-500/20 text-red-400",
  "Ligue 1": "bg-blue-500/20 text-blue-400",
  Bundesliga: "bg-amber-500/20 text-amber-400",
  "Serie A": "bg-green-500/20 text-green-400",
  "Champions League": "bg-cyan-500/20 text-cyan-400",
};

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUpcomingMatches();
      setMatches(data as Match[]);
    } catch {
      setError("Failed to load upcoming matches.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const grouped = matches.reduce<Record<string, Match[]>>((acc, m) => {
    const key = m.league || "Other";
    if (!acc[key]) acc[key] = [];
    acc[key].push(m);
    return acc;
  }, {});

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Activity className="w-6 h-6 text-brand-400" />
          Upcoming Matches
        </h1>
        <button onClick={load} disabled={loading} className="btn-ghost flex items-center gap-1.5">
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="card border-rose-500/30 bg-rose-500/5 flex items-start gap-3 mb-6">
          <AlertTriangle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <p className="text-sm text-rose-300">{error}</p>
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="flex gap-3 items-center">
                <div className="h-3 bg-slate-700 rounded w-24" />
                <div className="h-4 bg-slate-700 rounded flex-1" />
                <div className="h-3 bg-slate-700 rounded w-16" />
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && Object.keys(grouped).length === 0 && !error && (
        <div className="card text-center py-12">
          <Activity className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No upcoming matches found</p>
        </div>
      )}

      {!loading && (
        <div className="space-y-6">
          {Object.entries(grouped).map(([league, leagueMatches]) => (
            <div key={league}>
              <div className="flex items-center gap-2 mb-3">
                <span
                  className={`badge ${leagueColors[league] || "bg-slate-700 text-slate-300"}`}
                >
                  {league}
                </span>
                <span className="text-xs text-slate-600">{leagueMatches.length} matches</span>
              </div>

              <div className="space-y-2">
                {leagueMatches.map((m) => (
                  <div key={m.fixture_id} className="card-sm">
                    <div className="flex items-center gap-4">
                      <div className="text-xs text-slate-500 w-16 shrink-0">
                        <div>{formatDate(m.match_time)}</div>
                        <div className="font-medium text-slate-400">{formatTime(m.match_time)}</div>
                      </div>

                      <div className="flex-1 grid grid-cols-3 gap-2 items-center text-sm">
                        <span className="text-right font-medium text-slate-200 truncate">
                          {m.home_team}
                        </span>
                        <span className="text-center text-xs text-slate-600 font-bold">VS</span>
                        <span className="text-left font-medium text-slate-200 truncate">
                          {m.away_team}
                        </span>
                      </div>

                      {m.home_odds && (
                        <div className="flex items-center gap-2 text-xs text-slate-500 shrink-0">
                          <span className="font-mono">{m.home_odds.toFixed(2)}</span>
                          <span className="font-mono">{m.draw_odds?.toFixed(2)}</span>
                          <span className="font-mono">{m.away_odds?.toFixed(2)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
