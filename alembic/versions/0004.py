"""Create tools table for dynamic tool management.

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-19

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("parameters", JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("http_method", sa.String(10), nullable=True, server_default="POST"),
        sa.Column("headers", JSONB(), nullable=True),
        sa.Column("timeout", sa.Integer(), nullable=True, server_default="30"),
        sa.Column("required_permissions", JSONB(), server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_tools_enabled", "tools", ["is_enabled"])
    op.create_index("ix_tools_builtin", "tools", ["is_builtin"])


def downgrade() -> None:
    op.drop_index("ix_tools_builtin", table_name="tools")
    op.drop_index("ix_tools_enabled", table_name="tools")
    op.drop_table("tools")
