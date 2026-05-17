from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ── Odds ────────────────────────────────────────────────────────────────────

class OddsSnapshotIn(BaseModel):
    bookmaker: str
    odds_home: float = Field(gt=1.0)
    odds_draw: float = Field(gt=1.0)
    odds_away: float = Field(gt=1.0)
    odds_over25: float | None = None
    odds_under25: float | None = None
    odds_btts_yes: float | None = None
    odds_btts_no: float | None = None
    volume_home: float | None = None
    volume_draw: float | None = None
    volume_away: float | None = None
    is_live: bool = False
    match_minute: int | None = None


class OddsSnapshotOut(OddsSnapshotIn):
    id: int
    match_id: int
    timestamp: datetime
    class Config: from_attributes = True


# ── Match ────────────────────────────────────────────────────────────────────

class MatchCreate(BaseModel):
    external_id: str
    competition: str
    season: str
    match_date: datetime
    home_team: str
    away_team: str
    home_form: str | None = None
    away_form: str | None = None
    home_injuries: list[str] = []
    away_injuries: list[str] = []


class MatchUpdate(BaseModel):
    home_score: int | None = None
    away_score: int | None = None
    home_xg: float | None = None
    away_xg: float | None = None
    home_shots: int | None = None
    away_shots: int | None = None
    home_shots_on_target: int | None = None
    away_shots_on_target: int | None = None
    home_possession: float | None = None
    away_possession: float | None = None
    home_corners: int | None = None
    away_corners: int | None = None
    home_yellow_cards: int | None = None
    away_yellow_cards: int | None = None
    home_red_cards: int | None = None
    away_red_cards: int | None = None
    status: str | None = None


class MatchOut(BaseModel):
    id: int
    external_id: str
    competition: str
    home_team: str
    away_team: str
    match_date: datetime
    status: str
    home_score: int | None
    away_score: int | None
    home_xg: float | None
    away_xg: float | None
    home_shots: int | None
    away_shots: int | None
    home_possession: float | None
    away_possession: float | None
    home_form: str | None
    away_form: str | None
    class Config: from_attributes = True


# ── Analysis ─────────────────────────────────────────────────────────────────

class OddsAnalysisResult(BaseModel):
    opening_home: float | None
    opening_away: float | None
    current_home: float
    current_away: float
    movement_home_pct: float
    movement_away_pct: float
    is_sharp_move: bool
    sharp_direction: str | None          # "home" | "away" | None
    volume_anomaly: bool
    volume_multiplier: float
    market_inversion: bool               # si le favori a changé
    bookmaker_consensus_pct: float
    suspicion_contribution: float        # 0-25 pts vers le score global


class FootballStatsResult(BaseModel):
    home_attack_strength: float
    away_attack_strength: float
    home_defense_strength: float
    away_defense_strength: float
    expected_home_goals: float           # λ pour Poisson
    expected_away_goals: float
    h2h_home_wins: int
    h2h_draws: int
    h2h_away_wins: int
    h2h_avg_goals: float
    form_home_score: float               # 0-1
    form_away_score: float
    home_advantage_factor: float
    suspicion_contribution: float        # 0-25 pts


class ModelPrediction(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str
    prob_home: float
    prob_draw: float
    prob_away: float
    predicted_home_score: int
    predicted_away_score: int
    exact_score_prob: float
    confidence: float


class EnsembleResult(BaseModel):
    model_config = {"protected_namespaces": ()}
    prob_home: float
    prob_draw: float
    prob_away: float
    predicted_home_score: int
    predicted_away_score: int
    exact_score_probability: float
    prob_over25: float
    prob_btts: float
    prob_ht_home_lead: float
    prob_late_goal: float
    model_agreement: float
    predictions: list[ModelPrediction]


class SuspicionFlag(BaseModel):
    code: str
    description: str
    severity: str                        # "low" | "medium" | "high" | "critical"
    score_contribution: float


class SuspicionResult(BaseModel):
    score: float = Field(ge=0, le=100)
    level: str                           # "low" | "medium" | "high" | "critical"
    flags: list[SuspicionFlag]
    similar_suspect_matches: list[str]
    risk_assessment: str


class FullAnalysisResponse(BaseModel):
    match: MatchOut
    odds_analysis: OddsAnalysisResult
    football_stats: FootballStatsResult
    prediction: EnsembleResult
    suspicion: SuspicionResult
    predicted_winner: str
    prediction_confidence: float
    analysis_timestamp: datetime

    # Marchés lisibles
    markets: dict[str, Any]


# ── Live ─────────────────────────────────────────────────────────────────────

class LiveUpdatePayload(BaseModel):
    match_id: int
    minute: int
    home_score: int
    away_score: int
    event: str | None = None
    prob_home: float
    prob_draw: float
    prob_away: float
    suspicion_delta: float
    alert: str | None = None


# ── Dashboard ────────────────────────────────────────────────────────────────

class DashboardMatchCard(BaseModel):
    match_id: int
    home_team: str
    away_team: str
    match_date: datetime
    competition: str
    status: str
    suspicion_score: float
    suspicion_level: str
    predicted_winner: str
    prediction_confidence: float
    prob_home: float
    prob_draw: float
    prob_away: float
    predicted_score: str
    key_flags: list[str]
