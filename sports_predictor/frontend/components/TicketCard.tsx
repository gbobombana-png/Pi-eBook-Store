"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Star } from "lucide-react";
import { Ticket } from "@/lib/types";
import { formatOdds } from "@/lib/utils";
import BetCard from "./BetCard";
import ConfidenceBadge from "./ConfidenceBadge";

interface Props {
  ticket: Ticket;
  rank: number;
}

function avgConfidence(ticket: Ticket): number {
  if (!ticket.bets.length) return 0;
  return Math.round(ticket.bets.reduce((s, b) => s + b.confidence, 0) / ticket.bets.length);
}

export default function TicketCard({ ticket, rank }: Props) {
  const [open, setOpen] = useState(rank === 1);
  const conf = avgConfidence(ticket);

  return (
    <div className="card">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-3 text-left"
      >
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500/30 to-brand-600/10 text-brand-300 flex items-center justify-center font-bold text-sm border border-brand-500/20">
          #{rank}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className="font-semibold text-slate-100">{ticket.label}</span>
            {open ? (
              <ChevronUp className="w-4 h-4 text-slate-500 shrink-0" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-500 shrink-0" />
            )}
          </div>

          <div className="flex items-center flex-wrap gap-3 text-sm">
            <span className="flex items-center gap-1 font-bold text-amber-400">
              <Star className="w-3.5 h-3.5" />
              {formatOdds(ticket.total_odds)}x
            </span>
            <ConfidenceBadge value={conf} size="sm" />
            <span className="text-slate-500 text-xs">
              Stake {ticket.stake}u · Potential{" "}
              <span className="text-brand-400 font-semibold">
                {formatOdds(ticket.potential_gain)}u
              </span>
            </span>
            <span className="text-slate-500 text-xs">{ticket.bets.length} selections</span>
          </div>
        </div>
      </button>

      {open && (
        <div className="mt-4 space-y-3 border-t border-slate-700/40 pt-4">
          {ticket.bets.map((bet, i) => (
            <BetCard key={`${bet.fixture_id}-${i}`} bet={bet} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
