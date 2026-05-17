from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..core.database import get_db
from ..models.db_models import Match, MatchStatus, OddsSnapshot
from ..schemas.schemas import MatchCreate, MatchUpdate, MatchOut, OddsSnapshotIn, DashboardMatchCard

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[DashboardMatchCard])
async def list_matches(
    status: str | None = Query(None),
    competition: str | None = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = select(Match).order_by(desc(Match.match_date)).limit(limit).offset(offset)
    if status:
        q = q.where(Match.status == status)
    if competition:
        q = q.where(Match.competition == competition)

    result = await db.execute(q)
    matches = result.scalars().all()

    cards = []
    for m in matches:
        analysis = m.analysis
        if analysis:
            cards.append(DashboardMatchCard(
                match_id=m.id,
                home_team=m.home_team,
                away_team=m.away_team,
                match_date=m.match_date,
                competition=m.competition,
                status=m.status.value,
                suspicion_score=analysis.suspicion_score or 0.0,
                suspicion_level=analysis.suspicion_level.value if analysis.suspicion_level else "low",
                predicted_winner=analysis.predicted_winner or "-",
                prediction_confidence=analysis.prediction_confidence or 0.0,
                prob_home=analysis.prob_home_win or 0.0,
                prob_draw=analysis.prob_draw or 0.0,
                prob_away=analysis.prob_away_win or 0.0,
                predicted_score=f"{analysis.predicted_home_score or 0}:{analysis.predicted_away_score or 0}",
                key_flags=[f["description"] for f in (analysis.suspicion_flags or [])[:3]],
            ))
        else:
            cards.append(DashboardMatchCard(
                match_id=m.id,
                home_team=m.home_team,
                away_team=m.away_team,
                match_date=m.match_date,
                competition=m.competition,
                status=m.status.value,
                suspicion_score=0.0,
                suspicion_level="low",
                predicted_winner="-",
                prediction_confidence=0.0,
                prob_home=0.0, prob_draw=0.0, prob_away=0.0,
                predicted_score="0:0",
                key_flags=[],
            ))
    return cards


@router.post("", response_model=MatchOut, status_code=201)
async def create_match(payload: MatchCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Match).where(Match.external_id == payload.external_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Match {payload.external_id} already exists")

    match = Match(**payload.dict())
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


@router.get("/{match_id}", response_model=MatchOut)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    m = await db.get(Match, match_id)
    if not m:
        raise HTTPException(404, "Match not found")
    return m


@router.patch("/{match_id}", response_model=MatchOut)
async def update_match(match_id: int, payload: MatchUpdate, db: AsyncSession = Depends(get_db)):
    m = await db.get(Match, match_id)
    if not m:
        raise HTTPException(404, "Match not found")
    for field, value in payload.dict(exclude_none=True).items():
        setattr(m, field, value)
    await db.commit()
    await db.refresh(m)
    return m


@router.post("/{match_id}/odds", status_code=201)
async def add_odds_snapshot(
    match_id: int,
    payload: OddsSnapshotIn,
    db: AsyncSession = Depends(get_db),
):
    m = await db.get(Match, match_id)
    if not m:
        raise HTTPException(404, "Match not found")
    snap = OddsSnapshot(match_id=match_id, **payload.dict())
    db.add(snap)
    await db.commit()
    return {"status": "ok", "match_id": match_id}


@router.get("/{match_id}/odds")
async def get_odds_history(match_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OddsSnapshot)
        .where(OddsSnapshot.match_id == match_id)
        .order_by(OddsSnapshot.timestamp)
    )
    snaps = result.scalars().all()
    return [
        {
            "timestamp": s.timestamp.isoformat(),
            "bookmaker": s.bookmaker,
            "home": s.odds_home,
            "draw": s.odds_draw,
            "away": s.odds_away,
            "over25": s.odds_over25,
            "btts_yes": s.odds_btts_yes,
            "volume_home": s.volume_home,
            "volume_away": s.volume_away,
            "is_live": s.is_live,
            "minute": s.match_minute,
        }
        for s in snaps
    ]
