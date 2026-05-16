"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Zap, TrendingUp, Star, AlertTriangle } from "lucide-react";
import { DailyTickets } from "@/lib/types";
import { getDailyPredictions, triggerGeneration } from "@/lib/api";
import { formatDate, formatOdds } from "@/lib/utils";
import { getUser } from "@/lib/auth";
import TicketCard from "@/components/TicketCard";

export default function Dashboard() {
  const [data, setData] = useState<DailyTickets | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isAdmin = getUser()?.is_admin ?? false;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDailyPredictions();
      setData(result);
    } catch {
      setError("Failed to load predictions. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await triggerGeneration();
      await load();
    } catch {
      setError("Trigger failed.");
    } finally {
      setTriggering(false);
    }
  };

  const avgOdds =
    data && data.tickets.length > 0
      ? data.tickets.reduce((s, t) => s + t.total_odds, 0) / data.tickets.length
      : 0;

  const avgConf =
    data && data.tickets.length > 0
      ? data.tickets.reduce(
          (s, t) =>
            s +
            (t.bets.length
              ? t.bets.reduce((bs, b) => bs + b.confidence, 0) / t.bets.length
              : 0),
          0
        ) / data.tickets.length
      : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1 flex items-center gap-2">
            <Zap className="w-6 h-6 text-brand-400" />
            Daily Predictions
          </h1>
          {data && (
            <p className="text-sm text-slate-500">
              {formatDate(data.generated_at)} · {data.total_tickets} tickets · {data.date}
            </p>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={load}
            disabled={loading}
            className="btn-ghost flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Actualiser
          </button>
          {isAdmin && (
          <button
            onClick={handleTrigger}
            disabled={triggering || loading}
            className="btn-primary flex items-center gap-1.5"
          >
            <Zap className="w-3.5 h-3.5" />
            {triggering ? "Génération…" : "Générer"}
          </button>
          )}
        </div>
      </div>

      {/* Stats */}
      {data && !loading && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card text-center">
            <p className="stat-label mb-1">Tickets</p>
            <p className="stat-value">{data.total_tickets}</p>
          </div>
          <div className="card text-center">
            <p className="stat-label mb-1">Avg Odds</p>
            <p className="stat-value flex items-center justify-center gap-1">
              <Star className="w-4 h-4 text-amber-400" />
              {formatOdds(avgOdds)}x
            </p>
          </div>
          <div className="card text-center">
            <p className="stat-label mb-1">Avg Confidence</p>
            <p className="stat-value flex items-center justify-center gap-1">
              <TrendingUp className="w-4 h-4 text-brand-400" />
              {avgConf.toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="card border-rose-500/30 bg-rose-500/5 flex items-start gap-3 mb-6">
          <AlertTriangle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />
          <p className="text-sm text-rose-300">{error}</p>
        </div>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="card animate-pulse">
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-slate-700" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-700 rounded w-1/3" />
                  <div className="h-3 bg-slate-700/60 rounded w-1/4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tickets */}
      {!loading && data && (
        <div className="space-y-4">
          {data.tickets.length === 0 ? (
            <div className="card text-center py-12">
              <Zap className="w-8 h-8 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-400 mb-1">No predictions yet</p>
              <p className="text-sm text-slate-600 mb-4">
                Click "Generate Now" to create today's tickets
              </p>
              <button onClick={handleTrigger} className="btn-primary mx-auto">
                Generate Predictions
              </button>
            </div>
          ) : (
            data.tickets.map((ticket, i) => (
              <TicketCard key={ticket.ticket_number} ticket={ticket} rank={i + 1} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
