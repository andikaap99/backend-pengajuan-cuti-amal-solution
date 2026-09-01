"""rename log_cuti columns: disetujui->diproses, approved_at->processed_at

Revision ID: 9ff93a38d6a2
Revises: 1454378a3868
Create Date: 2026-08-24 10:06:03.229377
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = '9ff93a38d6a2'
down_revision: Union[str, None] = '1454378a3868'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tambah kolom baru
    op.add_column('log_cuti', sa.Column('diproses_pm', sa.Integer(), nullable=True))
    op.add_column('log_cuti', sa.Column('diproses_hr', sa.Integer(), nullable=True))
    op.add_column('log_cuti', sa.Column('diproses_direktur', sa.Integer(), nullable=True))
    op.add_column('log_cuti', sa.Column('processed_at_pm', sa.Date(), nullable=True))
    op.add_column('log_cuti', sa.Column('processed_at_hr', sa.Date(), nullable=True))
    op.add_column('log_cuti', sa.Column('processed_at_direktur', sa.Date(), nullable=True))

    # 2. Copy data dari kolom lama ke kolom baru
    op.execute("UPDATE log_cuti SET diproses_pm = disetujui_pm WHERE disetujui_pm IS NOT NULL")
    op.execute("UPDATE log_cuti SET diproses_hr = disetujui_hr WHERE disetujui_hr IS NOT NULL")
    op.execute("UPDATE log_cuti SET diproses_direktur = disetujui_direktur WHERE disetujui_direktur IS NOT NULL")
    op.execute("UPDATE log_cuti SET processed_at_pm = approved_at_pm WHERE approved_at_pm IS NOT NULL")
    op.execute("UPDATE log_cuti SET processed_at_hr = approved_at_hr WHERE approved_at_hr IS NOT NULL")
    op.execute("UPDATE log_cuti SET processed_at_direktur = approved_at_direktur WHERE approved_at_direktur IS NOT NULL")

    # 3. Drop foreign key lama
    op.drop_constraint('log_cuti_ibfk_3', 'log_cuti', type_='foreignkey')
    op.drop_constraint('log_cuti_ibfk_2', 'log_cuti', type_='foreignkey')
    op.drop_constraint('log_cuti_ibfk_1', 'log_cuti', type_='foreignkey')

    # 4. Buat foreign key baru
    op.create_foreign_key(None, 'log_cuti', 'users', ['diproses_pm'], ['id_user'])
    op.create_foreign_key(None, 'log_cuti', 'users', ['diproses_hr'], ['id_user'])
    op.create_foreign_key(None, 'log_cuti', 'users', ['diproses_direktur'], ['id_user'])

    # 5. Drop kolom lama
    op.drop_column('log_cuti', 'disetujui_pm')
    op.drop_column('log_cuti', 'disetujui_hr')
    op.drop_column('log_cuti', 'disetujui_direktur')
    op.drop_column('log_cuti', 'approved_at_pm')
    op.drop_column('log_cuti', 'approved_at_hr')
    op.drop_column('log_cuti', 'approved_at_direktur')


def downgrade() -> None:
    # 1. Tambah kolom lama
    op.add_column('log_cuti', sa.Column('disetujui_pm', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('log_cuti', sa.Column('disetujui_hr', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('log_cuti', sa.Column('disetujui_direktur', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('log_cuti', sa.Column('approved_at_pm', sa.DATE(), nullable=True))
    op.add_column('log_cuti', sa.Column('approved_at_hr', sa.DATE(), nullable=True))
    op.add_column('log_cuti', sa.Column('approved_at_direktur', sa.DATE(), nullable=True))

    # 2. Copy data dari kolom baru ke kolom lama
    op.execute("UPDATE log_cuti SET disetujui_pm = diproses_pm WHERE diproses_pm IS NOT NULL")
    op.execute("UPDATE log_cuti SET disetujui_hr = diproses_hr WHERE diproses_hr IS NOT NULL")
    op.execute("UPDATE log_cuti SET disetujui_direktur = diproses_direktur WHERE diproses_direktur IS NOT NULL")
    op.execute("UPDATE log_cuti SET approved_at_pm = processed_at_pm WHERE processed_at_pm IS NOT NULL")
    op.execute("UPDATE log_cuti SET approved_at_hr = processed_at_hr WHERE processed_at_hr IS NOT NULL")
    op.execute("UPDATE log_cuti SET approved_at_direktur = processed_at_direktur WHERE processed_at_direktur IS NOT NULL")

    # 3. Drop foreign key baru
    op.drop_constraint(None, 'log_cuti', type_='foreignkey')
    op.drop_constraint(None, 'log_cuti', type_='foreignkey')
    op.drop_constraint(None, 'log_cuti', type_='foreignkey')

    # 4. Buat foreign key lama
    op.create_foreign_key('log_cuti_ibfk_1', 'log_cuti', 'users', ['disetujui_direktur'], ['id_user'])
    op.create_foreign_key('log_cuti_ibfk_2', 'log_cuti', 'users', ['disetujui_hr'], ['id_user'])
    op.create_foreign_key('log_cuti_ibfk_3', 'log_cuti', 'users', ['disetujui_pm'], ['id_user'])

    # 5. Drop kolom baru
    op.drop_column('log_cuti', 'diproses_pm')
    op.drop_column('log_cuti', 'diproses_hr')
    op.drop_column('log_cuti', 'diproses_direktur')
    op.drop_column('log_cuti', 'processed_at_pm')
    op.drop_column('log_cuti', 'processed_at_hr')
    op.drop_column('log_cuti', 'processed_at_direktur')
