"use client";
import { EnsembleResult, ModelPrediction } from "@/lib/types";

interface Props {
  prediction: EnsembleResult;
  homeTeam: string;
  awayTeam: string;
  winner: string;
  confidence: number;
  markets: Record<string, unknown>;
}

function ProbBar({ label, prob, color }: { label: string; prob: number; color: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-400">{label}</span>
        <span className="font-bold text-white">{(prob * 100).toFixed(1)}%</span>
      </div>
      <div className="h-2 rounded-full bg-gray-800">
        <div
          className={`h-2 rounded-full ${color} transition-all duration-700`}
          style={{ width: `${prob * 100}%` }}
        />
      </div>
    </div>
  );
}

function MarketBadge({ label, prob, highlight }: { label: string; prob: number; highlight?: boolean }) {
  const pct = (prob * 100).toFixed(0);
  const isHigh = prob >= 0.65;
  return (
    <div className={`rounded-xl p-3 border ${isHigh ? "border-indigo-500/40 bg-indigo-500/10" : "border-gray-800 bg-gray-900"}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${isHigh ? "text-indigo-400" : "text-white"}`}>{pct}%</p>
    </div>
  );
}

const MODEL_COLORS: Record<string, string> = {
  poisson: "bg-blue-500",
  xgboost: "bg-purple-500",
  neural:  "bg-cyan-500",
  neural_analytical: "bg-cyan-600",
  xgboost_analytical: "bg-purple-600",
};

export default function PredictionPanel({ prediction, homeTeam, awayTeam, winner, confidence, markets }: Props) {
  const m = markets as Record<string, { prob?: number; score?: string; team?: string }>;

  return (
    <div className="space-y-5">
      {/* Winner + score */}
      <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
          🎯 Prédiction IA
        </h3>

        {/* Vainqueur */}
        <div className="text-center mb-6">
          <p className="text-xs text-gray-500 mb-1">Vainqueur probable</p>
          <p className="text-2xl font-black text-white">{winner}</p>
          <div className="flex items-center justify-center gap-2 mt-2">
            <span className="text-xs text-gray-500">Confiance</span>
            <span className="text-sm font-bold text-indigo-400">{confidence.toFixed(1)}%</span>
            <span className="text-xs text-gray-500">| Accord modèles</span>
            <span className="text-sm font-bold text-indigo-400">{(prediction.model_agreement * 100).toFixed(0)}%</span>
          </div>
        </div>

        {/* Score prédit */}
        <div className="flex items-center justify-center gap-4 mb-6 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
          <span className="text-sm font-semibold text-gray-300">{homeTeam}</span>
          <span className="text-3xl font-black text-white tabular-nums">
            {prediction.predicted_home_score} : {prediction.predicted_away_score}
          </span>
          <span className="text-sm font-semibold text-gray-300">{awayTeam}</span>
        </div>
        <p className="text-center text-xs text-gray-500">
          Prob. score exact: {(prediction.exact_score_probability * 100).toFixed(1)}%
        </p>

        {/* Barres probabilités */}
        <div className="space-y-3 mt-6">
          <ProbBar label={`Victoire ${homeTeam}`} prob={prediction.prob_home} color="bg-blue-500" />
          <ProbBar label="Match nul"              prob={prediction.prob_draw}  color="bg-gray-500" />
          <ProbBar label={`Victoire ${awayTeam}`} prob={prediction.prob_away}  color="bg-rose-500" />
        </div>
      </div>

      {/* Marchés */}
      <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
          📊 Marchés
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <MarketBadge label="Over 2.5 buts"  prob={prediction.prob_over25} />
          <MarketBadge label="Under 2.5 buts" prob={1 - prediction.prob_over25} />
          <MarketBadge label="BTTS Oui"        prob={prediction.prob_btts} />
          <MarketBadge label="BTTS Non"        prob={1 - prediction.prob_btts} />
          <MarketBadge label="1ère MT domicile" prob={prediction.prob_ht_home_lead} />
          <MarketBadge label="But tardif (+75')" prob={prediction.prob_late_goal} />
        </div>
      </div>

      {/* Détail par modèle */}
      <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
          🤖 Détail des modèles
        </h3>
        <div className="space-y-3">
          {prediction.predictions.map((mp) => (
            <div key={mp.model_name} className="flex items-center gap-3">
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${MODEL_COLORS[mp.model_name] || "bg-gray-500"}`} />
              <span className="text-xs text-gray-400 w-24 capitalize">{mp.model_name}</span>
              <div className="flex-1 flex gap-2 text-xs">
                <span className="text-blue-400">{(mp.prob_home * 100).toFixed(0)}%</span>
                <span className="text-gray-500">{(mp.prob_draw * 100).toFixed(0)}%</span>
                <span className="text-rose-400">{(mp.prob_away * 100).toFixed(0)}%</span>
              </div>
              <span className="text-xs text-gray-600">
                {mp.predicted_home_score}:{mp.predicted_away_score}
              </span>
              <span className="text-xs text-gray-600">
                conf: {(mp.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
