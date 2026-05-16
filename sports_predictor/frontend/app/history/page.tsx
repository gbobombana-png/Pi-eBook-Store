"use client";

import { useEffect, useState } from "react";
import { Clock, TrendingUp } from "lucide-react";
import { Ticket } from "@/lib/types";
import { formatOdds } from "@/lib/utils";
import ConfidenceBadge from "@/components/ConfidenceBadge";

const BACKEND = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface HistoryResponse {
  tickets: Ticket[];
  total: number;
}

function avgConf(ticket: Ticket): number {
  if (!ticket.bets.length) return 0;
  return Math.round(ticket.bets.reduce((s, b) => s + b.confidence, 0) / ticket.bets.length);
}

export default function HistoryPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${BACKEND}/api/v1/predictions/history?limit=50`);
        if (!res.ok) throw new Error("fetch failed");
        const data: HistoryResponse = await res.json();
        setTickets(data.tickets || []);
      } catch {
        setError("Failed to load history. Make sure the backend is running.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const totalPotential = tickets.reduce((s, t) => s + t.potential_gain, 0);
  const avgOdds =
    tickets.length > 0
      ? tickets.reduce((s, t) => s + t.total_odds, 0) / tickets.length
      : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2 mb-8">
        <Clock className="w-6 h-6 text-brand-400" />
        Prediction History
      </h1>

      {!loading && tickets.length > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card text-center">
            <p className="stat-label mb-1">Total Tickets</p>
            <p className="stat-value">{tickets.length}</p>
          </div>
          <div className="card text-center">
            <p className="stat-label mb-1">Avg Odds</p>
            <p className="stat-value">{formatOdds(avgOdds)}x</p>
          </div>
          <div className="card text-center">
            <p className="stat-label mb-1">Total Potential</p>
            <p className="stat-value flex items-center justify-center gap-1">
              <TrendingUp className="w-4 h-4 text-brand-400" />
              {formatOdds(totalPotential)}u
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="card border-rose-500/30 bg-rose-500/5 text-rose-300 text-sm p-4 mb-6">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-14 bg-slate-700/40 rounded" />
            </div>
          ))}
        </div>
      )}

      {!loading && tickets.length === 0 && !error && (
        <div className="card text-center py-12">
          <Clock className="w-8 h-8 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400">No ticket history yet</p>
          <p className="text-sm text-slate-600 mt-1">
            Generate predictions daily and results will appear here
          </p>
        </div>
      )}

      {!loading && tickets.length > 0 && (
        <div className="space-y-3">
          {tickets.map((ticket, i) => (
            <div key={`${ticket.ticket_number}-${i}`} className="card flex items-center gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-brand-500/15 text-brand-400 flex items-center justify-center text-xs font-bold border border-brand-500/20">
                #{ticket.ticket_number}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-semibold text-sm text-slate-100">{ticket.label}</span>
                </div>
                <div className="text-xs text-slate-500">
                  {ticket.bets.length} selections · Stake {ticket.stake}u
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <ConfidenceBadge value={avgConf(ticket)} size="sm" />
                <span className="text-amber-400 font-bold text-sm">
                  {formatOdds(ticket.total_odds)}x
                </span>
                <span className="text-brand-400 text-xs font-semibold">
                  +{formatOdds(ticket.potential_gain)}u
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
