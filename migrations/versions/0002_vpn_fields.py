"""VPN-поля пользователя + payments/support_messages/stats

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(64), server_default="", nullable=False))
    op.add_column("users", sa.Column("email", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("client_uuid", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("vless_link", sa.Text, nullable=True))
    op.add_column(
        "users",
        sa.Column("links", postgresql.JSONB, server_default="[]", nullable=True),
    )
    op.add_column("users", sa.Column("total_bytes", sa.BigInteger, server_default="0", nullable=False))
    op.add_column("users", sa.Column("used_bytes", sa.Float, server_default="0", nullable=False))
    op.add_column("users", sa.Column("expiry_at", sa.BigInteger, server_default="0", nullable=False))
    op.add_column("users", sa.Column("is_active", sa.Boolean, server_default="true", nullable=False))
    op.add_column("users", sa.Column("banned", sa.Boolean, server_default="false", nullable=False))
    op.add_column(
        "users", sa.Column("unsubscribed_at", sa.BigInteger, server_default="0", nullable=False)
    )
    op.add_column("users", sa.Column("channel_step", sa.Integer, server_default="0", nullable=False))
    op.add_column("users", sa.Column("chosen_channel", sa.Integer, server_default="-1", nullable=False))
    op.add_column("users", sa.Column("ban_reason", sa.Text, server_default="", nullable=False))
    op.add_column("users", sa.Column("ban_at", sa.BigInteger, server_default="0", nullable=False))
    op.add_column("users", sa.Column("balance", sa.Integer, server_default="0", nullable=False))

    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, nullable=False, index=True),
        sa.Column("username", sa.String(64), server_default=""),
        sa.Column("full_name", sa.String(128), server_default=""),
        sa.Column("amount", sa.Integer, server_default="0"),
        sa.Column("method", sa.String(32), server_default="sbp"),
        sa.Column("status", sa.String(16), server_default="claimed"),
        sa.Column("created_at", sa.BigInteger, server_default="0"),
        sa.Column("confirmed_at", sa.BigInteger, server_default="0"),
    )

    op.create_table(
        "support_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, index=True),
        sa.Column("username", sa.String(64)),
        sa.Column("full_name", sa.String(128)),
        sa.Column("text", sa.Text),
        sa.Column("created_at", sa.BigInteger, server_default="0"),
        sa.Column("status", sa.String(16), server_default="new"),
    )

    op.create_table(
        "stats",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", sa.BigInteger, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("stats")
    op.drop_table("support_messages")
    op.drop_table("payments")
    op.drop_index("ix_users_email", table_name="users")
    for col in (
        "balance", "ban_at", "ban_reason", "chosen_channel", "channel_step",
        "unsubscribed_at", "banned", "is_active", "expiry_at", "used_bytes",
        "total_bytes", "links", "vless_link", "client_uuid", "email", "username",
    ):
        op.drop_column("users", col)
