"""
Historical match data collector.
Fetches finished matches from API-Football, stores teams + matches in DB,
then computes aggregated team stats for ML training.
"""
import asyncio
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.team import Team
from app.models.match import Match, MatchStatus
from app.services.data_fetcher import get_fixtures, get_team_statistics, _request
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Ligues à collecter avec leur ID API-Football
COLLECTION_LEAGUES = [
    (39,  2024, "Premier League"),
    (140, 2024, "La Liga"),
    (61,  2024, "Ligue 1"),
    (78,  2024, "Bundesliga"),
    (135, 2024, "Serie A"),
    (2,   2024, "Champions League"),
    (39,  2023, "Premier League 23/24"),
    (140, 2023, "La Liga 23/24"),
]


async def collect_historical(
    season_only: Optional[int] = None,
    max_per_league: int = 100,
) -> dict:
    """
    Fetch finished matches from API-Football and store in DB.
    Returns summary dict with counts.
    """
    if not settings.API_FOOTBALL_KEY:
        logger.warning("API_FOOTBALL_KEY non défini — collection impossible avec mock data")
        return {"error": "Clé API-Football requise", "stored": 0}

    total_stored = 0
    total_skipped = 0

    async with AsyncSessionLocal() as db:
        for league_id, season, league_name in COLLECTION_LEAGUES:
            if season_only and season != season_only:
                continue

            logger.info(f"Collecte {league_name} {season}...")
            try:
                stored, skipped = await _collect_league(db, league_id, season, league_name, max_per_league)
                total_stored += stored
                total_skipped += skipped
                logger.info(f"  → {stored} stockés, {skipped} ignorés")
            except Exception as e:
                logger.error(f"Erreur {league_name}: {e}")

        # Mettre à jour les stats agrégées des équipes
        logger.info("Mise à jour des stats agrégées des équipes...")
        updated = await _update_team_stats(db)
        logger.info(f"  → {updated} équipes mises à jour")

    return {
        "matches_stored": total_stored,
        "matches_skipped": total_skipped,
        "teams_updated": updated,
    }


async def _collect_league(
    db: AsyncSession,
    league_id: int,
    season: int,
    league_name: str,
    max_per_league: int,
) -> tuple[int, int]:
    # Récupérer tous les matchs terminés de la saison
    data = await _request("fixtures", {
        "league": league_id,
        "season": season,
        "status": "FT",  # Full Time only
    })
    fixtures = data.get("response", []) if data else []
    fixtures = fixtures[:max_per_league]

    stored = skipped = 0
    for fix_data in fixtures:
        try:
            result = await _store_fixture(db, fix_data, league_name)
            if result:
                stored += 1
            else:
                skipped += 1
        except Exception as e:
            logger.debug(f"Skip fixture: {e}")
            skipped += 1

    await db.commit()
    return stored, skipped


async def _store_fixture(db: AsyncSession, fix_data: dict, league_name: str) -> bool:
    fix = fix_data.get("fixture", {})
    teams = fix_data.get("teams", {})
    goals = fix_data.get("goals", {})
    score = fix_data.get("score", {})

    api_id = fix.get("id")
    if not api_id:
        return False

    # Skip si déjà en DB
    existing = await db.execute(select(Match).where(Match.api_id == api_id))
    if existing.scalar_one_or_none():
        return False

    home_data = teams.get("home", {})
    away_data = teams.get("away", {})
    home_score = goals.get("home")
    away_score = goals.get("away")

    if home_score is None or away_score is None:
        return False

    # Upsert équipes
    home_team = await _get_or_create_team(db, home_data, league_name)
    away_team = await _get_or_create_team(db, away_data, league_name)

    if not home_team or not away_team:
        return False

    # Stocker le match
    kickoff_str = fix.get("date", "")
    try:
        kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
    except Exception:
        kickoff = None

    ht = score.get("halftime", {})
    match = Match(
        api_id=api_id,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        competition=league_name,
        competition_id=fix_data.get("league", {}).get("id"),
        season=str(fix_data.get("league", {}).get("season", "")),
        round=fix_data.get("league", {}).get("round", ""),
        kickoff=kickoff,
        venue=fix.get("venue", {}).get("name", "") if isinstance(fix.get("venue"), dict) else "",
        status=MatchStatus.FINISHED,
        home_score=int(home_score),
        away_score=int(away_score),
        home_score_ht=ht.get("home"),
        away_score_ht=ht.get("away"),
    )
    db.add(match)
    return True


