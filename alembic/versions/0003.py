"""Add is_enabled field to documents table.

Revision ID: 0003
Revises: 0002
Create Date: 2025-12-19

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_enabled column - controls whether document is used in RAG
    op.add_column(
        "documents",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    # Add index for efficient filtering of enabled documents
    op.create_index(
        "ix_documents_is_enabled",
        "documents",
        ["is_enabled"],
    )


def downgrade() -> None:
    op.drop_index("ix_documents_is_enabled", table_name="documents")
    op.drop_column("documents", "is_enabled")
