"""
ML model trainer.
Usage:
  python -m app.ml.trainer             # train on DB data (or synthetic if DB empty)
  python -m app.ml.trainer --synthetic # force synthetic data
"""
import os
import pickle
import asyncio
import argparse
import numpy as np
from typing import Optional
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models.match import Match, MatchStatus
from app.ml.features import build_feature_vector
from app.ml.synthetic import generate_synthetic_dataset
from app.services.analyzer import MatchContext
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _match_to_context(match: Match) -> Optional[MatchContext]:
    try:
        ht = match.home_team
        at = match.away_team
        return MatchContext(
            home_name=ht.name,
            away_name=at.name,
            home_goals_scored_avg=ht.home_goals_scored_avg or 1.5,
            home_goals_conceded_avg=ht.home_goals_conceded_avg or 1.2,
            away_goals_scored_avg=at.away_goals_scored_avg or 1.3,
            away_goals_conceded_avg=at.away_goals_conceded_avg or 1.4,
            home_xg_avg=ht.home_xg_avg or 1.5,
            away_xg_avg=at.away_xg_avg or 1.2,
            home_xga_avg=ht.home_xga_avg or 1.1,
            away_xga_avg=at.away_xga_avg or 1.4,
        )
    except Exception:
        return None


def _label(home_score: int, away_score: int) -> int:
    if home_score > away_score:  return 2
    if home_score == away_score: return 1
    return 0


async def collect_db_data():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Match).where(
                Match.status == MatchStatus.FINISHED,
                Match.home_score.isnot(None),
            )
        )
        matches = result.scalars().all()

    X, y = [], []
    for m in matches:
        ctx = _match_to_context(m)
        if ctx is None:
            continue
        try:
            X.append(build_feature_vector(ctx))
            y.append(_label(m.home_score, m.away_score))
        except Exception:
            continue
    return np.array(X), np.array(y)


def train(X: np.ndarray, y: np.ndarray, source: str = "unknown") -> None:
    logger.info(f"Training on {len(X)} samples from [{source}]")
    if len(X) < 50:
        logger.error("Pas assez de données pour entraîner (minimum 50 samples)")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    base = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=4,
        subsample=0.8, min_samples_leaf=5, random_state=42,
    )
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", CalibratedClassifierCV(base, cv=5, method="isotonic")),
    ])
    pipeline.fit(X_train, y_train)

    cv = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="accuracy")
    test_acc = pipeline.score(X_test, y_test)
    logger.info(f"CV accuracy : {cv.mean():.3f} ± {cv.std():.3f}")
    logger.info(f"Test accuracy: {test_acc:.3f}")

    os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
    with open(settings.MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f)
    logger.info(f"Modèle sauvegardé → {settings.MODEL_PATH}")


async def main(force_synthetic: bool = False) -> None:
    await init_db()

    X, y = np.array([]), np.array([])
    if not force_synthetic:
        logger.info("Collecte des données depuis la DB...")
        X, y = await collect_db_data()
        logger.info(f"{len(X)} matchs trouvés en DB")

    if len(X) < 100:
        logger.info("Données DB insuffisantes — utilisation de données synthétiques")
        X_syn, y_syn = generate_synthetic_dataset(n_samples=4000)
        if len(X) > 0:
            X = np.vstack([X, X_syn])
            y = np.concatenate([y, y_syn])
            source = f"DB({len(X) - len(X_syn)}) + synthetic(4000)"
        else:
            X, y = X_syn, y_syn
            source = "synthetic(4000)"
    else:
        source = f"DB({len(X)})"

    train(X, y, source=source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="Forcer les données synthétiques")
    args = parser.parse_args()
    asyncio.run(main(force_synthetic=args.synthetic))
