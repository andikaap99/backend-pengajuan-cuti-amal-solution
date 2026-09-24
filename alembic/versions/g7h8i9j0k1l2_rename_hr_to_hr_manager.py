"""rename hr role to hr_manager

Revision ID: g7h8i9j0k1l2
Revises: abc123def456
Create Date: 2026-09-21 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text
from alembic import op

revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Tambah 'hr_manager' ke enum (masih ada 'hr')
    op.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('karyawan', 'pm', 'hr', 'hr_manager', 'direktur', 'staff_hr') NOT NULL"))

    # Step 2: Update data dari 'hr' ke 'hr_manager'
    op.execute(text("UPDATE users SET role = 'hr_manager' WHERE role = 'hr'"))

    # Step 3: Hapus 'hr' dari enum
    op.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('karyawan', 'pm', 'hr_manager', 'direktur', 'staff_hr') NOT NULL"))


def downgrade() -> None:
    # Step 1: Tambah 'hr' ke enum (masih ada 'hr_manager')
    op.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('karyawan', 'pm', 'hr', 'hr_manager', 'direktur', 'staff_hr') NOT NULL"))

    # Step 2: Update data dari 'hr_manager' ke 'hr'
    op.execute(text("UPDATE users SET role = 'hr' WHERE role = 'hr_manager'"))

    # Step 3: Hapus 'hr_manager' dari enum
    op.execute(text("ALTER TABLE users MODIFY COLUMN role ENUM('karyawan', 'pm', 'hr', 'direktur', 'staff_hr') NOT NULL"))
