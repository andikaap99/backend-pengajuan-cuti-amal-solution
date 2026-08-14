from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.log_cuti import LogCutiCreate, RiwayatCutiOut


async def create_leave_request(data: LogCutiCreate, user_id: int, db: AsyncSession) -> LogCuti:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if data.tanggal_mulai < date.today():
        raise HTTPException(status_code=400, detail="Tanggal cuti tidak boleh di masa lalu")

    if (data.tanggal_mulai - date.today()).days < 10:
        raise HTTPException(status_code=400, detail="Maksimal pengajuan 10 hari sebelum hari pertama cuti")

    durasi = (data.tanggal_selesai - data.tanggal_mulai).days + 1

    if durasi <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tanggal tidak valid")

    if durasi > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maksimal cuti selama 4 hari")

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak cukup")

    if data.pengganti == user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pengganti tidak boleh diri sendiri")

    pengganti = await db.execute(select(User).where(User.id_user == data.pengganti))
    if not pengganti.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User pengganti tidak ditemukan")

    if user.role == "direktur":
        raise HTTPException(status_code=400, detail="Direktur tidak bisa mengajukan cuti")

    match user.role:
        case "karyawan":
            if user.id_departemen != 1:
                status_pengajuan = "menunggu_pm"
            else:
                status_pengajuan = "menunggu_hr"
        case "pm":
            status_pengajuan = "menunggu_hr"
        case "hr":
            status_pengajuan = "menunggu_direktur"

    log = LogCuti(
        id_user=user_id,
        jenis_cuti="cuti tahunan",
        tanggal_mulai=data.tanggal_mulai,
        tanggal_selesai=data.tanggal_selesai,
        keterangan_cuti=data.keterangan,
        pengganti=data.pengganti,
        status=status_pengajuan,
    )
    db.add(log)

    user.sisa_cuti -= durasi
    db.add(user)

    await db.commit()
    await db.refresh(log)
    return log


async def get_all_leaves(db: AsyncSession) -> list[LogCuti]:
    result = await db.execute(select(LogCuti))
    return result.scalars().all()


async def get_my_leaves(user_id: int, db: AsyncSession) -> list[RiwayatCutiOut]:
    result = await db.execute(select(LogCuti).where(LogCuti.id_user == user_id))
    logs = result.scalars().all()

    list_pengganti_ids = [log.pengganti for log in logs]
    result_pengganti = await db.execute(select(User).where(User.id_user.in_(list_pengganti_ids)))
    map_pengganti = {u.id_user: u.nama for u in result_pengganti.scalars().all()}

    return [
        RiwayatCutiOut(
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            nama_pengganti=map_pengganti.get(log.pengganti, "Tidak diketahui"),
            keterangan=log.keterangan_cuti,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            status=log.status,
        )
        for log in logs
    ]
