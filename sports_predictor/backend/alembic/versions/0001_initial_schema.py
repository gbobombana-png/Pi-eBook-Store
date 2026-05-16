"""Initial schema — teams, matches, predictions, tickets

Revision ID: 0001
Revises:
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("short_name", sa.String(length=10), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("league", sa.String(length=50), nullable=True),
        sa.Column("league_id", sa.Integer(), nullable=True),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("elo_rating", sa.Float(), nullable=True),
        sa.Column("form_last5", sa.String(length=5), nullable=True),
        sa.Column("home_goals_avg", sa.Float(), nullable=True),
        sa.Column("away_goals_avg", sa.Float(), nullable=True),
        sa.Column("home_conceded_avg", sa.Float(), nullable=True),
        sa.Column("away_conceded_avg", sa.Float(), nullable=True),
        sa.Column("home_xg_avg", sa.Float(), nullable=True),
        sa.Column("away_xg_avg", sa.Float(), nullable=True),
        sa.Column("btts_pct", sa.Float(), nullable=True),
        sa.Column("over25_pct", sa.Float(), nullable=True),
        sa.Column("avg_corners", sa.Float(), nullable=True),
        sa.Column("avg_cards", sa.Float(), nullable=True),
        sa.Column("injuries_count", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_api_id", "teams", ["api_id"], unique=True)
    op.create_index("ix_teams_name", "teams", ["name"], unique=False)

    # --- matches ---
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fixture_id", sa.Integer(), nullable=False),
        sa.Column("home_team_id", sa.Integer(), nullable=True),
        sa.Column("away_team_id", sa.Integer(), nullable=True),
        sa.Column("home_team_name", sa.String(length=100), nullable=False),
        sa.Column("away_team_name", sa.String(length=100), nullable=False),
        sa.Column("league_id", sa.Integer(), nullable=True),
        sa.Column("league_name", sa.String(length=100), nullable=True),
        sa.Column("season", sa.Integer(), nullable=True),
        sa.Column("round", sa.String(length=50), nullable=True),
        sa.Column("match_date", sa.DateTime(), nullable=False),
        sa.Column("venue_name", sa.String(length=150), nullable=True),
        sa.Column("venue_city", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            sa.Enum("scheduled", "live", "finished", "postponed", "cancelled", name="matchstatus"),
            nullable=True,
        ),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("home_ht_score", sa.Integer(), nullable=True),
        sa.Column("away_ht_score", sa.Integer(), nullable=True),
        sa.Column("home_xg", sa.Float(), nullable=True),
        sa.Column("away_xg", sa.Float(), nullable=True),
        sa.Column("home_shots", sa.Integer(), nullable=True),
        sa.Column("away_shots", sa.Integer(), nullable=True),
        sa.Column("home_shots_on_target", sa.Integer(), nullable=True),
        sa.Column("away_shots_on_target", sa.Integer(), nullable=True),
        sa.Column("home_possession", sa.Float(), nullable=True),
        sa.Column("away_possession", sa.Float(), nullable=True),
        sa.Column("home_corners", sa.Integer(), nullable=True),
        sa.Column("away_corners", sa.Integer(), nullable=True),
        sa.Column("home_fouls", sa.Integer(), nullable=True),
        sa.Column("away_fouls", sa.Integer(), nullable=True),
        sa.Column("home_yellow_cards", sa.Integer(), nullable=True),
        sa.Column("away_yellow_cards", sa.Integer(), nullable=True),
        sa.Column("home_red_cards", sa.Integer(), nullable=True),
        sa.Column("away_red_cards", sa.Integer(), nullable=True),
        sa.Column("weather", sa.String(length=50), nullable=True),
        sa.Column("referee", sa.String(length=100), nullable=True),
        sa.Column("attendance", sa.Integer(), nullable=True),
        sa.Column("odds_home", sa.Float(), nullable=True),
        sa.Column("odds_draw", sa.Float(), nullable=True),
        sa.Column("odds_away", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_matches_fixture_id", "matches", ["fixture_id"], unique=True)
    op.create_index("ix_matches_match_date", "matches", ["match_date"], unique=False)

    # --- tickets ---
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.String(length=36), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("total_odds", sa.Float(), nullable=True),
        sa.Column("stake", sa.Float(), nullable=True),
        sa.Column("potential_gain", sa.Float(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "won", "lost", "void", name="ticketstatus"),
            nullable=True,
        ),
        sa.Column("settled_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_ticket_id", "tickets", ["ticket_id"], unique=True)
    op.create_index("ix_tickets_target_date", "tickets", ["target_date"], unique=False)

    # --- predictions ---
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("fixture_id", sa.Integer(), nullable=True),
        sa.Column("match_label", sa.String(length=200), nullable=True),
        sa.Column("competition", sa.String(length=100), nullable=True),
        sa.Column("kickoff", sa.DateTime(), nullable=True),
        sa.Column(
            "bet_type",
            sa.Enum("home", "draw", "away", "btts_yes", "btts_no", "over25", "under25", name="bettype"),
            nullable=True,
        ),
        sa.Column("odds", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("value_edge", sa.Float(), nullable=True),
        sa.Column("prob_home", sa.Float(), nullable=True),
        sa.Column("prob_draw", sa.Float(), nullable=True),
        sa.Column("prob_away", sa.Float(), nullable=True),
        sa.Column("prob_btts", sa.Float(), nullable=True),
        sa.Column("prob_over25", sa.Float(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("key_stats", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "result",
            sa.Enum("pending", "won", "lost", "void", name="predictionresult"),
            nullable=True,
        ),
        sa.Column("actual_home_score", sa.Integer(), nullable=True),
        sa.Column("actual_away_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["ticket_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_fixture_id", "predictions", ["fixture_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_predictions_fixture_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_tickets_target_date", table_name="tickets")
    op.drop_index("ix_tickets_ticket_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_matches_match_date", table_name="matches")
    op.drop_index("ix_matches_fixture_id", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_teams_name", table_name="teams")
    op.drop_index("ix_teams_api_id", table_name="teams")
    op.drop_table("teams")
    op.execute("DROP TYPE IF EXISTS matchstatus")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
    op.execute("DROP TYPE IF EXISTS bettype")
    op.execute("DROP TYPE IF EXISTS predictionresult")
