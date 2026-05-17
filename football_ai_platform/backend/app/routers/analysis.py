from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..models.db_models import Match, MatchAnalysis, OddsSnapshot
from ..schemas.schemas import FullAnalysisResponse
from ..services import prediction_engine as pe
from ..services.football_analyzer import TeamProfile, H2HRecord

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _build_profile_from_body(data: dict) -> TeamProfile:
    return TeamProfile(
        name=data["name"],
        avg_goals_scored=data.get("avg_goals_scored", 1.5),
        avg_goals_conceded=data.get("avg_goals_conceded", 1.5),
        avg_xg_for=data.get("avg_xg_for", 1.4),
        avg_xg_against=data.get("avg_xg_against", 1.4),
        home_avg_scored=data.get("home_avg_scored", 1.7),
        home_avg_conceded=data.get("home_avg_conceded", 1.2),
        away_avg_scored=data.get("away_avg_scored", 1.2),
        away_avg_conceded=data.get("away_avg_conceded", 1.7),
        form=data.get("form", "WDDLL"),
        injuries=data.get("injuries", []),
        games=data.get("games", 0),
    )


@router.post("/match/{match_id}", response_model=FullAnalysisResponse)
async def analyze_match(
    match_id: int,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Lance l'analyse complète d'un match.
    Body attendu:
    {
      "home_profile": { ... TeamProfile fields ... },
      "away_profile": { ... TeamProfile fields ... },
      "h2h": { "home_wins": 5, "draws": 3, "away_wins": 4, "avg_goals": 2.6 },
      "is_home_fixture": true
    }
    """
    match = await db.get(Match, match_id)
    if not match:
        raise HTTPException(404, "Match not found")

    # Récupérer l'historique des cotes en DB
    odds_result = await db.execute(
        select(OddsSnapshot)
        .where(OddsSnapshot.match_id == match_id)
        .order_by(OddsSnapshot.timestamp)
    )
    snaps = odds_result.scalars().all()
    odds_snapshots = [
        {"home": s.odds_home, "draw": s.odds_draw, "away": s.odds_away, "ts": int(s.timestamp.timestamp())}
        for s in snaps
    ]
    volumes = [
        {"total": (s.volume_home or 0) + (s.volume_away or 0) + (s.volume_draw or 0)}
        for s in snaps
    ]

    home_profile = _build_profile_from_body(body.get("home_profile", {"name": match.home_team}))
    away_profile = _build_profile_from_body(body.get("away_profile", {"name": match.away_team}))
    h2h_data = body.get("h2h", {})
    h2h = H2HRecord(
        home_wins=h2h_data.get("home_wins", 0),
        draws=h2h_data.get("draws", 0),
        away_wins=h2h_data.get("away_wins", 0),
        avg_goals=h2h_data.get("avg_goals", 2.5),
    )
    is_home = body.get("is_home_fixture", True)

    from ..schemas.schemas import MatchOut
    match_out = MatchOut.from_orm(match)

    analysis = pe.run_full_analysis(
        match=match_out,
        home_profile=home_profile,
        away_profile=away_profile,
        h2h=h2h,
        odds_snapshots=odds_snapshots,
        volumes=volumes if any(v["total"] > 0 for v in volumes) else None,
        is_home_fixture=is_home,
    )

    # Sauvegarder en DB
    existing = await db.execute(select(MatchAnalysis).where(MatchAnalysis.match_id == match_id))
    db_analysis = existing.scalar_one_or_none()

    if not db_analysis:
        db_analysis = MatchAnalysis(match_id=match_id)
        db.add(db_analysis)

    db_analysis.predicted_winner = analysis.predicted_winner
    db_analysis.prob_home_win = analysis.prediction.prob_home
    db_analysis.prob_draw = analysis.prediction.prob_draw
    db_analysis.prob_away_win = analysis.prediction.prob_away
    db_analysis.predicted_home_score = analysis.prediction.predicted_home_score
    db_analysis.predicted_away_score = analysis.prediction.predicted_away_score
    db_analysis.exact_score_prob = analysis.prediction.exact_score_probability
    db_analysis.prob_over25 = analysis.prediction.prob_over25
    db_analysis.prob_btts = analysis.prediction.prob_btts
    db_analysis.prediction_confidence = analysis.prediction_confidence
    db_analysis.model_agreement = analysis.prediction.model_agreement
    db_analysis.suspicion_score = analysis.suspicion.score
    db_analysis.suspicion_flags = [f.dict() for f in analysis.suspicion.flags]
    db_analysis.similar_suspect_matches = analysis.suspicion.similar_suspect_matches
    db_analysis.poisson_prediction = analysis.markets.get("top_5_scores", [])
    db_analysis.odds_analysis = analysis.odds_analysis.dict()

    await db.commit()
    return analysis


@router.post("/quick", response_model=FullAnalysisResponse)
async def quick_analyze(body: dict = Body(...)):
    """
    Analyse rapide sans persistance DB.
    Utile pour tests et demos.
    """
    from ..schemas.schemas import MatchOut
    from datetime import datetime

    home = body.get("home_team", "Team A")
    away = body.get("away_team", "Team B")

    mock_match = MatchOut(
        id=0,
        external_id="quick",
        competition=body.get("competition", "Unknown"),
        home_team=home,
        away_team=away,
        match_date=datetime.utcnow(),
        status="scheduled",
        home_score=None,
        away_score=None,
        home_xg=None,
        away_xg=None,
        home_shots=None,
        away_shots=None,
        home_possession=None,
        away_possession=None,
        home_form=body.get("home_profile", {}).get("form", "WDDLL"),
        away_form=body.get("away_profile", {}).get("form", "WDDLL"),
    )

    home_profile = _build_profile_from_body(body.get("home_profile", {"name": home}))
    away_profile = _build_profile_from_body(body.get("away_profile", {"name": away}))
    h2h_data = body.get("h2h", {})
    h2h = H2HRecord(
        home_wins=h2h_data.get("home_wins", 0),
        draws=h2h_data.get("draws", 0),
        away_wins=h2h_data.get("away_wins", 0),
        avg_goals=h2h_data.get("avg_goals", 2.5),
    )

    odds_snaps = body.get("odds_snapshots", [])
    return pe.run_full_analysis(
        match=mock_match,
        home_profile=home_profile,
        away_profile=away_profile,
        h2h=h2h,
        odds_snapshots=odds_snaps,
        is_home_fixture=body.get("is_home_fixture", True),
    )
