"""
Main prediction orchestrator.
Fetches data → analyzes → selects top bets → builds daily tickets.
"""
from datetime import date, datetime, timedelta
from typing import Optional
from app.services.data_fetcher import (
    get_fixtures, get_team_statistics, get_head_to_head,
    get_fixture_odds, get_team_injuries,
)
from app.services.odds_fetcher import get_live_odds, extract_odds
from app.services.analyzer import MatchContext, analyze, AnalysisResult
from app.ml.model import predict_probabilities
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Leagues to analyze (API-Football IDs)
LEAGUES = [
    (39, 2025),   # Premier League
    (140, 2025),  # La Liga
    (61, 2025),   # Ligue 1
    (78, 2025),   # Bundesliga
    (135, 2025),  # Serie A
    (2, 2025),    # Champions League
]


async def generate_daily_tickets(target_date: Optional[date] = None) -> list[dict]:
    """Generate 5 prediction tickets targeting ~5.0 total odds."""
    if target_date is None:
        target_date = date.today()

    from_date = target_date.strftime("%Y-%m-%d")
    to_date   = target_date.strftime("%Y-%m-%d")

    logger.info(f"Generating tickets for {from_date}")

    # 1. Collect all upcoming fixtures
    all_fixtures = []
    for league_id, season in LEAGUES:
        fixtures = await get_fixtures(league_id, season, from_date, to_date)
        all_fixtures.extend([(f, league_id, season) for f in fixtures])

    logger.info(f"Found {len(all_fixtures)} fixtures")

    # 2. Analyze each fixture
    candidates = []
    for fixture_data, league_id, season in all_fixtures:
        try:
            analysis = await _analyze_fixture(fixture_data, league_id, season)
            if analysis and analysis["confidence"] >= settings.MIN_CONFIDENCE:
                candidates.append(analysis)
        except Exception as e:
            logger.error(f"Error analyzing fixture {fixture_data.get('fixture', {}).get('id')}: {e}")

    # 3. Sort by value edge then confidence
    candidates.sort(key=lambda x: (x["value_edge"], x["confidence"]), reverse=True)

    # 4. Build 5 tickets targeting ~5.0 total odds
    tickets = _build_tickets(candidates)
    logger.info(f"Generated {len(tickets)} tickets from {len(candidates)} candidates")
    return tickets


async def _analyze_fixture(fixture_data: dict, league_id: int, season: int) -> Optional[dict]:
    fixture = fixture_data.get("fixture", {})
    teams   = fixture_data.get("teams", {})
    league  = fixture_data.get("league", {})

    home_id = teams.get("home", {}).get("id")
    away_id = teams.get("away", {}).get("id")
    fix_id  = fixture.get("id")

    if not all([home_id, away_id, fix_id]):
        return None

    # Fetch stats
    home_stats = await get_team_statistics(home_id, league_id, season)
    away_stats = await get_team_statistics(away_id, league_id, season)
    h2h        = await get_head_to_head(home_id, away_id, last=10)
    odds_raw   = await get_fixture_odds(fix_id)

    ctx = _build_context(
        home_name=teams["home"]["name"],
        away_name=teams["away"]["name"],
        home_stats=home_stats or {},
        away_stats=away_stats or {},
        h2h=h2h,
        odds_raw=odds_raw,
    )

    # ML probabilities
    ml_home, ml_draw, ml_away = predict_probabilities(ctx)
    ctx.ml_prob_home = ml_home
    ctx.ml_prob_draw = ml_draw

    result = analyze(ctx)

    return {
        "fixture_id": fix_id,
        "match": f"{ctx.home_name} vs {ctx.away_name}",
        "competition": league.get("name", ""),
        "kickoff": fixture.get("date", ""),
        "bet_type": result.best_bet,
        "odds": result.best_odds,
        "confidence": result.confidence,
        "value_edge": result.value_edge,
        "prob_home": result.prob_home,
        "prob_draw": result.prob_draw,
        "prob_away": result.prob_away,
        "prob_btts": result.prob_btts,
        "prob_over25": result.prob_over25,
        "reasoning": result.reasoning,
        "risks": result.risks,
        "key_stats": result.key_stats,
        "score_breakdown": result.key_stats.get("scores", {}),
    }


