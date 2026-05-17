"""
Analyse des statistiques footballistiques.
Calcule les forces d'attaque/défense, les λ Poisson, la forme et le H2H.
"""
from dataclasses import dataclass
from ..schemas.schemas import FootballStatsResult
from ..ml.xgboost_model import XGBFeatures


LEAGUE_HOME_AVG = 1.52   # buts moyens domicile en ligue standard
LEAGUE_AWAY_AVG = 1.18


@dataclass
class TeamProfile:
    name: str
    avg_goals_scored: float = 1.5
    avg_goals_conceded: float = 1.5
    avg_xg_for: float = 1.4
    avg_xg_against: float = 1.4
    home_avg_scored: float = 1.7
    home_avg_conceded: float = 1.2
    away_avg_scored: float = 1.2
    away_avg_conceded: float = 1.7
    form: str = "WWDLL"      # 5 derniers matchs
    injuries: list[str] | None = None
    games: int = 0

    @property
    def attack_strength_home(self) -> float:
        base = self.home_avg_scored / LEAGUE_HOME_AVG if LEAGUE_HOME_AVG > 0 else 1.0
        return max(0.3, min(2.5, base))

    @property
    def attack_strength_away(self) -> float:
        base = self.away_avg_scored / LEAGUE_AWAY_AVG if LEAGUE_AWAY_AVG > 0 else 1.0
        return max(0.3, min(2.5, base))

    @property
    def defense_strength_home(self) -> float:
        base = LEAGUE_AWAY_AVG / self.home_avg_conceded if self.home_avg_conceded > 0 else 1.0
        return max(0.3, min(2.5, base))

    @property
    def defense_strength_away(self) -> float:
        base = LEAGUE_HOME_AVG / self.away_avg_conceded if self.away_avg_conceded > 0 else 1.0
        return max(0.3, min(2.5, base))

    @property
    def form_score(self) -> float:
        """0-1: convertit WWDLL → score moyen (V=1, N=0.5, D=0)"""
        mp = {"W": 1.0, "D": 0.5, "L": 0.0}
        scores = [mp.get(c, 0.5) for c in self.form.upper()[-5:]]
        return sum(scores) / len(scores) if scores else 0.5

    @property
    def key_injuries(self) -> int:
        return len(self.injuries or [])


@dataclass
class H2HRecord:
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0
    avg_goals: float = 2.5
    recent_results: list[str] | None = None  # ex: ["1-2", "0-0", "3-1"]

    @property
    def total(self) -> int:
        return self.home_wins + self.draws + self.away_wins

    @property
    def home_win_rate(self) -> float:
        if self.total == 0:
            return 0.5
        return self.home_wins / self.total


def build_xgb_features(
    home: TeamProfile,
    away: TeamProfile,
    h2h: H2HRecord,
    odds_implied_home: float = 0.45,
    odds_implied_draw: float = 0.25,
    odds_implied_away: float = 0.30,
    is_home: bool = True,
) -> XGBFeatures:
    return XGBFeatures(
        home_avg_goals_scored=home.avg_goals_scored,
        away_avg_goals_scored=away.avg_goals_scored,
        home_avg_goals_conceded=home.avg_goals_conceded,
        away_avg_goals_conceded=away.avg_goals_conceded,
        home_xg_for=home.avg_xg_for,
        away_xg_for=away.avg_xg_for,
        home_xg_against=home.avg_xg_against,
        away_xg_against=away.avg_xg_against,
        home_form=home.form_score,
        away_form=away.form_score,
        h2h_home_win_rate=h2h.home_win_rate,
        h2h_avg_goals=h2h.avg_goals,
        h2h_matches=h2h.total,
        odds_implied_home=odds_implied_home,
        odds_implied_draw=odds_implied_draw,
        odds_implied_away=odds_implied_away,
        home_advantage=1.0 if is_home else 0.5,
        home_injured_key=home.key_injuries,
        away_injured_key=away.key_injuries,
        home_xg_last5=home.avg_xg_for,
        away_xg_last5=away.avg_xg_for,
    )


def analyze(
    home: TeamProfile,
    away: TeamProfile,
    h2h: H2HRecord,
    is_home_fixture: bool = True,
) -> tuple[FootballStatsResult, float, float]:
    """
    Retourne (FootballStatsResult, lambda_home, lambda_away).
    Les lambdas sont utilisés directement par le modèle Poisson.
    """
    # Forces
    atk_h = home.attack_strength_home if is_home_fixture else home.attack_strength_away
    def_h = home.defense_strength_home if is_home_fixture else home.defense_strength_away
    atk_a = away.attack_strength_away
    def_a = away.defense_strength_away

    # λ Dixon-Coles (home advantage déjà intégré dans les strengths)
    lambda_home = atk_h * def_a * LEAGUE_HOME_AVG
    lambda_away = atk_a * def_h * LEAGUE_AWAY_AVG

    # Ajustement forme
    form_adj = (home.form_score - away.form_score) * 0.10
    lambda_home = max(0.2, lambda_home * (1 + form_adj))
    lambda_away = max(0.2, lambda_away * (1 - form_adj))

    # Ajustement blessures
    inj_penalty = 0.05 * home.key_injuries
    lambda_home = max(0.2, lambda_home * (1 - inj_penalty))
    inj_penalty_a = 0.05 * away.key_injuries
    lambda_away = max(0.2, lambda_away * (1 - inj_penalty_a))

    # Contribution suspicion: forte dépend de l'écart xG vs forces
    xg_gap = abs(home.avg_xg_for - home.avg_goals_scored)
    susp = min(15.0, xg_gap * 5)

    result = FootballStatsResult(
        home_attack_strength=round(atk_h, 3),
        away_attack_strength=round(atk_a, 3),
        home_defense_strength=round(def_h, 3),
        away_defense_strength=round(def_a, 3),
        expected_home_goals=round(lambda_home, 3),
        expected_away_goals=round(lambda_away, 3),
        h2h_home_wins=h2h.home_wins,
        h2h_draws=h2h.draws,
        h2h_away_wins=h2h.away_wins,
        h2h_avg_goals=round(h2h.avg_goals, 2),
        form_home_score=round(home.form_score, 3),
        form_away_score=round(away.form_score, 3),
        home_advantage_factor=round(atk_h / max(atk_a, 0.1), 3),
        suspicion_contribution=round(susp, 2),
    )

    return result, lambda_home, lambda_away
