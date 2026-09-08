"""add jatah_tambahan to users

Revision ID: b8c9d0e1f2a3
Revises: 7a34d37bb74e
Create Date: 2026-09-07 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8c9d0e1f2a3'
down_revision: Union[str, None] = '7a34d37bb74e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('jatah_tambahan', sa.Integer(), server_default='0', nullable=False))

    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE users u
        SET jatah_tambahan = (
            SELECT COALESCE(SUM(jumlah_hari), 0)
            FROM log_cuti_ekstra le
            WHERE le.id_user = u.id_user
        )
    """))


def downgrade() -> None:
    op.drop_column('users', 'jatah_tambahan')
