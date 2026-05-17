"use client";
import { DashboardMatchCard, SuspicionLevel } from "@/lib/types";
import { format } from "date-fns";
import Link from "next/link";

const LEVEL_BADGE: Record<SuspicionLevel, string> = {
  low:      "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  medium:   "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  high:     "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
};

const STATUS_DOT: Record<string, string> = {
  live:      "bg-emerald-400 animate-pulse",
  scheduled: "bg-blue-400",
  finished:  "bg-gray-500",
  cancelled: "bg-red-500",
};

interface Props {
  match: DashboardMatchCard;
}

export default function MatchCard({ match }: Props) {
  const lvl = match.suspicion_level as SuspicionLevel;

  return (
    <Link href={`/matches/${match.match_id}`}>
      <div className="rounded-2xl bg-gray-900 border border-gray-800 hover:border-gray-700 hover:bg-gray-900/80 transition-all duration-200 p-5 cursor-pointer group">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${STATUS_DOT[match.status] || "bg-gray-500"}`} />
            <span className="text-xs text-gray-500">{match.competition}</span>
          </div>
          <span className="text-xs text-gray-600">
            {format(new Date(match.match_date), "dd/MM HH:mm")}
          </span>
        </div>

        {/* Teams + score */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{match.home_team}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Dom. · {(match.prob_home * 100).toFixed(0)}%
            </p>
          </div>
          <div className="text-center px-4">
            <p className="text-xl font-black text-white tabular-nums">
              {match.predicted_score}
            </p>
            <p className="text-xs text-gray-600 mt-0.5">prédit</p>
          </div>
          <div className="flex-1 text-right">
            <p className="text-sm font-semibold text-white">{match.away_team}</p>
            <p className="text-xs text-gray-500 mt-0.5">
              Ext. · {(match.prob_away * 100).toFixed(0)}%
            </p>
          </div>
        </div>

        {/* Proba bars */}
        <div className="flex gap-1 h-1.5 rounded-full overflow-hidden mb-4">
          <div className="bg-blue-500 rounded-full transition-all" style={{ width: `${match.prob_home * 100}%` }} />
          <div className="bg-gray-600 rounded-full transition-all" style={{ width: `${match.prob_draw * 100}%` }} />
          <div className="bg-rose-500 rounded-full transition-all" style={{ width: `${match.prob_away * 100}%` }} />
        </div>

        {/* Bottom row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Suspicion score */}
            <div className={`flex items-center gap-1.5 border rounded-full px-2.5 py-1 text-xs font-semibold ${LEVEL_BADGE[lvl]}`}>
              <span>🔍</span>
              <span>{match.suspicion_score.toFixed(0)}/100</span>
            </div>
            {/* Confidence */}
            <span className="text-xs text-gray-500">
              conf. <span className="text-gray-300 font-medium">{match.prediction_confidence.toFixed(0)}%</span>
            </span>
          </div>
          <span className="text-xs text-indigo-400 font-medium group-hover:text-indigo-300 transition-colors">
            Analyser →
          </span>
        </div>

        {/* Key flags */}
        {match.key_flags.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-800">
            {match.key_flags.slice(0, 2).map((f, i) => (
              <p key={i} className="text-xs text-orange-400/70 flex items-center gap-1">
                <span>⚠</span> {f}
              </p>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
