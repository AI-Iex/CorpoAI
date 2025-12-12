"""Add summary fields to sessions table.

Revision ID: 0002
Revises: 0001
Create Date: 2025-11-28

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add summary column - stores the compressed conversation history
    op.add_column(
        "sessions",
        sa.Column("summary", sa.Text(), nullable=True),
    )
    # Add summary_up_to_message_id - tracks which messages are included in summary
    op.add_column(
        "sessions",
        sa.Column("summary_up_to_message_id", UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sessions", "summary_up_to_message_id")
    op.drop_column("sessions", "summary")
