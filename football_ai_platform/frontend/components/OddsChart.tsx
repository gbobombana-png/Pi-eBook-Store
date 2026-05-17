"use client";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend,
} from "recharts";
import { OddsDataPoint } from "@/lib/types";
import { format } from "date-fns";

interface Props {
  data: OddsDataPoint[];
  homeTeam: string;
  awayTeam: string;
  sharpMove?: boolean;
  sharpDirection?: "home" | "away" | null;
}

const CustomTooltip = ({ active, payload, label }: unknown) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 text-xs shadow-xl">
      <p className="text-gray-400 mb-2">{label}</p>
      {payload.map((p: { color: string; name: string; value: number }) => (
        <p key={p.name} style={{ color: p.color }} className="flex justify-between gap-4">
          <span>{p.name}</span><span className="font-bold">{p.value?.toFixed(3)}</span>
        </p>
      ))}
    </div>
  );
};

export default function OddsChart({ data, homeTeam, awayTeam, sharpMove, sharpDirection }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    time: format(new Date(d.timestamp), "HH:mm"),
  }));

  return (
    <div className="rounded-2xl bg-gray-900 border border-gray-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
          📈 Évolution des cotes
        </h3>
        {sharpMove && (
          <span className="text-xs bg-orange-500/20 text-orange-400 border border-orange-500/30 px-2 py-1 rounded-full font-semibold">
            ⚡ Sharp move {sharpDirection === "home" ? `→ ${homeTeam}` : `→ ${awayTeam}`}
          </span>
        )}
      </div>

      {data.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-gray-600 text-sm">
          Aucune donnée de cotes disponible
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={formatted} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
            <XAxis dataKey="time" tick={{ fill: "#6b7280", fontSize: 11 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 11 }} domain={["auto", "auto"]} />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: "11px", color: "#9ca3af" }}
              formatter={(v) =>
                v === "home" ? homeTeam : v === "away" ? awayTeam : "Nul"
              }
            />
            <Line
              type="monotone" dataKey="home" stroke="#60a5fa"
              strokeWidth={2} dot={false} name="home"
            />
            <Line
              type="monotone" dataKey="draw" stroke="#6b7280"
              strokeWidth={1.5} dot={false} strokeDasharray="4 4" name="draw"
            />
            <Line
              type="monotone" dataKey="away" stroke="#f87171"
              strokeWidth={2} dot={false} name="away"
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Volume bar */}
      {data.some((d) => d.volume) && (
        <div className="mt-4">
          <p className="text-xs text-gray-500 mb-2">Volume relatif des paris</p>
          <div className="flex gap-1 items-end h-12">
            {data.slice(-20).map((d, i) => {
              const maxVol = Math.max(...data.map((x) => x.volume || 0), 1);
              const h = ((d.volume || 0) / maxVol) * 48;
              return (
                <div
                  key={i}
                  className="flex-1 bg-indigo-500/40 rounded-sm"
                  style={{ height: `${h}px` }}
                  title={`Vol: ${d.volume}`}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
