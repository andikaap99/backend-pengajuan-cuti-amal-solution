from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User


FINAL_APPROVED_STATUSES = ["disetujui_hr", "disetujui_direktur"]


async def aktifkan_user_selesai_cuti(db: AsyncSession) -> int:
    """cek semua user yang statusnya 'Cuti', kalau tidak ada cuti aktif hari ini → balik ke 'Aktif'"""
    today = date.today()

    result_users = await db.execute(
        select(User).where(User.status == "Cuti")
    )
    users = result_users.scalars().all()

    if not users:
        return 0

    count = 0
    for user in users:
        # tentukan status approved sesuai role
        if user.role == "hr":
            approved_statuses = ["disetujui_direktur"]
        else:
            approved_statuses = FINAL_APPROVED_STATUSES

        # cek apakah ada cuti yang sedang berjalan hari ini
        result_active = await db.execute(
            select(LogCuti).where(
                LogCuti.id_user == user.id_user,
                LogCuti.status.in_(approved_statuses),
                LogCuti.tanggal_mulai <= today,
                LogCuti.tanggal_selesai >= today,
            )
        )
        active_leave = result_active.scalars().first()

        if not active_leave:
            user.status = "Aktif"
            db.add(user)
            count += 1

    await db.commit()
    return count
