"""Save generated tickets + predictions to PostgreSQL."""
from datetime import date, datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.prediction import Ticket, Prediction, PredictionResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def save_tickets(tickets: list[dict], target_date: date, db: AsyncSession) -> list[Ticket]:
    saved = []
    for t in tickets:
        ticket = Ticket(
            ticket_number=t["ticket_number"],
            label=t["label"],
            target_date=target_date,
            generated_at=datetime.utcnow(),
            total_odds=t["total_odds"],
            stake=t.get("stake", 1.0),
            potential_gain=t.get("potential_gain", t["total_odds"]),
            result=PredictionResult.PENDING,
        )
        db.add(ticket)
        await db.flush()  # get ticket.id without committing

        for bet in t.get("bets", []):
            pred = Prediction(
                ticket_id=ticket.id,
                fixture_id=bet.get("fixture_id"),
                match_label=bet.get("match", ""),
                competition=bet.get("competition", ""),
                kickoff=_parse_dt(bet.get("kickoff")),
                bet_type=bet.get("bet_type", "home"),
                odds=bet.get("odds", 1.0),
                confidence=bet.get("confidence", 60),
                value_edge=bet.get("value_edge", 0.0),
                prob_home=bet.get("prob_home"),
                prob_draw=bet.get("prob_draw"),
                prob_away=bet.get("prob_away"),
                prob_btts=bet.get("prob_btts"),
                prob_over25=bet.get("prob_over25"),
                reasoning=bet.get("reasoning", ""),
                risks=bet.get("risks", ""),
                score_breakdown=bet.get("score_breakdown", {}),
                key_stats=bet.get("key_stats", {}),
            )
            db.add(pred)

        saved.append(ticket)

    await db.commit()
    logger.info(f"Saved {len(saved)} tickets for {target_date}")
    return saved


async def get_history(db: AsyncSession, limit: int = 50) -> list[dict]:
    result = await db.execute(
        select(Ticket)
        .order_by(desc(Ticket.generated_at))
        .limit(limit)
    )
    tickets = result.scalars().all()
    return [_ticket_to_dict(t) for t in tickets]


def _ticket_to_dict(t: Ticket) -> dict:
    bets = []
    for p in (t.predictions or []):
        bets.append({
            "fixture_id": p.fixture_id or 0,
            "match": p.match_label or "",
            "competition": p.competition or "",
            "kickoff": p.kickoff.isoformat() if p.kickoff else "",
            "bet_type": p.bet_type,
            "odds": p.odds,
            "confidence": p.confidence,
            "value_edge": p.value_edge or 0.0,
            "prob_home": p.prob_home or 0.33,
            "prob_draw": p.prob_draw or 0.33,
            "prob_away": p.prob_away or 0.34,
            "prob_btts": p.prob_btts or 0.5,
            "prob_over25": p.prob_over25 or 0.5,
            "reasoning": p.reasoning or "",
            "risks": p.risks or "",
            "score_breakdown": p.score_breakdown or {},
            "key_stats": p.key_stats or {},
        })
    return {
        "ticket_number": t.ticket_number or t.id,
        "label": t.label or f"Ticket #{t.id}",
        "total_odds": t.total_odds or 1.0,
        "stake": t.stake or 1.0,
        "potential_gain": t.potential_gain or t.total_odds or 1.0,
        "bets": bets,
        "target_date": str(t.target_date) if t.target_date else "",
        "generated_at": t.generated_at.isoformat() if t.generated_at else "",
        "result": t.result.value if t.result else "pending",
    }


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
