from datetime import date
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti_ekstra import LogCutiEkstra
from app.models.user import User


async def get_effective_sisa_cuti(user: User, tahun: int, db: AsyncSession) -> int:
    return user.sisa_cuti + user.jatah_tambahan


async def konsumsi_cuti(user: User, durasi: int, db: AsyncSession) -> None:
    sisa = durasi

    if user.jatah_tambahan > 0:
        pakai = min(user.jatah_tambahan, sisa)
        user.jatah_tambahan -= pakai
        sisa -= pakai

    if sisa > 0:
        if user.sisa_cuti < sisa:
            raise HTTPException(status_code=400, detail="Sisa cuti tidak cukup")
        user.sisa_cuti -= sisa

    db.add(user)


async def tambah_sisa_cuti(id_user: int, jumlah_hari: int, keterangan: str, id_penambah: int, db: AsyncSession) -> LogCutiEkstra:
    result_user = await db.execute(select(User).where(User.id_user == id_user))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    today = date.today()
    tahun = today.year

    log = LogCutiEkstra(
        id_user=id_user,
        id_penambah=id_penambah,
        jumlah_hari=jumlah_hari,
        keterangan=keterangan,
        added_at=today,
        tahun=tahun
    )
    db.add(log)

    user.jatah_tambahan += jumlah_hari
    db.add(user)

    await db.commit()
    await db.refresh(log)

    return log