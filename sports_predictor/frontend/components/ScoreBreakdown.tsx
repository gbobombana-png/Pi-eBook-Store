import { ScoreBreakdown as SB } from "@/lib/types";
import { pct } from "@/lib/utils";

interface Props {
  breakdown: SB;
}

const dimensions: { key: keyof SB; label: string; color: string }[] = [
  { key: "form", label: "Form", color: "bg-blue-500" },
  { key: "psychology", label: "Psychology", color: "bg-purple-500" },
  { key: "squad", label: "Squad", color: "bg-cyan-500" },
  { key: "tactics", label: "Tactics", color: "bg-amber-500" },
  { key: "advanced", label: "Advanced", color: "bg-rose-500" },
  { key: "odds", label: "Odds", color: "bg-emerald-500" },
  { key: "ml", label: "ML Model", color: "bg-brand-500" },
];

export default function ScoreBreakdown({ breakdown }: Props) {
  return (
    <div className="space-y-2">
      {dimensions.map(({ key, label, color }) => {
        const val = breakdown[key] ?? 0;
        return (
          <div key={key} className="flex items-center gap-3">
            <span className="text-xs text-slate-400 w-20 shrink-0">{label}</span>
            <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${color} transition-all duration-500`}
                style={{ width: pct(val) }}
              />
            </div>
            <span className="text-xs font-semibold text-slate-300 w-8 text-right">
              {val.toFixed(0)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
