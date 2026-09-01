"""merge holiday cols

Revision ID: 1454378a3868
Revises: 48fa8bea1e74, f1a2b3c4d5e6
Create Date: 2026-08-23 21:45:39.691980
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1454378a3868'
down_revision: Union[str, None] = ('48fa8bea1e74', 'f1a2b3c4d5e6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
