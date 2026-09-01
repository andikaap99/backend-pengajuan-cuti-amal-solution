from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.user import User
from app.models.departemen import Departemen
from app.schemas.penambahan_kerja import PenambahanKerjaQueueOut, PenambahanKerjaApprovalResponse


## pengajuan kerja di cuti bersama
async def create_penambahan_kerja(user_id: int, tanggal_mulai: date, tanggal_selesai: date, keterangan: str, db:AsyncSession) -> LogPenambahanKerja:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan!")

    if user.id_departemen != 3:
        raise HTTPException(status_code=400, detail="Hanya karyawan departemen 3 yang dapat mengajukan!")

    if tanggal_mulai > tanggal_selesai:
        raise HTTPException(status_code=400, detail="Tanggal mulai tidak boleh lebih dari tanggal selesai!")

    overlapping = await db.execute(select(LogPenambahanKerja).where(
        LogPenambahanKerja.id_user == user_id,
        LogPenambahanKerja.tanggal_mulai <= tanggal_selesai,
        LogPenambahanKerja.tanggal_selesai >= tanggal_mulai,
        LogPenambahanKerja.status != "ditolak_pm"
    ))

    if overlapping.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Pengajuan tanggal tersebut sudah ada!")

    log = LogPenambahanKerja(
        id_user=user_id,
        tanggal_mulai=tanggal_mulai,
        tanggal_selesai=tanggal_selesai,
        keterangan_pengajuan=keterangan,
        status="menunggu_pm"
    )

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return log


## get riwayat penambahan kerja
async def get_my_penambahan_kerja(user_id: int, db: AsyncSession) -> list[LogPenambahanKerja]:
    result = await db.execute(select(LogPenambahanKerja).where(
        LogPenambahanKerja.id_user == user_id).order_by(LogPenambahanKerja.tanggal_mulai.desc())
    )

    return result.scalars().all()


## queue penambahan kerja
async def get_penambahan_kerja_queue(pm_id: int, db: AsyncSession) -> list[PenambahanKerjaQueueOut]:
    result_team = await db.execute(select(User.id_user).where(User.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return []

    result = await db.execute(select(LogPenambahanKerja).options(
        selectinload(LogPenambahanKerja.user_log).selectinload(User.user_departemen)).where(
            LogPenambahanKerja.id_user.in_(team_ids), LogPenambahanKerja.status == "menunggu_pm"
        ).order_by(LogPenambahanKerja.tanggal_mulai.asc())
    )
    logs = result.scalars().all()

    return [
        PenambahanKerjaQueueOut(
            id_pengajuan_kerja=log.id_pengajuan_kerja,
            nama=log.user_log.nama,
            nama_departemen=log.user_log.user_departemen.nama_departemen,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            keterangan=log.keterangan_pengajuan,
        ) for log in logs
    ]


## approvement penambahan kerja
async def process_penambahan_kerja(
 log_id: int, pm_id: int, action: str, alasan: str | None, db: AsyncSession       
) -> PenambahanKerjaApprovalResponse:
    result = await db.execute(select(LogPenambahanKerja).where(LogPenambahanKerja.id_pengajuan_kerja == log_id))
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan!")

    if log.status != "menunggu_pm":
        raise HTTPException(status_code=400, detail="Pengajuan sudah diproses")

    result_user = await db.execute(select(User).where(User.id_user == log.id_user))
    user = result_user.scalar_one_or_none()

    if not user or user.id_pm != pm_id:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses untuk pengajuan ini!")

    if action == "acc":
        log.status="disetujui_pm"
        log.diproses_pm=pm_id
        log.processed_at_pm=date.today()
    elif action == "decline":
        if not alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")
        log.status="ditolak_pm"
        log.diproses_pm=pm_id
        log.processed_at_pm=date.today()

    db.add(log)
    await db.commit()
    await db.refresh(log)

    return PenambahanKerjaApprovalResponse(
        detail="Pengajuan berhasil disetujui!" if action == "acc" else "Pengajuan berhasil ditolak!",
        status_baru=log.status
    )

