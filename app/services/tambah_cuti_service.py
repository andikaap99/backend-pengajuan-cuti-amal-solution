from datetime import date
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti_ekstra import LogCutiEkstra
from app.models.user import User


async def get_total_tambahan_cuti(user_id: int, tahun: int, db: AsyncSession) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(LogCutiEkstra.jumlah_hari), 0)).where(
            LogCutiEkstra.id_user == user_id,
            LogCutiEkstra.tahun == tahun,
        )
    )

    return result.scalar_one()


async def get_effective_sisa_cuti(user: User, tahun: int, db: AsyncSession) -> int:
    tambahan = await get_total_tambahan_cuti(user.id_user, tahun, db)

    return user.sisa_cuti + tambahan


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
    await db.commit()
    await db.refresh(log)

    return log