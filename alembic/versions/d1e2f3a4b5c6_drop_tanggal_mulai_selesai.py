"""drop tanggal_mulai/tanggal_selesai dari log_cuti & log_penambahan_kerja,
tambah tabel log_penambahan_kerja_dates (tanggal individual)

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a7
Create Date: 2026-09-23 12:00:00.000000
"""
from typing import Sequence, Union
from datetime import timedelta

from alembic import op
import sqlalchemy as sa


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _expand(start, end):
    values = []
    current = start
    while current <= end:
        values.append(current)
        current += timedelta(days=1)
    return values


def upgrade() -> None:
    ## 1. tabel tanggal individual untuk penambahan kerja
    op.create_table(
        'log_penambahan_kerja_dates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('id_pengajuan_kerja', sa.Integer(), nullable=False),
        sa.Column('tanggal', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['id_pengajuan_kerja'], ['log_penambahan_kerja.id_pengajuan_kerja'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_log_penambahan_kerja_dates_id', 'log_penambahan_kerja_dates', ['id'], unique=False)
    op.create_index('ix_log_penambahan_kerja_dates_tanggal', 'log_penambahan_kerja_dates', ['tanggal'], unique=False)
    op.create_index('ix_log_penambahan_kerja_dates_id_pengajuan_kerja', 'log_penambahan_kerja_dates', ['id_pengajuan_kerja'], unique=False)

    conn = op.get_bind()

    ## 2. backfill tanggal penambahan kerja dari range lama (semua hari)
    rows = conn.execute(
        sa.text("SELECT id_pengajuan_kerja, tanggal_mulai, tanggal_selesai FROM log_penambahan_kerja")
    ).fetchall()

    insert_kerja = []
    for id_pengajuan_kerja, tanggal_mulai, tanggal_selesai in rows:
        if not tanggal_mulai or not tanggal_selesai:
            continue
        for t in _expand(tanggal_mulai, tanggal_selesai):
            insert_kerja.append({'id_pengajuan_kerja': id_pengajuan_kerja, 'tanggal': t})

    if insert_kerja:
        op.bulk_insert(
            sa.table(
                'log_penambahan_kerja_dates',
                sa.column('id_pengajuan_kerja', sa.Integer),
                sa.column('tanggal', sa.Date),
            ),
            insert_kerja,
        )

    ## 3. backfill log_cuti yang belum punya baris tanggal (mis. cuti_bersama),
    ##    expand penuh dari range lama (tanpa skip weekend)
    rows = conn.execute(sa.text(
        """
        SELECT lc.id_log_cuti, lc.tanggal_mulai, lc.tanggal_selesai
        FROM log_cuti lc
        WHERE NOT EXISTS (
            SELECT 1 FROM log_cuti_dates d WHERE d.id_log_cuti = lc.id_log_cuti
        )
        """
    )).fetchall()

    insert_cuti = []
    for id_log_cuti, tanggal_mulai, tanggal_selesai in rows:
        if not tanggal_mulai or not tanggal_selesai:
            continue
        for t in _expand(tanggal_mulai, tanggal_selesai):
            insert_cuti.append({'id_log_cuti': id_log_cuti, 'tanggal': t})

    if insert_cuti:
        op.bulk_insert(
            sa.table(
                'log_cuti_dates',
                sa.column('id_log_cuti', sa.Integer),
                sa.column('tanggal', sa.Date),
            ),
            insert_cuti,
        )

    ## 4. drop kolom range
    op.drop_column('log_cuti', 'tanggal_mulai')
    op.drop_column('log_cuti', 'tanggal_selesai')
    op.drop_column('log_penambahan_kerja', 'tanggal_mulai')
    op.drop_column('log_penambahan_kerja', 'tanggal_selesai')


def downgrade() -> None:
    op.add_column('log_cuti', sa.Column('tanggal_mulai', sa.Date(), nullable=True))
    op.add_column('log_cuti', sa.Column('tanggal_selesai', sa.Date(), nullable=True))
    op.add_column('log_penambahan_kerja', sa.Column('tanggal_mulai', sa.Date(), nullable=True))
    op.add_column('log_penambahan_kerja', sa.Column('tanggal_selesai', sa.Date(), nullable=True))

    conn = op.get_bind()

    conn.execute(sa.text(
        """
        UPDATE log_cuti lc
        SET tanggal_mulai = (SELECT MIN(d.tanggal) FROM log_cuti_dates d WHERE d.id_log_cuti = lc.id_log_cuti),
            tanggal_selesai = (SELECT MAX(d.tanggal) FROM log_cuti_dates d WHERE d.id_log_cuti = lc.id_log_cuti)
        """
    ))
    conn.execute(sa.text(
        """
        UPDATE log_penambahan_kerja lk
        SET tanggal_mulai = (SELECT MIN(d.tanggal) FROM log_penambahan_kerja_dates d WHERE d.id_pengajuan_kerja = lk.id_pengajuan_kerja),
            tanggal_selesai = (SELECT MAX(d.tanggal) FROM log_penambahan_kerja_dates d WHERE d.id_pengajuan_kerja = lk.id_pengajuan_kerja)
        """
    ))

    op.drop_index('ix_log_penambahan_kerja_dates_id_pengajuan_kerja', table_name='log_penambahan_kerja_dates')
    op.drop_index('ix_log_penambahan_kerja_dates_tanggal', table_name='log_penambahan_kerja_dates')
    op.drop_index('ix_log_penambahan_kerja_dates_id', table_name='log_penambahan_kerja_dates')
    op.drop_table('log_penambahan_kerja_dates')
