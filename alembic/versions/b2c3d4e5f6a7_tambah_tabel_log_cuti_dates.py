"""tambah tabel log_cuti_dates untuk tanggal cuti individual

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-09-22 12:00:00.000000
"""
from typing import Sequence, Union
from datetime import timedelta

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    ## 1. Buat tabel log_cuti_dates
    op.create_table(
        'log_cuti_dates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_log_cuti', sa.Integer(), nullable=False),
        sa.Column('tanggal', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['id_log_cuti'], ['log_cuti.id_log_cuti'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_log_cuti_dates_id', 'log_cuti_dates', ['id'], unique=False)
    op.create_index('ix_log_cuti_dates_tanggal', 'log_cuti_dates', ['tanggal'], unique=False)
    op.create_index('ix_log_cuti_dates_id_log_cuti', 'log_cuti_dates', ['id_log_cuti'], unique=False)

    ## 2. Migrate data existing: insert individual dates (exclude weekend Sabtu=5, Minggu=6)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id_log_cuti, tanggal_mulai, tanggal_selesai FROM log_cuti")
    )
    rows = result.fetchall()

    insert_values = []
    for id_log_cuti, tanggal_mulai, tanggal_selesai in rows:
        if not tanggal_mulai or not tanggal_selesai:
            continue
        current = tanggal_mulai
        while current <= tanggal_selesai:
            ## skip weekend (5=Saturday, 6=Sunday)
            if current.weekday() not in (5, 6):
                insert_values.append({'id_log_cuti': id_log_cuti, 'tanggal': current})
            current += timedelta(days=1)

    if insert_values:
        op.bulk_insert(
            sa.table('log_cuti_dates',
                sa.column('id_log_cuti', sa.Integer),
                sa.column('tanggal', sa.Date),
            ),
            insert_values
        )


def downgrade() -> None:
    op.drop_index('ix_log_cuti_dates_id_log_cuti', table_name='log_cuti_dates')
    op.drop_index('ix_log_cuti_dates_tanggal', table_name='log_cuti_dates')
    op.drop_index('ix_log_cuti_dates_id', table_name='log_cuti_dates')
    op.drop_table('log_cuti_dates')
