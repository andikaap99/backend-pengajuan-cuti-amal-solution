from datetime import date
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti_ekstra import LogCutiEkstra
from app.models.user import User


async def get_jatah_cuti_awal(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(User.total_cuti)))
    return result.scalar() or 12


async def konsumsi_cuti(user: User, durasi: int, db: AsyncSession) -> None:
    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=400, detail="Sisa cuti tidak cukup")
    user.sisa_cuti -= durasi
    db.add(user)


async def tambah_sisa_cuti_semua(jumlah_hari: int, keterangan: str, id_penambah: int, db: AsyncSession) -> list[LogCutiEkstra]:
    result_users = await db.execute(select(User).where(User.role.in_(["karyawan", "pm", "hr_manager", "staff_hr"])))
    users = result_users.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="Tidak ada user ditemukan")

    if jumlah_hari == 0:
        raise HTTPException(status_code=400, detail="Jumlah hari tidak boleh 0")

    if jumlah_hari < 0:
        user_minus = next((u for u in users if u.sisa_cuti + jumlah_hari < 0), None)
        if user_minus is not None:
            raise HTTPException(
                status_code=400,
                detail=f"Sisa cuti tidak mencukupi untuk user {user_minus.nama}",
            )

    today = date.today()
    tahun = today.year
    logs = []

    for user in users:
        log = LogCutiEkstra(
            id_user=user.id_user,
            id_penambah=id_penambah,
            jumlah_hari=jumlah_hari,
            keterangan=keterangan,
            added_at=today,
            tahun=tahun
        )
        db.add(log)
        user.sisa_cuti += jumlah_hari
        user.total_cuti += jumlah_hari
        db.add(user)
        logs.append(log)

    await db.commit()
    for log in logs:
        await db.refresh(log)

    return logs
