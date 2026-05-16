"""
Model trainer — run once you have enough historical match data in the DB.
Usage: python -m app.ml.trainer
"""
import os
import pickle
import asyncio
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import Match, MatchStatus
from app.ml.features import build_feature_vector
from app.services.analyzer import MatchContext
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _match_to_context(match) -> Optional[MatchContext]:
    """Convert a DB Match row to a MatchContext (best effort)."""
    try:
        ht = match.home_team
        at = match.away_team
        ctx = MatchContext(
            home_name=ht.name,
            away_name=at.name,
            home_form5=ht.form_last5 or "WWWDD",
            away_form5=at.form_last5 or "WDLWL",
            home_form10=ht.form_last10 or "WWWWDWWDWL",
            away_form10=at.form_last10 or "WDLWLWDLWW",
            home_goals_scored_avg=ht.home_goals_scored_avg,
            home_goals_conceded_avg=ht.home_goals_conceded_avg,
            away_goals_scored_avg=at.away_goals_scored_avg,
            away_goals_conceded_avg=at.away_goals_conceded_avg,
            home_xg_avg=ht.home_xg_avg or 1.5,
            away_xg_avg=at.away_xg_avg or 1.2,
            home_xga_avg=ht.home_xga_avg or 1.1,
            away_xga_avg=at.away_xga_avg or 1.4,
        )
        return ctx
    except Exception:
        return None


def _label(home_score: int, away_score: int) -> int:
    """0 = away win, 1 = draw, 2 = home win."""
    if home_score > away_score:  return 2
    if home_score == away_score: return 1
    return 0


async def collect_training_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Match).where(Match.status == MatchStatus.FINISHED,
                                Match.home_score.isnot(None))
        )
        matches = result.scalars().all()

    X, y = [], []
    for m in matches:
        ctx = _match_to_context(m)
        if ctx is None:
            continue
        try:
            feat = build_feature_vector(ctx)
            X.append(feat)
            y.append(_label(m.home_score, m.away_score))
        except Exception:
            continue

    return np.array(X), np.array(y)


def train(X: np.ndarray, y: np.ndarray):
    if len(X) < 100:
        logger.warning(f"Only {len(X)} samples — model may not be reliable. Need ≥ 100.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    base_clf = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05,
        max_depth=4, subsample=0.8, random_state=42,
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base_clf, cv=5, method="isotonic")),
    ])

    pipeline.fit(X_train, y_train)

    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
    test_acc = pipeline.score(X_test, y_test)
    logger.info(f"CV accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    logger.info(f"Test accuracy: {test_acc:.3f}")

    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
    with open(settings.MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info(f"Model saved to {settings.MODEL_PATH}")
    return pipeline


async def main():
    await init_db()
    logger.info("Collecting training data...")
    X, y = await collect_training_data()
    logger.info(f"Dataset: {len(X)} samples — classes: {dict(zip(*np.unique(y, return_counts=True)))}")
    if len(X) == 0:
        logger.error("No training data found. Run the data fetcher first.")
        return
    train(X, y)


if __name__ == "__main__":
    asyncio.run(main())


# Allow Optional import
from typing import Optional
