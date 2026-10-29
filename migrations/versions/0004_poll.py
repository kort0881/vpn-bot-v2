"""Таблица ответов на опрос

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "poll_answers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("poll_id", sa.String(64), index=True),
        sa.Column("telegram_id", sa.BigInteger, index=True),
        sa.Column("username", sa.String(128)),
        sa.Column("full_name", sa.String(256)),
        sa.Column("option_ids", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("poll_answers")
