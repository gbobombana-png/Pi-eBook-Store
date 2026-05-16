from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True)
    home_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    competition = Column(String(100))
    competition_id = Column(Integer)
    season = Column(String(10))
    round = Column(String(50))
    kickoff = Column(DateTime(timezone=True), index=True)
    venue = Column(String(100))
    city = Column(String(50))
    country = Column(String(50))
    status = Column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)

    # Result
    home_score = Column(Integer)
    away_score = Column(Integer)
    home_score_ht = Column(Integer)
    away_score_ht = Column(Integer)

    # Match stats (post-match)
    home_xg = Column(Float)
    away_xg = Column(Float)
    home_shots = Column(Integer)
    away_shots = Column(Integer)
    home_shots_on = Column(Integer)
    away_shots_on = Column(Integer)
    home_possession = Column(Float)
    away_possession = Column(Float)
    home_corners = Column(Integer)
    away_corners = Column(Integer)
    home_yellow = Column(Integer)
    away_yellow = Column(Integer)
    home_red = Column(Integer)
    away_red = Column(Integer)

    # Context
    weather = Column(String(50))
    temperature = Column(Float)
    referee = Column(String(100))
    attendance = Column(Integer)

    extra_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    home_team = relationship("Team", foreign_keys=[home_team_id], back_populates="home_matches")
    away_team = relationship("Team", foreign_keys=[away_team_id], back_populates="away_matches")
    predictions = relationship("Prediction", back_populates="match")
