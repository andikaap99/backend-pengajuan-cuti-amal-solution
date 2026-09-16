### ==kode baru==
"""update many-to-many karyawan-pm

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-09-09 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Buat tabel user_pm (junction table)
    op.create_table(
        'user_pm',
        sa.Column('id_user_pm', sa.Integer(), nullable=False),
        sa.Column('id_karyawan', sa.Integer(), nullable=False),
        sa.Column('id_pm', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['id_karyawan'], ['users.id_user']),
        sa.ForeignKeyConstraint(['id_pm'], ['users.id_user']),
        sa.PrimaryKeyConstraint('id_user_pm')
    )
    op.create_index('ix_user_pm_id_user_pm', 'user_pm', ['id_user_pm'], unique=False)

    # 2. Buat tabel log_cuti_approval_pm
    op.create_table(
        'log_cuti_approval_pm',
        sa.Column('id_approval', sa.Integer(), nullable=False),
        sa.Column('id_log_cuti', sa.Integer(), nullable=False),
        sa.Column('id_pm', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('menunggu', 'disetujui', 'ditolak'), nullable=False),
        sa.Column('processed_at', sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(['id_log_cuti'], ['log_cuti.id_log_cuti']),
        sa.ForeignKeyConstraint(['id_pm'], ['users.id_user']),
        sa.PrimaryKeyConstraint('id_approval')
    )
    op.create_index('ix_log_cuti_approval_pm_id_approval', 'log_cuti_approval_pm', ['id_approval'], unique=False)

    # 3. Migrate data lama: insert id_pm dari users ke user_pm
    op.execute("""
        INSERT INTO user_pm (id_karyawan, id_pm)
        SELECT id_user, id_pm FROM users WHERE id_pm IS NOT NULL
    """)

    # 4. Hapus kolom id_pm dari users
    op.drop_constraint('users_ibfk_2', 'users', type_='foreignkey')
    op.drop_column('users', 'id_pm')

    # 5. Hapus kolom diproses_pm dan processed_at_pm dari log_cuti
    op.drop_constraint('log_cuti_ibfk_6', 'log_cuti', type_='foreignkey')
    op.drop_column('log_cuti', 'diproses_pm')
    op.drop_column('log_cuti', 'processed_at_pm')


def downgrade() -> None:
    # 1. Kembalikan kolom diproses_pm dan processed_at_pm ke log_cuti
    op.add_column('log_cuti', sa.Column('processed_at_pm', sa.Date(), nullable=True))
    op.add_column('log_cuti', sa.Column('diproses_pm', sa.Integer(), nullable=True))
    op.create_foreign_key('log_cuti_ibfk_4', 'log_cuti', 'users', ['diproses_pm'], ['id_user'])

    # 2. Kembalikan kolom id_pm ke users
    op.add_column('users', sa.Column('id_pm', sa.Integer(), nullable=True))
    op.create_foreign_key('users_ibfk_2', 'users', 'users', ['id_pm'], ['id_user'])

    # 3. Hapus tabel log_cuti_approval_pm
    op.drop_index('ix_log_cuti_approval_pm_id_approval', table_name='log_cuti_approval_pm')
    op.drop_table('log_cuti_approval_pm')

    # 4. Hapus tabel user_pm
    op.drop_index('ix_user_pm_id_user_pm', table_name='user_pm')
    op.drop_table('user_pm')