def _build_context(home_name, away_name, home_stats, away_stats, h2h, odds_raw) -> MatchContext:
    def _avg(stats, side, key):
        try:
            return float(stats["goals"][side]["average"][key])
        except (KeyError, TypeError, ValueError):
            return 1.2

    home_scored = _avg(home_stats, "for", "home")
    home_conceded = _avg(home_stats, "against", "home")
    away_scored = _avg(away_stats, "for", "away")
    away_conceded = _avg(away_stats, "against", "away")

    h2h_hw = sum(1 for m in h2h if m.get("teams", {}).get("home", {}).get("winner"))
    h2h_aw = sum(1 for m in h2h if m.get("teams", {}).get("away", {}).get("winner"))
    h2h_d  = len(h2h) - h2h_hw - h2h_aw
    h2h_goals = [
        (m.get("goals", {}).get("home", 0) or 0) + (m.get("goals", {}).get("away", 0) or 0)
        for m in h2h
    ]
    h2h_avg = sum(h2h_goals) / max(len(h2h_goals), 1)

    # Extract odds
    odds: dict = {}
    if odds_raw:
        try:
            for bk in odds_raw[0].get("bookmakers", []):
                for bet in bk.get("bets", []):
                    vals = {v["value"]: float(v["odd"]) for v in bet.get("values", [])}
                    if bet["name"] == "Match Winner":
                        odds["home"] = vals.get("Home")
                        odds["draw"] = vals.get("Draw")
                        odds["away"] = vals.get("Away")
                    elif "Over/Under" in bet["name"]:
                        odds["over25"] = vals.get("Over 2.5")
                    elif "Both Teams Score" in bet["name"]:
                        odds["btts_yes"] = vals.get("Yes")
        except Exception:
            pass

    return MatchContext(
        home_name=home_name,
        away_name=away_name,
        home_goals_scored_avg=home_scored,
        home_goals_conceded_avg=home_conceded,
        away_goals_scored_avg=away_scored,
        away_goals_conceded_avg=away_conceded,
        h2h_home_wins=h2h_hw,
        h2h_draws=h2h_d,
        h2h_away_wins=h2h_aw,
        h2h_avg_goals=h2h_avg,
        odds_home=odds.get("home"),
        odds_draw=odds.get("draw"),
        odds_away=odds.get("away"),
        odds_over25=odds.get("over25"),
        odds_btts_yes=odds.get("btts_yes"),
    )


def _build_tickets(candidates: list[dict]) -> list[dict]:
    tickets = []
    used = set()
    ticket_num = 0

    # Greedy: pick 2-3 bets per ticket to reach ~5.0 total odds
    i = 0
    while len(tickets) < settings.TICKETS_PER_DAY and i < len(candidates):
        ticket_bets = []
        total_odds = 1.0

        for j in range(i, min(i + 10, len(candidates))):
            c = candidates[j]
            if c["fixture_id"] in used:
                continue
            if total_odds * c["odds"] > settings.TARGET_ODDS * 1.5:
                continue
            ticket_bets.append(c)
            total_odds *= c["odds"]
            used.add(c["fixture_id"])
            if total_odds >= settings.TARGET_ODDS * 0.7:
                break

        if ticket_bets:
            ticket_num += 1
            tickets.append({
                "ticket_number": ticket_num,
                "label": f"Ticket #{ticket_num}",
                "total_odds": round(total_odds, 2),
                "bets": ticket_bets,
                "stake": 1.0,
                "potential_gain": round(total_odds, 2),
            })
        i += max(1, len(ticket_bets))

    return tickets
