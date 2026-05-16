from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, Text, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class PredictionResult(str, enum.Enum):
    PENDING = "pending"
    WIN = "win"
    LOSS = "loss"
    VOID = "void"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    fixture_id = Column(Integer, index=True)
    match_label = Column(String(200))
    competition = Column(String(100))
    kickoff = Column(DateTime(timezone=True))
    bet_type = Column(String(20), nullable=False)
    odds = Column(Float, nullable=False)
    confidence = Column(Integer, nullable=False)
    value_edge = Column(Float)
    prob_home = Column(Float)
    prob_draw = Column(Float)
    prob_away = Column(Float)
    prob_btts = Column(Float)
    prob_over25 = Column(Float)
    reasoning = Column(Text)
    risks = Column(Text)
    score_breakdown = Column(JSON, default={})
    key_stats = Column(JSON, default={})
    result = Column(Enum(PredictionResult, native_enum=False), default=PredictionResult.PENDING)
    actual_home_score = Column(Integer)
    actual_away_score = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ticket = relationship("Ticket", back_populates="predictions")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(Integer)
    label = Column(String(100))
    target_date = Column(Date, index=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_odds = Column(Float)
    stake = Column(Float, default=1.0)
    potential_gain = Column(Float)
    result = Column(Enum(PredictionResult, native_enum=False), default=PredictionResult.PENDING)
    resolved_at = Column(DateTime(timezone=True))

    predictions = relationship("Prediction", back_populates="ticket", lazy="selectin")
