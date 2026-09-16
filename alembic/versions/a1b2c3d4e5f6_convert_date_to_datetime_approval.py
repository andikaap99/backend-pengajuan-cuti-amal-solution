"""convert date to datetime for approval and pengajuan fields

Revision ID: a1b2c3d4e5f6
Revises: 369df610cbe9
Create Date: 2026-09-11 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '369df610cbe9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # log_cuti: tanggal_pengajuan, processed_at_hr, processed_at_direktur, edited_at
    op.alter_column('log_cuti', 'tanggal_pengajuan',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'processed_at_hr',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'processed_at_direktur',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'edited_at',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)

    # log_cuti_approval_pm: processed_at
    op.alter_column('log_cuti_approval_pm', 'processed_at',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)

    # log_penambahan_kerja: tanggal_pengajuan, processed_at_hr
    op.alter_column('log_penambahan_kerja', 'tanggal_pengajuan',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)
    op.alter_column('log_penambahan_kerja', 'processed_at_hr',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)

    # log_penambahan_kerja_approval_pm: processed_at
    op.alter_column('log_penambahan_kerja_approval_pm', 'processed_at',
               existing_type=sa.Date(),
               type_=sa.DateTime(),
               existing_nullable=True)


def downgrade() -> None:
    # log_penambahan_kerja_approval_pm: processed_at
    op.alter_column('log_penambahan_kerja_approval_pm', 'processed_at',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)

    # log_penambahan_kerja: tanggal_pengajuan, processed_at_hr
    op.alter_column('log_penambahan_kerja', 'processed_at_hr',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)
    op.alter_column('log_penambahan_kerja', 'tanggal_pengajuan',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)

    # log_cuti_approval_pm: processed_at
    op.alter_column('log_cuti_approval_pm', 'processed_at',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)

    # log_cuti: tanggal_pengajuan, processed_at_hr, processed_at_direktur, edited_at
    op.alter_column('log_cuti', 'edited_at',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'processed_at_direktur',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'processed_at_hr',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)
    op.alter_column('log_cuti', 'tanggal_pengajuan',
               existing_type=sa.DateTime(),
               type_=sa.Date(),
               existing_nullable=True)
