### ==kode baru==
"""update many-to-many penambahan kerja approval pm

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-09-09 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Buat tabel log_penambahan_kerja_approval_pm
    op.create_table(
        'log_penambahan_kerja_approval_pm',
        sa.Column('id_approval', sa.Integer(), nullable=False),
        sa.Column('id_pengajuan_kerja', sa.Integer(), nullable=False),
        sa.Column('id_pm', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('menunggu', 'disetujui', 'ditolak'), nullable=False),
        sa.Column('processed_at', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['id_pengajuan_kerja'], ['log_penambahan_kerja.id_pengajuan_kerja']),
        sa.ForeignKeyConstraint(['id_pm'], ['users.id_user']),
        sa.PrimaryKeyConstraint('id_approval')
    )
    op.create_index('ix_log_penambahan_kerja_approval_pm_id_approval', 'log_penambahan_kerja_approval_pm', ['id_approval'], unique=False)

    # 2. Migrate data lama: insert approval dari log_penambahan_kerja yang sudah diproses
    op.execute("""
        INSERT INTO log_penambahan_kerja_approval_pm (id_pengajuan_kerja, id_pm, status, processed_at)
        SELECT id_pengajuan_kerja, diproses_pm, 
               CASE WHEN status = 'disetujui_pm' THEN 'disetujui' WHEN status = 'ditolak_pm' THEN 'ditolak' ELSE 'menunggu' END,
               processed_at_pm
        FROM log_penambahan_kerja WHERE diproses_pm IS NOT NULL
    """)

    # 3. Hapus kolom diproses_pm dan processed_at_pm dari log_penambahan_kerja
    op.execute("ALTER TABLE log_penambahan_kerja DROP FOREIGN KEY log_penambahan_kerja_ibfk_1")
    op.drop_column('log_penambahan_kerja', 'diproses_pm')
    op.drop_column('log_penambahan_kerja', 'processed_at_pm')


def downgrade() -> None:
    # 1. Kembalikan kolom diproses_pm dan processed_at_pm ke log_penambahan_kerja
    op.add_column('log_penambahan_kerja', sa.Column('processed_at_pm', sa.Date(), nullable=True))
    op.add_column('log_penambahan_kerja', sa.Column('diproses_pm', sa.Integer(), nullable=True))
    op.create_foreign_key('log_penambahan_kerja_ibfk_2', 'log_penambahan_kerja', 'users', ['diproses_pm'], ['id_user'])

    # 2. Hapus tabel log_penambahan_kerja_approval_pm
    op.drop_index('ix_log_penambahan_kerja_approval_pm_id_approval', table_name='log_penambahan_kerja_approval_pm')
    op.drop_table('log_penambahan_kerja_approval_pm')
