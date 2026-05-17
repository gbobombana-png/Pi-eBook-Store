"use client";
import { useEffect, useState } from "react";
import { api, createMatchWebSocket } from "@/lib/api";
import { DashboardMatchCard, LiveUpdate } from "@/lib/types";
import MatchCard from "@/components/MatchCard";

const STAT_CARDS = [
  { icon: "🗓", label: "Matchs analysés", key: "total",     color: "text-indigo-400" },
  { icon: "🚨", label: "Alertes critiques", key: "critical", color: "text-red-400"    },
  { icon: "⚠️", label: "Risque élevé",     key: "high",     color: "text-orange-400" },
  { icon: "⚡", label: "En direct",         key: "live",     color: "text-emerald-400"},
];

export default function Dashboard() {
  const [matches, setMatches] = useState<DashboardMatchCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [globalAlerts, setGlobalAlerts] = useState<string[]>([]);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    api.listMatches({ limit: 50 })
      .then(setMatches)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Global WebSocket pour alertes dashboard
  useEffect(() => {
    try {
      const ws = createMatchWebSocket("global", (data) => {
        const d = data as LiveUpdate;
        if (d.type === "SUSPICION_ALERT" || d.type === "LIVE_ALERT") {
          const msg = (d as unknown as { message?: string; alert?: string }).message
                   || (d as unknown as { alert?: string }).alert || "";
          if (msg) setGlobalAlerts((prev) => [msg, ...prev].slice(0, 5));
        }
      });
      ws.onopen  = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      return () => ws.close();
    } catch {
      // WebSocket non disponible en dev
    }
  }, []);

  const stats = {
    total:    matches.length,
    critical: matches.filter((m) => m.suspicion_level === "critical").length,
    high:     matches.filter((m) => m.suspicion_level === "high").length,
    live:     matches.filter((m) => m.status === "live").length,
  };

  const filtered = matches.filter((m) => {
    if (filter === "all")      return true;
    if (filter === "live")     return m.status === "live";
    if (filter === "critical") return m.suspicion_level === "critical";
    if (filter === "high")     return ["high", "critical"].includes(m.suspicion_level);
    return true;
  });

  return (
    <div className="p-6 space-y-8 max-w-screen-2xl mx-auto">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Football AI Platform</h1>
          <p className="text-sm text-gray-500 mt-1">
            Analyse prédictive · Détection de matchs suspects · Temps réel
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-400 animate-pulse" : "bg-gray-600"}`} />
          <span className="text-xs text-gray-500">{wsConnected ? "Live connecté" : "Hors ligne"}</span>
        </div>
      </div>

      {/* Global alerts */}
      {globalAlerts.length > 0 && (
        <div className="space-y-2">
          {globalAlerts.map((a, i) => (
            <div key={i} className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-sm text-red-400">
              {a}
            </div>
          ))}
        </div>
      )}

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STAT_CARDS.map((s) => (
          <div key={s.key} className="rounded-2xl bg-gray-900 border border-gray-800 p-5">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">{s.icon}</span>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
            <p className={`text-3xl font-black ${s.color}`}>
              {stats[s.key as keyof typeof stats]}
            </p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { id: "all",      label: "Tous" },
          { id: "live",     label: "⚡ Live" },
          { id: "critical", label: "🚨 Critiques" },
          { id: "high",     label: "⚠️ Élevé" },
        ].map((f) => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              filter === f.id
                ? "bg-indigo-600 text-white"
                : "bg-gray-900 border border-gray-800 text-gray-400 hover:text-white hover:border-gray-700"
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="ml-auto text-xs text-gray-600 self-center">
          {filtered.length} match{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Match grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-2xl bg-gray-900 border border-gray-800 h-48 animate-pulse" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-600">
          <p className="text-4xl mb-4">📭</p>
          <p>Aucun match disponible pour ce filtre.</p>
          <p className="text-sm mt-2">
            Utilisez <code className="bg-gray-800 px-1 rounded">/api/v1/matches</code> pour en ajouter.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((m) => (
            <MatchCard key={m.match_id} match={m} />
          ))}
        </div>
      )}
    </div>
  );
}
