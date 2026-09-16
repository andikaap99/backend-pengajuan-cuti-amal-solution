"""empty message

Revision ID: 6c5da0c37047
Revises: f4a5b6c7d8e9, f5g6h7i8j9k0
Create Date: 2026-09-10 10:21:22.515538
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6c5da0c37047'
down_revision: Union[str, None] = ('f4a5b6c7d8e9', 'f5g6h7i8j9k0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
