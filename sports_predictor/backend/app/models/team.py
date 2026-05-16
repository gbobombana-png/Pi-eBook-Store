from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    api_id = Column(Integer, unique=True, index=True)
    name = Column(String(100), nullable=False)
    short_name = Column(String(10))
    country = Column(String(50))
    league = Column(String(100))
    logo_url = Column(String(255))

    # Aggregated stats (updated daily)
    home_goals_scored_avg = Column(Float, default=0.0)
    home_goals_conceded_avg = Column(Float, default=0.0)
    away_goals_scored_avg = Column(Float, default=0.0)
    away_goals_conceded_avg = Column(Float, default=0.0)
    home_xg_avg = Column(Float, default=0.0)
    away_xg_avg = Column(Float, default=0.0)
    home_xga_avg = Column(Float, default=0.0)
    away_xga_avg = Column(Float, default=0.0)
    home_wins_pct = Column(Float, default=0.0)
    away_wins_pct = Column(Float, default=0.0)
    btts_pct = Column(Float, default=0.0)
    over25_pct = Column(Float, default=0.0)
    corners_avg = Column(Float, default=0.0)
    shots_on_target_avg = Column(Float, default=0.0)
    possession_avg = Column(Float, default=0.0)

    # Form (last 5 matches: W/D/L)
    form_last5 = Column(String(5))
    form_last10 = Column(String(10))

    # Elo-style rating
    elo_rating = Column(Float, default=1500.0)

    extra_data = Column(JSON, default={})
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    home_matches = relationship("Match", foreign_keys="Match.home_team_id", back_populates="home_team")
    away_matches = relationship("Match", foreign_keys="Match.away_team_id", back_populates="away_team")
