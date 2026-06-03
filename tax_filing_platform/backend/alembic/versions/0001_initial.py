"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-03
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The declarative models are the source of truth; generated migrations should replace this bootstrap in production.
    from app.database import Base
    from app import models as _models
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    for table in ["admin_actions", "blockchain_events", "audit_logs", "payments", "documents", "filings", "users"]:
        op.drop_table(table)
