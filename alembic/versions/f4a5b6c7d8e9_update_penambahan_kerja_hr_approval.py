### ==kode baru==
"""update penambahan kerja status enum and add hr approval

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-09-09 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update enum status column untuk menambahkan nilai baru
    op.execute("ALTER TABLE log_penambahan_kerja MODIFY COLUMN status ENUM('menunggu_pm', 'disetujui_pm', 'ditolak_pm', 'menunggu_hr', 'disetujui_hr', 'ditolak_hr') NOT NULL")

    # 2. Tambah kolom alasan_penolakan
    op.add_column('log_penambahan_kerja', sa.Column('alasan_penolakan', sa.Text(), nullable=True))

    # 3. Tambah kolom processed_at_hr
    op.add_column('log_penambahan_kerja', sa.Column('processed_at_hr', sa.Date(), nullable=True))


def downgrade() -> None:
    # 1. Hapus kolom processed_at_hr
    op.drop_column('log_penambahan_kerja', 'processed_at_hr')

    # 2. Hapus kolom alasan_penolakan
    op.drop_column('log_penambahan_kerja', 'alasan_penolakan')

    # 3. Kembalikan enum status ke nilai lama
    op.execute("ALTER TABLE log_penambahan_kerja MODIFY COLUMN status ENUM('menunggu_pm', 'disetujui_pm', 'ditolak_pm') NOT NULL")