async def _get_or_create_team(db: AsyncSession, team_data: dict, league_name: str) -> Optional[Team]:
    api_id = team_data.get("id")
    name = team_data.get("name", "")
    if not api_id or not name:
        return None

    result = await db.execute(select(Team).where(Team.api_id == api_id))
    team = result.scalar_one_or_none()
    if team:
        return team

    team = Team(
        api_id=api_id,
        name=name,
        logo_url=team_data.get("logo", ""),
        league=league_name,
    )
    db.add(team)
    await db.flush()
    return team


async def _update_team_stats(db: AsyncSession) -> int:
    """Recompute aggregated stats for all teams from stored matches."""
    result = await db.execute(select(Team))
    teams = result.scalars().all()
    updated = 0

    for team in teams:
        # Matchs à domicile terminés
        home_q = await db.execute(
            select(Match).where(
                Match.home_team_id == team.id,
                Match.status == MatchStatus.FINISHED,
                Match.home_score.isnot(None),
            )
        )
        home_matches = home_q.scalars().all()

        # Matchs à l'extérieur terminés
        away_q = await db.execute(
            select(Match).where(
                Match.away_team_id == team.id,
                Match.status == MatchStatus.FINISHED,
                Match.away_score.isnot(None),
            )
        )
        away_matches = away_q.scalars().all()

        if not home_matches and not away_matches:
            continue

        # Stats domicile
        if home_matches:
            team.home_goals_scored_avg = _avg([m.home_score for m in home_matches])
            team.home_goals_conceded_avg = _avg([m.away_score for m in home_matches])
            team.home_wins_pct = sum(1 for m in home_matches if m.home_score > m.away_score) / len(home_matches) * 100

        # Stats extérieur
        if away_matches:
            team.away_goals_scored_avg = _avg([m.away_score for m in away_matches])
            team.away_goals_conceded_avg = _avg([m.home_score for m in away_matches])
            team.away_wins_pct = sum(1 for m in away_matches if m.away_score > m.home_score) / len(away_matches) * 100

        # Stats globales
        all_matches = home_matches + away_matches
        btts = sum(1 for m in all_matches if m.home_score > 0 and m.away_score > 0)
        over25 = sum(1 for m in all_matches if (m.home_score + m.away_score) > 2)
        team.btts_pct = btts / len(all_matches) * 100
        team.over25_pct = over25 / len(all_matches) * 100

        # Forme (5 derniers matchs toutes compétitions)
        recent = sorted(all_matches, key=lambda m: m.kickoff or datetime.min, reverse=True)[:10]
        form = []
        for m in recent:
            if m.home_team_id == team.id:
                form.append("W" if m.home_score > m.away_score else ("D" if m.home_score == m.away_score else "L"))
            else:
                form.append("W" if m.away_score > m.home_score else ("D" if m.home_score == m.away_score else "L"))
        team.form_last5 = "".join(form[:5])
        team.form_last10 = "".join(form[:10])

        # Elo simple
        team.elo_rating = _compute_elo(team, home_matches, away_matches)
        updated += 1

    await db.commit()
    return updated


def _avg(values: list) -> float:
    cleaned = [v for v in values if v is not None]
    return round(sum(cleaned) / max(len(cleaned), 1), 3)


def _compute_elo(team: Team, home_matches: list, away_matches: list) -> float:
    rating = 1500.0
    K = 32
    for m in sorted(home_matches + away_matches, key=lambda m: m.kickoff or datetime.min):
        if m.home_team_id == team.id:
            expected = 1 / (1 + 10 ** ((1500 - rating) / 400))
            actual = 1.0 if m.home_score > m.away_score else (0.5 if m.home_score == m.away_score else 0.0)
        else:
            expected = 1 / (1 + 10 ** ((1500 - rating) / 400))
            actual = 1.0 if m.away_score > m.home_score else (0.5 if m.home_score == m.away_score else 0.0)
        rating += K * (actual - expected)
    return round(rating, 1)
