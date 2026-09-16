"""tambah tanggal_pengajuan di log_penambahan_kerja

Revision ID: f5g6h7i8j9k0
Revises: e3f4a5b6c7d8
Create Date: 2026-09-10 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f5g6h7i8j9k0'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('log_penambahan_kerja', sa.Column('tanggal_pengajuan', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('log_penambahan_kerja', 'tanggal_pengajuan')
