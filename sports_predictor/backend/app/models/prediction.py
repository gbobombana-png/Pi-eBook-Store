from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class BetType(str, enum.Enum):
    HOME_WIN = "1"
    DRAW = "X"
    AWAY_WIN = "2"
    BTTS_YES = "BTTS_YES"
    BTTS_NO = "BTTS_NO"
    OVER_25 = "OVER_2.5"
    UNDER_25 = "UNDER_2.5"
    OVER_35 = "OVER_3.5"
    DOUBLE_CHANCE_1X = "1X"
    DOUBLE_CHANCE_X2 = "X2"
    ASIAN_HANDICAP = "AH"
    DNB = "DNB"


class PredictionResult(str, enum.Enum):
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    VOID = "void"
    HALF_WIN = "half_win"
    HALF_LOSS = "half_loss"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    bet_type = Column(Enum(BetType), nullable=False)
    odds = Column(Float, nullable=False)
    confidence = Column(Integer, nullable=False)  # 0-100

    # Analysis scores (0-100 each)
    score_form = Column(Float)
    score_psychology = Column(Float)
    score_squad = Column(Float)
    score_tactics = Column(Float)
    score_advanced = Column(Float)
    score_odds = Column(Float)
    score_ml = Column(Float)
    score_total = Column(Float)

    # Probabilities
    prob_home = Column(Float)
    prob_draw = Column(Float)
    prob_away = Column(Float)
    prob_btts = Column(Float)
    prob_over25 = Column(Float)
    implied_prob = Column(Float)   # from bookmaker odds
    value_edge = Column(Float)     # our prob - implied prob

    # Explanation
    reasoning = Column(Text)
    risks = Column(Text)
    key_stats = Column(JSON, default={})

    # Result tracking
    result = Column(Enum(PredictionResult), default=PredictionResult.PENDING)
    resolved_at = Column(DateTime(timezone=True))
    actual_home_score = Column(Integer)
    actual_away_score = Column(Integer)

    match = relationship("Match", back_populates="predictions")
    ticket = relationship("Ticket", back_populates="predictions")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    label = Column(String(50))            # e.g. "Ticket #1 — Mercredi 15 Mai"
    total_odds = Column(Float)
    stake = Column(Float, default=1.0)
    potential_gain = Column(Float)

    result = Column(Enum(PredictionResult), default=PredictionResult.PENDING)
    resolved_at = Column(DateTime(timezone=True))

    predictions = relationship("Prediction", back_populates="ticket")
