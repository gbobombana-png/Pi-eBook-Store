from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Boolean, DateTime, JSON,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum
from ..core.database import Base


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class SuspicionLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(64), unique=True, index=True)
    competition = Column(String(128))
    season = Column(String(16))
    match_date = Column(DateTime)
    status = Column(SAEnum(MatchStatus), default=MatchStatus.SCHEDULED)

    home_team = Column(String(128), index=True)
    away_team = Column(String(128), index=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)

    # Stats footballistiques
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)
    home_shots = Column(Integer, nullable=True)
    away_shots = Column(Integer, nullable=True)
    home_shots_on_target = Column(Integer, nullable=True)
    away_shots_on_target = Column(Integer, nullable=True)
    home_possession = Column(Float, nullable=True)
    away_possession = Column(Float, nullable=True)
    home_corners = Column(Integer, nullable=True)
    away_corners = Column(Integer, nullable=True)
    home_fouls = Column(Integer, nullable=True)
    away_fouls = Column(Integer, nullable=True)
    home_yellow_cards = Column(Integer, nullable=True)
    away_yellow_cards = Column(Integer, nullable=True)
    home_red_cards = Column(Integer, nullable=True)
    away_red_cards = Column(Integer, nullable=True)
    home_offsides = Column(Integer, nullable=True)
    away_offsides = Column(Integer, nullable=True)

    # Composition et contexte
    home_injuries = Column(JSON, default=list)  # liste de joueurs blessés
    away_injuries = Column(JSON, default=list)
    home_form = Column(String(10))   # ex: "WWDLL"
    away_form = Column(String(10))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    odds = relationship("OddsSnapshot", back_populates="match", cascade="all, delete-orphan")
    analysis = relationship("MatchAnalysis", back_populates="match", uselist=False, cascade="all, delete-orphan")
    live_events = relationship("LiveEvent", back_populates="match", cascade="all, delete-orphan")


class OddsSnapshot(Base):
    __tablename__ = "odds_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    bookmaker = Column(String(64))
    timestamp = Column(DateTime, default=datetime.utcnow)

    odds_home = Column(Float)
    odds_draw = Column(Float)
    odds_away = Column(Float)
    odds_over25 = Column(Float, nullable=True)
    odds_under25 = Column(Float, nullable=True)
    odds_btts_yes = Column(Float, nullable=True)
    odds_btts_no = Column(Float, nullable=True)

    # Volumes (en unités normalisées)
    volume_home = Column(Float, nullable=True)
    volume_draw = Column(Float, nullable=True)
    volume_away = Column(Float, nullable=True)

    is_live = Column(Boolean, default=False)
    match_minute = Column(Integer, nullable=True)

    match = relationship("Match", back_populates="odds")


class MatchAnalysis(Base):
    __tablename__ = "match_analyses"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), unique=True, index=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Prédictions ML
    predicted_winner = Column(String(128))
    prob_home_win = Column(Float)
    prob_draw = Column(Float)
    prob_away_win = Column(Float)
    predicted_home_score = Column(Integer, nullable=True)
    predicted_away_score = Column(Integer, nullable=True)
    exact_score_prob = Column(Float, nullable=True)

    # Marchés
    prob_over25 = Column(Float)
    prob_btts = Column(Float)
    prob_ht_home = Column(Float, nullable=True)
    prob_late_goal = Column(Float, nullable=True)

    # Confiance
    prediction_confidence = Column(Float)
    model_agreement = Column(Float)  # consensus entre modèles (0-1)

    # Suspicion
    suspicion_score = Column(Float, default=0.0)
    suspicion_level = Column(SAEnum(SuspicionLevel), default=SuspicionLevel.LOW)
    suspicion_flags = Column(JSON, default=list)   # liste des alertes détectées
    similar_suspect_matches = Column(JSON, default=list)

    # Détail des modèles
    poisson_prediction = Column(JSON, nullable=True)
    xgboost_prediction = Column(JSON, nullable=True)
    neural_prediction = Column(JSON, nullable=True)
    ensemble_weights = Column(JSON, nullable=True)

    # Analyse des cotes
    odds_analysis = Column(JSON, nullable=True)

    match = relationship("Match", back_populates="analysis")


class LiveEvent(Base):
    __tablename__ = "live_events"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), index=True)
    minute = Column(Integer)
    event_type = Column(String(32))   # goal, red_card, penalty, substitution
    team = Column(String(128))
    player = Column(String(128), nullable=True)
    description = Column(Text, nullable=True)

    # Recalcul probabilités au moment de l'event
    prob_home_win_after = Column(Float, nullable=True)
    prob_draw_after = Column(Float, nullable=True)
    prob_away_win_after = Column(Float, nullable=True)
    suspicion_delta = Column(Float, nullable=True)  # variation du score suspicion

    timestamp = Column(DateTime, default=datetime.utcnow)
    match = relationship("Match", back_populates="live_events")


class TeamStats(Base):
    __tablename__ = "team_stats"

    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String(128), unique=True, index=True)
    competition = Column(String(128))
    season = Column(String(16))

    avg_goals_scored = Column(Float, default=1.5)
    avg_goals_conceded = Column(Float, default=1.5)
    avg_xg_for = Column(Float, default=1.4)
    avg_xg_against = Column(Float, default=1.4)
    attack_strength = Column(Float, default=1.0)
    defense_strength = Column(Float, default=1.0)

    home_avg_goals_scored = Column(Float, default=1.7)
    home_avg_goals_conceded = Column(Float, default=1.2)
    away_avg_goals_scored = Column(Float, default=1.2)
    away_avg_goals_conceded = Column(Float, default=1.7)

    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    form_vector = Column(JSON, default=list)  # [1,1,0,0.5,1] derniers 5 matchs

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
