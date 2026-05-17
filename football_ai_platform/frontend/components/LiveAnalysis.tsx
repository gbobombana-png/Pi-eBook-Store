"use client";
import { useEffect, useRef, useState } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { createMatchWebSocket } from "@/lib/api";
import { LiveUpdate } from "@/lib/types";

interface LivePoint {
  minute: number;
  home: number;
  draw: number;
  away: number;
  score: string;
}

interface Props {
  matchId: number;
  homeTeam: string;
  awayTeam: string;
  initialProbHome: number;
  initialProbDraw: number;
  initialProbAway: number;
}

export default function LiveAnalysis({
  matchId, homeTeam, awayTeam,
  initialProbHome, initialProbDraw, initialProbAway,
}: Props) {
  const [history, setHistory] = useState<LivePoint[]>([
    { minute: 0, home: initialProbHome, draw: initialProbDraw, away: initialProbAway, score: "0:0" },
  ]);
  const [currentScore, setCurrentScore] = useState("0:0");
  const [alerts, setAlerts] = useState<string[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = createMatchWebSocket(matchId, (data) => {
      const d = data as LiveUpdate;
      if (d.type === "pong") return;

      if (d.minute !== undefined && d.prob_home !== undefined) {
        const score = `${d.home_score ?? 0}:${d.away_score ?? 0}`;
        setCurrentScore(score);
        setHistory((prev) => [
          ...prev.slice(-90),
          { minute: d.minute!, home: d.prob_home!, draw: d.prob_draw!, away: d.prob_away!, score },
        ]);
      }
      if (d.alert) {
        setAlerts((prev) => [d.alert!, ...prev].slice(0, 10));
      }
    });
    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    wsRef.current = ws;
    return () => ws.close();
  }, [matchId]);

  const latest = history[history.length - 1];

  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
          ⚡ Analyse Live
        </h3>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-400 animate-pulse" : "bg-gray-600"}`} />
          <span className="text-xs text-gray-500">{connected ? "Connecté" : "Hors ligne"}</span>
        </div>
      </div>

      {/* Score live */}
      <div className="flex items-center justify-center gap-6 py-4">
        <span className="text-sm font-semibold text-gray-300">{homeTeam}</span>
        <span className="text-4xl font-black text-white tabular-nums tracking-widest">{currentScore}</span>
        <span className="text-sm font-semibold text-gray-300">{awayTeam}</span>
      </div>

      {/* Probabilités actuelles */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Domicile", prob: latest.home, color: "text-blue-400" },
          { label: "Nul",      prob: latest.draw, color: "text-gray-400"  },
          { label: "Extérieur",prob: latest.away, color: "text-rose-400"  },
        ].map((x) => (
          <div key={x.label} className="rounded-xl bg-gray-800 p-3">
            <p className="text-xs text-gray-500">{x.label}</p>
            <p className={`text-xl font-black ${x.color}`}>{(x.prob * 100).toFixed(1)}%</p>
          </div>
        ))}
      </div>

      {/* Graphique probabilités live */}
      <ResponsiveContainer width="100%" height={160}>
        <AreaChart data={history} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
          <defs>
            <linearGradient id="gHome" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#60a5fa" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#60a5fa" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gAway" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f87171" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="minute" tick={{ fill: "#6b7280", fontSize: 10 }} label={{ value: "min", position: "insideRight", fill: "#6b7280", fontSize: 10 }} />
          <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} domain={[0, 1]} />
          <Tooltip
            formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
            contentStyle={{ background: "#111827", border: "1px solid #374151", fontSize: "11px" }}
          />
          <Area type="monotone" dataKey="home" stroke="#60a5fa" fill="url(#gHome)" strokeWidth={2} dot={false} />
          <Area type="monotone" dataKey="draw" stroke="#6b7280" fill="none" strokeWidth={1} strokeDasharray="3 3" dot={false} />
          <Area type="monotone" dataKey="away" stroke="#f87171" fill="url(#gAway)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>

      {/* Alertes */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Alertes live</p>
          {alerts.map((a, i) => (
            <div key={i} className="text-xs bg-orange-500/10 border border-orange-500/30 text-orange-400 rounded-lg px-3 py-2">
              {a}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
