"use client";
import { FootballStatsResult } from "@/lib/types";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  stats: FootballStatsResult;
  homeTeam: string;
  awayTeam: string;
}

function StatRow({ label, homeVal, awayVal, format = "dec" }: {
  label: string;
  homeVal: number;
  awayVal: number;
  format?: "dec" | "pct" | "int";
}) {
  const fmt = (v: number) =>
    format === "pct" ? `${(v * 100).toFixed(0)}%` :
    format === "int" ? `${Math.round(v)}` :
    v.toFixed(2);

  const maxV = Math.max(homeVal, awayVal, 0.01);
  const homeW = (homeVal / maxV) * 50;
  const awayW = (awayVal / maxV) * 50;

  return (
    <div className="grid grid-cols-3 items-center gap-2 text-xs">
      <div className="text-right">
        <span className={`font-semibold ${homeVal >= awayVal ? "text-blue-400" : "text-gray-400"}`}>
          {fmt(homeVal)}
        </span>
      </div>
      <div className="text-center flex flex-col items-center gap-1">
        <span className="text-gray-500">{label}</span>
        <div className="flex w-full h-1.5 rounded-full overflow-hidden bg-gray-800">
          <div className="ml-auto bg-blue-500 rounded-full" style={{ width: `${homeW}%` }} />
          <div className="bg-rose-500 rounded-full" style={{ width: `${awayW}%` }} />
        </div>
      </div>
      <div>
        <span className={`font-semibold ${awayVal >= homeVal ? "text-rose-400" : "text-gray-400"}`}>
          {fmt(awayVal)}
        </span>
      </div>
    </div>
  );
}

export default function StatisticsPanel({ stats, homeTeam, awayTeam }: Props) {
  const radarData = [
    { metric: "Attaque", home: stats.home_attack_strength, away: stats.away_attack_strength },
    { metric: "Défense", home: stats.home_defense_strength, away: stats.away_defense_strength },
    { metric: "Forme",   home: stats.form_home_score,       away: stats.form_away_score },
    { metric: "xG",      home: stats.expected_home_goals / 3, away: stats.expected_away_goals / 3 },
  ];

  const h2h_total = stats.h2h_home_wins + stats.h2h_draws + stats.h2h_away_wins;

  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6 space-y-5">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
        ⚽ Analyse Footballistique
      </h3>

      {/* Radar chart */}
      <div className="flex justify-center">
        <ResponsiveContainer width="100%" height={180}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#1f2937" />
            <PolarAngleAxis dataKey="metric" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <Radar name={homeTeam} dataKey="home" stroke="#60a5fa" fill="#60a5fa" fillOpacity={0.2} />
            <Radar name={awayTeam} dataKey="away" stroke="#f87171" fill="#f87171" fillOpacity={0.2} />
            <Tooltip
              contentStyle={{ background: "#111827", border: "1px solid #374151", fontSize: "11px" }}
              formatter={(v: number) => v.toFixed(3)}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Header teams */}
      <div className="grid grid-cols-3 text-xs font-semibold">
        <span className="text-blue-400 text-right pr-2">{homeTeam}</span>
        <span className="text-gray-500 text-center">Statistique</span>
        <span className="text-rose-400 pl-2">{awayTeam}</span>
      </div>

      <div className="space-y-3">
        <StatRow label="xG attendus"      homeVal={stats.expected_home_goals} awayVal={stats.expected_away_goals} />
        <StatRow label="Att. force"        homeVal={stats.home_attack_strength} awayVal={stats.away_attack_strength} />
        <StatRow label="Déf. force"        homeVal={stats.home_defense_strength} awayVal={stats.away_defense_strength} />
        <StatRow label="Forme récente"     homeVal={stats.form_home_score} awayVal={stats.form_away_score} format="pct" />
      </div>

      {/* H2H */}
      {h2h_total > 0 && (
        <div className="pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
            H2H — {h2h_total} matchs | Moy. {stats.h2h_avg_goals.toFixed(1)} buts
          </p>
          <div className="flex items-center gap-2">
            <span className="text-xs text-blue-400 w-8 text-right font-bold">{stats.h2h_home_wins}V</span>
            <div className="flex-1 flex h-3 rounded-full overflow-hidden bg-gray-800">
              <div className="bg-blue-500" style={{ width: `${(stats.h2h_home_wins / h2h_total) * 100}%` }} />
              <div className="bg-gray-500" style={{ width: `${(stats.h2h_draws / h2h_total) * 100}%` }} />
              <div className="bg-rose-500" style={{ width: `${(stats.h2h_away_wins / h2h_total) * 100}%` }} />
            </div>
            <span className="text-xs text-rose-400 w-8 font-bold">{stats.h2h_away_wins}V</span>
          </div>
          <div className="flex justify-between text-xs text-gray-600 mt-1 px-10">
            <span>{((stats.h2h_home_wins / h2h_total) * 100).toFixed(0)}%</span>
            <span>{stats.h2h_draws}N ({((stats.h2h_draws / h2h_total) * 100).toFixed(0)}%)</span>
            <span>{((stats.h2h_away_wins / h2h_total) * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
