"""add cuti_bersama status to log_cuti enum

Revision ID: abc123def456
Revises: fdf3abe4ca8b
Create Date: 2026-09-15 10:00:00.000000
"""
from typing import Union

from alembic import op

revision: str = 'abc123def456'
down_revision: Union[str, None] = 'fdf3abe4ca8b'
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

NEW_ENUM = "'menunggu_pm','disetujui_pm','ditolak_pm','menunggu_hr','disetujui_hr','ditolak_hr','menunggu_direktur','disetujui_direktur','ditolak_direktur','cuti_bersama'"

def upgrade() -> None:
    op.execute(f"ALTER TABLE log_cuti MODIFY COLUMN status ENUM({NEW_ENUM}) NOT NULL")

def downgrade() -> None:
    OLD_ENUM = "'menunggu_pm','disetujui_pm','ditolak_pm','menunggu_hr','disetujui_hr','ditolak_hr','menunggu_direktur','disetujui_direktur','ditolak_direktur'"
    op.execute(f"ALTER TABLE log_cuti MODIFY COLUMN status ENUM({OLD_ENUM}) NOT NULL")
