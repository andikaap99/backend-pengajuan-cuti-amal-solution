"""tambah tabel password_reset_tokens

Revision ID: a1b2c3d4e5f7
Revises: g7h8i9j0k1l2
Create Date: 2026-09-22 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_tokens',
        sa.Column('id_token', sa.Integer(), nullable=False),
        sa.Column('id_user', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('expired_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['id_user'], ['users.id_user']),
        sa.PrimaryKeyConstraint('id_token'),
    )
    op.create_index('ix_password_reset_tokens_id_token', 'password_reset_tokens', ['id_token'], unique=False)
    op.create_index('ix_password_reset_tokens_token', 'password_reset_tokens', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_password_reset_tokens_token', table_name='password_reset_tokens')
    op.drop_index('ix_password_reset_tokens_id_token', table_name='password_reset_tokens')
    op.drop_table('password_reset_tokens')
