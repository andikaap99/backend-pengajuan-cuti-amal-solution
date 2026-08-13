from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.log_cuti import LogCutiCreate


async def create_leave_request(data: LogCutiCreate, user_id: int, db: AsyncSession) -> LogCuti:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    durasi = (data.tanggal_selesai - data.tanggal_mulai).days + 1

    if durasi <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tanggal tidak valid")

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak cukup")

    if data.pengganti == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pengganti tidak boleh diri sendiri")

    pengganti = await db.execute(select(User).where(User.id_user == data.pengganti))
    if not pengganti.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User pengganti tidak ditemukan")

    match user.role:
        case "karyawan":
            status = "menunggu_pm"
        case "pm":
            status = "menunggu_hr"
        case "hr":
            status = "menunggu_direktur"

    log = LogCuti(
        id_user=user_id,
        jenis_cuti=data.jenis_cuti,
        tanggal_mulai=data.tanggal_mulai,
        tanggal_selesai=data.tanggal_selesai,
        keterangan_cuti=data.keterangan,
        pengganti=data.pengganti,
        status=status,
    )
    db.add(log)

    user.sisa_cuti -= durasi
    db.add(user)

    await db.commit()
    await db.refresh(log)
    return log
