"use client";
import { SuspicionFlag, SuspicionLevel } from "@/lib/types";

const LEVEL_CONFIG: Record<SuspicionLevel, { label: string; color: string; bg: string; ring: string }> = {
  low:      { label: "FAIBLE",    color: "text-emerald-400", bg: "bg-emerald-500", ring: "ring-emerald-500/30" },
  medium:   { label: "MODÉRÉ",    color: "text-yellow-400",  bg: "bg-yellow-500",  ring: "ring-yellow-500/30"  },
  high:     { label: "ÉLEVÉ",     color: "text-orange-400",  bg: "bg-orange-500",  ring: "ring-orange-500/30"  },
  critical: { label: "CRITIQUE",  color: "text-red-400",     bg: "bg-red-500",     ring: "ring-red-500/30"     },
};

const SEVERITY_DOT: Record<string, string> = {
  low: "bg-emerald-400", medium: "bg-yellow-400", high: "bg-orange-400", critical: "bg-red-500",
};

interface Props {
  score: number;
  level: SuspicionLevel;
  flags: SuspicionFlag[];
  riskAssessment: string;
  similarMatches?: string[];
}

export default function SuspicionMeter({ score, level, flags, riskAssessment, similarMatches = [] }: Props) {
  const cfg = LEVEL_CONFIG[level];

  // Arc SVG gauge
  const r = 54;
  const circ = Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <div className={`rounded-2xl bg-gray-900 border border-gray-800 ring-2 ${cfg.ring} p-6`}>
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest mb-4">
        🔍 Suspicion Engine
      </h3>

      {/* Arc gauge */}
      <div className="flex flex-col items-center mb-6">
        <svg width="140" height="80" viewBox="0 0 140 80">
          {/* Background arc */}
          <path
            d="M 10 75 A 60 60 0 0 1 130 75"
            fill="none" stroke="#1f2937" strokeWidth="12" strokeLinecap="round"
          />
          {/* Score arc */}
          <path
            d="M 10 75 A 60 60 0 0 1 130 75"
            fill="none"
            stroke={level === "critical" ? "#ef4444" : level === "high" ? "#f97316" : level === "medium" ? "#eab308" : "#10b981"}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            style={{ transition: "stroke-dasharray 0.8s ease" }}
          />
          {/* Score text */}
          <text x="70" y="68" textAnchor="middle" fill="white" fontSize="26" fontWeight="bold">
            {score.toFixed(0)}
          </text>
          <text x="70" y="76" textAnchor="middle" fill="#9ca3af" fontSize="9">/ 100</text>
        </svg>

        <span className={`text-xs font-bold px-3 py-1 rounded-full ${cfg.bg} text-white mt-2`}>
          RISQUE {cfg.label}
        </span>
      </div>

      {/* Risk assessment */}
      <p className={`text-xs ${cfg.color} mb-4 text-center`}>{riskAssessment}</p>

      {/* Flags */}
      {flags.length > 0 && (
        <div className="space-y-2 mb-4">
          <p className="text-xs text-gray-500 uppercase tracking-wider">Anomalies détectées</p>
          {flags.map((f, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${SEVERITY_DOT[f.severity] || "bg-gray-500"}`} />
              <div>
                <span className="text-gray-300">{f.description}</span>
                <span className="ml-1 text-gray-600">(+{f.score_contribution.toFixed(0)}pts)</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Similar matches */}
      {similarMatches.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Patterns similaires</p>
          {similarMatches.map((m, i) => (
            <p key={i} className="text-xs text-orange-400 flex items-center gap-1">
              <span>⚡</span> {m}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
