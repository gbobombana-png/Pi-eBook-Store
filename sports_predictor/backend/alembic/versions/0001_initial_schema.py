"""Initial schema — teams, matches, predictions, tickets

Revision ID: 0001
Revises:
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

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
        sa.Column("league", sa.String(length=100), nullable=True),
        sa.Column("logo_url", sa.String(length=255), nullable=True),
        sa.Column("home_goals_scored_avg", sa.Float(), nullable=True),
        sa.Column("home_goals_conceded_avg", sa.Float(), nullable=True),
        sa.Column("away_goals_scored_avg", sa.Float(), nullable=True),
        sa.Column("away_goals_conceded_avg", sa.Float(), nullable=True),
        sa.Column("home_xg_avg", sa.Float(), nullable=True),
        sa.Column("away_xg_avg", sa.Float(), nullable=True),
        sa.Column("home_xga_avg", sa.Float(), nullable=True),
        sa.Column("away_xga_avg", sa.Float(), nullable=True),
        sa.Column("home_wins_pct", sa.Float(), nullable=True),
        sa.Column("away_wins_pct", sa.Float(), nullable=True),
        sa.Column("btts_pct", sa.Float(), nullable=True),
        sa.Column("over25_pct", sa.Float(), nullable=True),
        sa.Column("corners_avg", sa.Float(), nullable=True),
        sa.Column("shots_on_target_avg", sa.Float(), nullable=True),
        sa.Column("possession_avg", sa.Float(), nullable=True),
        sa.Column("form_last5", sa.String(length=5), nullable=True),
        sa.Column("form_last10", sa.String(length=10), nullable=True),
        sa.Column("elo_rating", sa.Float(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_api_id", "teams", ["api_id"], unique=True)
    op.create_index("ix_teams_id", "teams", ["id"], unique=False)
    op.create_index("ix_teams_name", "teams", ["name"], unique=False)

    # --- matches (status as VARCHAR, not native enum) ---
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("api_id", sa.Integer(), nullable=True),
        sa.Column("home_team_id", sa.Integer(), nullable=False),
        sa.Column("away_team_id", sa.Integer(), nullable=False),
        sa.Column("competition", sa.String(length=100), nullable=True),
        sa.Column("competition_id", sa.Integer(), nullable=True),
        sa.Column("season", sa.String(length=10), nullable=True),
        sa.Column("round", sa.String(length=50), nullable=True),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column("venue", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=9), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("home_score_ht", sa.Integer(), nullable=True),
        sa.Column("away_score_ht", sa.Integer(), nullable=True),
        sa.Column("home_xg", sa.Float(), nullable=True),
        sa.Column("away_xg", sa.Float(), nullable=True),
        sa.Column("home_shots", sa.Integer(), nullable=True),
        sa.Column("away_shots", sa.Integer(), nullable=True),
        sa.Column("home_shots_on", sa.Integer(), nullable=True),
        sa.Column("away_shots_on", sa.Integer(), nullable=True),
        sa.Column("home_possession", sa.Float(), nullable=True),
        sa.Column("away_possession", sa.Float(), nullable=True),
        sa.Column("home_corners", sa.Integer(), nullable=True),
        sa.Column("away_corners", sa.Integer(), nullable=True),
        sa.Column("home_yellow", sa.Integer(), nullable=True),
        sa.Column("away_yellow", sa.Integer(), nullable=True),
        sa.Column("home_red", sa.Integer(), nullable=True),
        sa.Column("away_red", sa.Integer(), nullable=True),
        sa.Column("weather", sa.String(length=50), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=True),
        sa.Column("referee", sa.String(length=100), nullable=True),
        sa.Column("attendance", sa.Integer(), nullable=True),
        sa.Column("extra_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_matches_api_id", "matches", ["api_id"], unique=True)
    op.create_index("ix_matches_id", "matches", ["id"], unique=False)
    op.create_index("ix_matches_kickoff", "matches", ["kickoff"], unique=False)

    # --- tickets ---
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("total_odds", sa.Float(), nullable=True),
        sa.Column("stake", sa.Float(), server_default="1.0", nullable=True),
        sa.Column("potential_gain", sa.Float(), nullable=True),
        sa.Column("result", sa.String(length=7), server_default="pending", nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_id", "tickets", ["id"], unique=False)
    op.create_index("ix_tickets_target_date", "tickets", ["target_date"], unique=False)
    op.create_index("ix_tickets_generated_at", "tickets", ["generated_at"], unique=False)

    # --- predictions ---
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), sa.ForeignKey("tickets.id"), nullable=True),
        sa.Column("fixture_id", sa.Integer(), nullable=True),
        sa.Column("match_label", sa.String(length=200), nullable=True),
        sa.Column("competition", sa.String(length=100), nullable=True),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=True),
        sa.Column("bet_type", sa.String(length=20), nullable=False),
        sa.Column("odds", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("value_edge", sa.Float(), nullable=True),
        sa.Column("prob_home", sa.Float(), nullable=True),
        sa.Column("prob_draw", sa.Float(), nullable=True),
        sa.Column("prob_away", sa.Float(), nullable=True),
        sa.Column("prob_btts", sa.Float(), nullable=True),
        sa.Column("prob_over25", sa.Float(), nullable=True),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("key_stats", sa.JSON(), nullable=True),
        sa.Column("result", sa.String(length=7), server_default="pending", nullable=True),
        sa.Column("actual_home_score", sa.Integer(), nullable=True),
        sa.Column("actual_away_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_id", "predictions", ["id"], unique=False)
    op.create_index("ix_predictions_fixture_id", "predictions", ["fixture_id"], unique=False)
    op.create_index("ix_predictions_ticket_id", "predictions", ["ticket_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_predictions_ticket_id", table_name="predictions")
    op.drop_index("ix_predictions_fixture_id", table_name="predictions")
    op.drop_index("ix_predictions_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_tickets_generated_at", table_name="tickets")
    op.drop_index("ix_tickets_target_date", table_name="tickets")
    op.drop_index("ix_tickets_id", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_matches_kickoff", table_name="matches")
    op.drop_index("ix_matches_id", table_name="matches")
    op.drop_index("ix_matches_api_id", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_teams_name", table_name="teams")
    op.drop_index("ix_teams_id", table_name="teams")
    op.drop_index("ix_teams_api_id", table_name="teams")
    op.drop_table("teams")
