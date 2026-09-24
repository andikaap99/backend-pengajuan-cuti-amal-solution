"""final status direktur penambahan kerja:
tambah enum disetujui_direktur/ditolak_direktur, kolom diproses_direktur,
backfill baris yang diproses direktur dari kolom hr

Revision ID: e7a8b9c0d1e2
Revises: d1e2f3a4b5c6
Create Date: 2026-09-23 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = 'e7a8b9c0d1e2'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_ENUM = (
    "menunggu_pm", "disetujui_pm", "ditolak_pm",
    "menunggu_hr", "disetujui_hr", "ditolak_hr",
    "menunggu_direktur", "disetujui_direktur", "ditolak_direktur",
)
OLD_ENUM = (
    "menunggu_pm", "disetujui_pm", "ditolak_pm",
    "menunggu_hr", "disetujui_hr", "ditolak_hr",
    "menunggu_direktur",
)


def upgrade() -> None:
    ## 1. enum: tambah final status direktur (flow samakan dengan cuti)
    op.execute(
        "ALTER TABLE log_penambahan_kerja MODIFY COLUMN status "
        f"ENUM{NEW_ENUM} NOT NULL"
    )

    ## 2. kolom proses direktur (paritas log_cuti)
    op.add_column('log_penambahan_kerja', sa.Column('diproses_direktur', sa.Integer(), nullable=True))
    op.add_column('log_penambahan_kerja', sa.Column('processed_at_direktur', sa.DateTime(), nullable=True))
    op.create_foreign_key(None, 'log_penambahan_kerja', 'users', ['diproses_direktur'], ['id_user'])

    ## 3. backfill: baris final yang diproses user role direktur
    ##    (dulu direktur menulis status disetujui_hr/ditolak_hr + diproses_hr)
    op.execute(
        """
        UPDATE log_penambahan_kerja lpk
        JOIN users u ON u.id_user = lpk.diproses_hr
        SET lpk.status = CASE lpk.status
                WHEN 'disetujui_hr' THEN 'disetujui_direktur'
                WHEN 'ditolak_hr' THEN 'ditolak_direktur'
                ELSE lpk.status
            END,
            lpk.diproses_direktur = lpk.diproses_hr,
            lpk.processed_at_direktur = lpk.processed_at_hr,
            lpk.diproses_hr = NULL,
            lpk.processed_at_hr = NULL
        WHERE lpk.status IN ('disetujui_hr', 'ditolak_hr')
          AND u.role = 'direktur'
        """
    )


def downgrade() -> None:
    ## balikkan baris final direktur ke kolom hr dulu (sebelum enum di-resize)
    op.execute(
        """
        UPDATE log_penambahan_kerja
        SET status = CASE status
                WHEN 'disetujui_direktur' THEN 'disetujui_hr'
                WHEN 'ditolak_direktur' THEN 'ditolak_hr'
                ELSE status
            END,
            diproses_hr = diproses_direktur,
            processed_at_hr = processed_at_direktur,
            diproses_direktur = NULL,
            processed_at_direktur = NULL
        WHERE status IN ('disetujui_direktur', 'ditolak_direktur')
        """
    )

    op.drop_constraint(None, 'log_penambahan_kerja', type_='foreignkey')
    op.drop_column('log_penambahan_kerja', 'processed_at_direktur')
    op.drop_column('log_penambahan_kerja', 'diproses_direktur')

    op.execute(
        "ALTER TABLE log_penambahan_kerja MODIFY COLUMN status "
        f"ENUM{OLD_ENUM} NOT NULL"
    )
