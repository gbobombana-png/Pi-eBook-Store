"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { FullAnalysisResponse, OddsDataPoint } from "@/lib/types";
import SuspicionMeter from "@/components/SuspicionMeter";
import PredictionPanel from "@/components/PredictionPanel";
import OddsChart from "@/components/OddsChart";
import StatisticsPanel from "@/components/StatisticsPanel";
import LiveAnalysis from "@/components/LiveAnalysis";
import { format } from "date-fns";

// Données de démonstration pour /api/v1/analysis/quick
const DEMO_BODY = {
  home_team: "Paris Saint-Germain",
  away_team: "Olympique de Marseille",
  competition: "Ligue 1",
  is_home_fixture: true,
  home_profile: {
    name: "Paris Saint-Germain",
    avg_goals_scored: 2.4,
    avg_goals_conceded: 0.9,
    avg_xg_for: 2.2,
    avg_xg_against: 0.95,
    home_avg_scored: 2.7,
    home_avg_conceded: 0.8,
    away_avg_scored: 2.1,
    away_avg_conceded: 1.0,
    form: "WWWDW",
    injuries: [],
    games: 28,
  },
  away_profile: {
    name: "Olympique de Marseille",
    avg_goals_scored: 1.6,
    avg_goals_conceded: 1.4,
    avg_xg_for: 1.5,
    avg_xg_against: 1.3,
    home_avg_scored: 1.8,
    home_avg_conceded: 1.1,
    away_avg_scored: 1.4,
    away_avg_conceded: 1.7,
    form: "WDLWL",
    injuries: ["Key striker"],
    games: 28,
  },
  h2h: { home_wins: 8, draws: 4, away_wins: 3, avg_goals: 2.8 },
  odds_snapshots: [
    { home: 1.72, draw: 3.60, away: 5.50, ts: Date.now() / 1000 - 86400 },
    { home: 1.68, draw: 3.70, away: 5.80, ts: Date.now() / 1000 - 43200 },
    { home: 1.63, draw: 3.80, away: 6.20, ts: Date.now() / 1000 - 3600  },
    { home: 1.58, draw: 3.90, away: 6.50, ts: Date.now() / 1000         },
  ],
};

