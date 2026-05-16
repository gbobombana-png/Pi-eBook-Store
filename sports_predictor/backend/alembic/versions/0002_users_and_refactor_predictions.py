"""Add users table + refactor predictions/tickets schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-16 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=100), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # --- drop old predictions + tickets and recreate (schema changed significantly) ---
    op.drop_table("predictions")
    op.drop_table("tickets")
    op.execute("DROP TYPE IF EXISTS predictionresult")
    op.execute("DROP TYPE IF EXISTS ticketstatus")
    op.execute("DROP TYPE IF EXISTS bettype")

    op.execute("CREATE TYPE predictionresult AS ENUM ('pending', 'win', 'loss', 'void')")

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.Integer(), nullable=True),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("total_odds", sa.Float(), nullable=True),
        sa.Column("stake", sa.Float(), server_default="1.0"),
        sa.Column("potential_gain", sa.Float(), nullable=True),
        sa.Column("result", sa.Enum("pending", "win", "loss", "void", name="predictionresult"),
                  server_default="pending"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tickets_target_date", "tickets", ["target_date"])
    op.create_index("ix_tickets_generated_at", "tickets", ["generated_at"])

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
        sa.Column("result", sa.Enum("pending", "win", "loss", "void", name="predictionresult"),
                  server_default="pending"),
        sa.Column("actual_home_score", sa.Integer(), nullable=True),
        sa.Column("actual_away_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_predictions_fixture_id", "predictions", ["fixture_id"])
    op.create_index("ix_predictions_ticket_id", "predictions", ["ticket_id"])


def downgrade() -> None:
    op.drop_index("ix_predictions_ticket_id", table_name="predictions")
    op.drop_index("ix_predictions_fixture_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_tickets_generated_at", table_name="tickets")
    op.drop_index("ix_tickets_target_date", table_name="tickets")
    op.drop_table("tickets")
    op.execute("DROP TYPE IF EXISTS predictionresult")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
