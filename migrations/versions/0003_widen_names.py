"""Расширение full_name/username под старые данные

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("support_messages", "full_name", type_=sa.String(256), existing_nullable=True)
    op.alter_column("support_messages", "username", type_=sa.String(128), existing_nullable=True)
    op.alter_column("payments", "full_name", type_=sa.String(256), existing_nullable=True)
    op.alter_column("payments", "username", type_=sa.String(128), existing_nullable=True)
    op.alter_column("users", "username", type_=sa.String(128), existing_nullable=False)


def downgrade() -> None:
    op.alter_column("users", "username", type_=sa.String(64), existing_nullable=False)
    op.alter_column("payments", "username", type_=sa.String(64), existing_nullable=True)
    op.alter_column("payments", "full_name", type_=sa.String(128), existing_nullable=True)
    op.alter_column("support_messages", "username", type_=sa.String(64), existing_nullable=True)
    op.alter_column("support_messages", "full_name", type_=sa.String(128), existing_nullable=True)
