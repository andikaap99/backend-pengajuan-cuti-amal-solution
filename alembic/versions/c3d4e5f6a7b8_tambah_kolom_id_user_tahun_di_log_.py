"""tambah kolom id_user dan tahun di log_cuti_ekstra

Revision ID: c3d4e5f6a7b8
Revises: 2b6a4322d081
Create Date: 2026-08-26 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '2b6a4322d081'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('log_cuti_ekstra', sa.Column('id_user', sa.Integer(), nullable=False))
    op.add_column('log_cuti_ekstra', sa.Column('tahun', sa.Integer(), nullable=False))
    op.create_foreign_key('fk_log_cuti_ekstra_id_user', 'log_cuti_ekstra', 'users', ['id_user'], ['id_user'])


def downgrade() -> None:
    op.drop_constraint('fk_log_cuti_ekstra_id_user', 'log_cuti_ekstra', type_='foreignkey')
    op.drop_column('log_cuti_ekstra', 'tahun')
    op.drop_column('log_cuti_ekstra', 'id_user')
