"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Target, TrendingUp } from "lucide-react";
import { Bet } from "@/lib/types";
import { betTypeLabel, confidenceColor, formatOdds, formatTime, pct } from "@/lib/utils";
import ConfidenceBadge from "./ConfidenceBadge";
import ScoreBreakdown from "./ScoreBreakdown";

interface Props {
  bet: Bet;
  index: number;
}

function splitTeams(match: string): [string, string] {
  const parts = match.split(" vs ");
  return [parts[0] ?? match, parts[1] ?? ""];
}

export default function BetCard({ bet, index }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [home, away] = splitTeams(bet.match);
  const reasoningLines = bet.reasoning.split(/[.•\n]+/).filter((s) => s.trim().length > 2);
  const riskLines = bet.risks.split(/[.•\n]+/).filter((s) => s.trim().length > 2);

  return (
    <div className="card-sm">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-brand-500/20 text-brand-400 flex items-center justify-center text-xs font-bold">
          {index + 1}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <p className="font-semibold text-sm text-slate-100 truncate">
              {home} vs {away}
            </p>
            <span className="text-xs text-slate-500 shrink-0">{formatTime(bet.kickoff)}</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="badge bg-brand-500/15 text-brand-400 border border-brand-500/30">
              {betTypeLabel(bet.bet_type)}
            </span>
            <ConfidenceBadge value={bet.confidence} size="sm" />
            <span className="text-xs text-slate-400">
              Edge{" "}
              <span className={`font-semibold ${confidenceColor(bet.value_edge * 100)}`}>
                +{(bet.value_edge * 100).toFixed(1)}%
              </span>
            </span>
          </div>

          <div className="flex items-center gap-4 text-xs text-slate-500 mb-3">
            <span className="flex items-center gap-1">
              <TrendingUp className="w-3 h-3" />
              {formatOdds(bet.odds)}x
            </span>
            <span className="flex items-center gap-1">
              <Target className="w-3 h-3" />
              {(bet.prob_home * 100).toFixed(0)}% H ·{" "}
              {(bet.prob_draw * 100).toFixed(0)}% D ·{" "}
              {(bet.prob_away * 100).toFixed(0)}% A
            </span>
          </div>

          <div className="flex items-center gap-2 mb-2">
            {(
              [
                ["home", bet.prob_home, "bg-blue-500"],
                ["draw", bet.prob_draw, "bg-amber-500"],
                ["away", bet.prob_away, "bg-rose-500"],
              ] as const
            ).map(([side, p, color]) => (
              <div key={side} className="flex-1">
                <div className="h-1 rounded-full bg-slate-700 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${color}`}
                    style={{ width: pct(p * 100) }}
                  />
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors mt-1"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {expanded ? "Hide" : "Show"} analysis
          </button>

          {expanded && (
            <div className="mt-3 space-y-3 border-t border-slate-700/50 pt-3">
              {bet.score_breakdown && (
                <>
                  <p className="section-title">Score Breakdown</p>
                  <ScoreBreakdown breakdown={bet.score_breakdown} />
                </>
              )}

              {reasoningLines.length > 0 && (
                <div>
                  <p className="section-title">Reasoning</p>
                  <ul className="space-y-1">
                    {reasoningLines.map((r, i) => (
                      <li key={i} className="text-xs text-slate-400 flex items-start gap-1.5">
                        <span className="text-brand-400 mt-0.5">✓</span>
                        {r.trim()}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {riskLines.length > 0 && (
                <div>
                  <p className="section-title">Risks</p>
                  <ul className="space-y-1">
                    {riskLines.map((r, i) => (
                      <li key={i} className="text-xs text-slate-400 flex items-start gap-1.5">
                        <span className="text-rose-400 mt-0.5">⚠</span>
                        {r.trim()}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
