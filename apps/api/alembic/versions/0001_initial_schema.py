"""initial schema — tenancy, channels, content, and AI layer

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-09

Baseline migration. Enables the pgvector extension, then creates the full schema from the
SQLAlchemy metadata. Subsequent migrations are incremental op.* diffs via autogenerate.
"""

from typing import Sequence, Union

from alembic import op

from app.db.base import Base
import app.models  # noqa: F401  (registers all tables on Base.metadata)

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector must exist before any Vector columns are created.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=False)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=False)
    op.execute("DROP EXTENSION IF EXISTS vector")