export default function MatchDetailPage({ params }: { params: { id: string } }) {
  const [analysis, setAnalysis] = useState<FullAnalysisResponse | null>(null);
  const [oddsHistory, setOddsHistory] = useState<OddsDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isDemo = params.id === "demo";

  useEffect(() => {
    const run = async () => {
      try {
        if (isDemo) {
          const result = await api.quickAnalyze(DEMO_BODY);
          setAnalysis(result);
          // Générer historique de cotes depuis les snapshots démo
          const odds: OddsDataPoint[] = DEMO_BODY.odds_snapshots.map((s, i) => ({
            timestamp: new Date(s.ts * 1000).toISOString(),
            home: s.home,
            draw: s.draw,
            away: s.away,
          }));
          setOddsHistory(odds);
        } else {
          const matchId = parseInt(params.id);
          const [hist] = await Promise.all([
            api.getOddsHistory(matchId).catch(() => []),
          ]);
          setOddsHistory(hist);
          // L'analyse doit être déjà sauvegardée en DB ou nécessite un appel POST /analysis/match/{id}
          // Pour la démo, on utilise quick analyze avec des données fictives
          const result = await api.quickAnalyze({ ...DEMO_BODY, home_team: `Team Home ${params.id}` });
          setAnalysis(result);
        }
      } catch (e: unknown) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [params.id, isDemo]);

  if (loading) return (
    <div className="p-8 flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-gray-400">Analyse en cours…</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="p-8 text-center">
      <p className="text-red-400 mb-4">Erreur: {error}</p>
      <a href="/" className="text-indigo-400 hover:underline">← Retour au dashboard</a>
    </div>
  );

  if (!analysis) return null;

  const { match, prediction, suspicion, football_stats, odds_analysis, markets } = analysis;
  const isLive = match.status === "live";

  return (
    <div className="p-6 space-y-6 max-w-screen-2xl mx-auto">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <a href="/" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">
            ← Dashboard
          </a>
          <p className="text-xs text-gray-500 mt-1">{match.competition}</p>
          <h1 className="text-xl font-black text-white mt-1">
            {match.home_team} <span className="text-gray-500">vs</span> {match.away_team}
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            {format(new Date(match.match_date), "EEEE d MMMM yyyy · HH:mm")}
          </p>
        </div>

        {/* Match result si terminé */}
        {match.home_score !== null && (
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Résultat final</p>
            <p className="text-3xl font-black text-white tabular-nums">
              {match.home_score} : {match.away_score}
            </p>
          </div>
        )}
      </div>

      {/* Suspicion alert banner */}
      {suspicion.level === "critical" && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/40 px-4 py-3 flex items-center gap-3">
          <span className="text-xl">🚨</span>
          <div>
            <p className="text-sm font-bold text-red-400">ALERTE CRITIQUE — Match potentiellement suspect</p>
            <p className="text-xs text-red-300/70">{suspicion.risk_assessment}</p>
          </div>
          <span className="ml-auto text-2xl font-black text-red-400">{suspicion.score.toFixed(0)}/100</span>
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left: Prediction + Stats */}
        <div className="lg:col-span-2 space-y-6">
          <PredictionPanel
            prediction={prediction}
            homeTeam={match.home_team}
            awayTeam={match.away_team}
            winner={analysis.predicted_winner}
            confidence={analysis.prediction_confidence}
            markets={markets as Record<string, unknown>}
          />
          <StatisticsPanel
            stats={football_stats}
            homeTeam={match.home_team}
            awayTeam={match.away_team}
          />
          <OddsChart
            data={oddsHistory}
            homeTeam={match.home_team}
            awayTeam={match.away_team}
            sharpMove={odds_analysis.is_sharp_move}
            sharpDirection={odds_analysis.sharp_direction}
          />
        </div>

        {/* Right: Suspicion + Live */}
        <div className="space-y-6">
          <SuspicionMeter
            score={suspicion.score}
            level={suspicion.level}
            flags={suspicion.flags}
            riskAssessment={suspicion.risk_assessment}
            similarMatches={suspicion.similar_suspect_matches}
          />

          {/* Odds analysis summary */}
          <div className="rounded-2xl bg-gray-900 border border-gray-800 p-5 space-y-3">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
              📉 Marché — Résumé
            </h3>
            {[
              { label: "Mvt domicile",  val: `${odds_analysis.movement_home_pct > 0 ? "+" : ""}${odds_analysis.movement_home_pct.toFixed(1)}%`, alert: odds_analysis.is_sharp_move },
              { label: "Sharp move",    val: odds_analysis.is_sharp_move ? `Oui → ${odds_analysis.sharp_direction}` : "Non", alert: odds_analysis.is_sharp_move },
              { label: "Inversion",     val: odds_analysis.market_inversion ? "✅ Détectée" : "Non", alert: odds_analysis.market_inversion },
              { label: "Vol. anormal",  val: odds_analysis.volume_anomaly ? `×${odds_analysis.volume_multiplier.toFixed(1)}` : "Non", alert: odds_analysis.volume_anomaly },
              { label: "Consensus BK",  val: `${odds_analysis.bookmaker_consensus_pct.toFixed(0)}%`, alert: odds_analysis.bookmaker_consensus_pct < 85 },
            ].map((row) => (
              <div key={row.label} className="flex justify-between text-xs">
                <span className="text-gray-500">{row.label}</span>
                <span className={row.alert ? "text-orange-400 font-semibold" : "text-gray-300"}>
                  {row.val}
                </span>
              </div>
            ))}
          </div>

          {isLive && (
            <LiveAnalysis
              matchId={match.id}
              homeTeam={match.home_team}
              awayTeam={match.away_team}
              initialProbHome={prediction.prob_home}
              initialProbDraw={prediction.prob_draw}
              initialProbAway={prediction.prob_away}
            />
          )}
        </div>
      </div>
    </div>
  );
}
