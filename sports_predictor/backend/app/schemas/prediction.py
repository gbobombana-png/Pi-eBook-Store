from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BetOut(BaseModel):
    fixture_id: int
    match: str
    competition: str
    kickoff: str
    bet_type: str
    odds: float
    confidence: int = Field(..., ge=0, le=100)
    value_edge: float
    prob_home: float
    prob_draw: float
    prob_away: float
    prob_btts: float
    prob_over25: float
    reasoning: str
    risks: str
    key_stats: dict
    score_breakdown: dict


class TicketOut(BaseModel):
    ticket_number: int
    label: str
    total_odds: float
    stake: float
    potential_gain: float
    bets: list[BetOut]


class DailyTicketsOut(BaseModel):
    date: str
    generated_at: str
    tickets: list[TicketOut]
    total_tickets: int
