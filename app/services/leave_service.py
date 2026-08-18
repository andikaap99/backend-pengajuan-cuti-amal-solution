from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.log_cuti import PengajuanCutiOut, RiwayatCutiOut, PengajuanOngoingOut, RingkasanCutiOut



## fungsi pengajuan cuti
async def create_pengajuan_cuti(data: PengajuanCutiOut, user_id: int, db: AsyncSession) -> LogCuti:
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

    if data.pengganti is not None:
        if data.pengganti == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pengganti tidak boleh diri sendiri")

        pengganti = await db.execute(select(User).where(User.id_user == data.pengganti))
        if not pengganti.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User pengganti tidak ditemukan")

    if user.role == "direktur":
        raise HTTPException(status_code=400, detail="Direktur tidak bisa mengajukan cuti")

    status_pengajuan = get_ongoing_statuses(user)[0]

    log = LogCuti(
        id_user=user_id,
        jenis_cuti="cuti tahunan",
        tanggal_mulai=data.tanggal_mulai,
        tanggal_selesai=data.tanggal_selesai,
        keterangan_cuti=data.keterangan_cuti,
        pengganti=data.pengganti,
        status=status_pengajuan,
    )
    db.add(log)

    await kurangi_jatah_cuti(user_id, durasi, db)

    await db.commit()
    await db.refresh(log)
    return log


## fugnsi get all cuti pribadi
async def get_my_cuti(user_id: int, db: AsyncSession) -> list[RiwayatCutiOut]:
    result = await db.execute(select(LogCuti).where(LogCuti.id_user == user_id))
    logs = result.scalars().all()

    list_pengganti_ids = [log.pengganti for log in logs if log.pengganti is not None]
    result_pengganti = await db.execute(select(User).where(User.id_user.in_(list_pengganti_ids))) if list_pengganti_ids else None
    map_pengganti = {u.id_user: u.nama for u in result_pengganti.scalars().all()} if result_pengganti else {}

    return [
        RiwayatCutiOut(
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            nama_pengganti=map_pengganti.get(log.pengganti, "Tidak ada") if log.pengganti else "Tidak ada",
            keterangan_cuti=log.keterangan_cuti,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            status=log.status,
        )
        for log in logs
    ]


## fungsi get all cuti pribadi (ongoing only)
async def get_my_ongoing_cuti(user_id: int, db: AsyncSession) -> list[PengajuanOngoingOut]:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    ongoing_statuses = get_ongoing_statuses(user)
    result = await db.execute(
        select(LogCuti).where(
            LogCuti.id_user == user_id,
            LogCuti.status.in_(ongoing_statuses)
        )
    )
    logs = result.scalars().all()

    return [
        PengajuanOngoingOut(
            jenis_cuti=log.jenis_cuti,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            keterangan_cuti=log.keterangan_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            status_sekarang=log.status,
            disetujui_pm=log.disetujui_pm,
            disetujui_hr=log.disetujui_hr,
            disetujui_direktur=log.disetujui_direktur,
            approved_at_pm=log.approved_at_pm,
            approved_at_hr=log.approved_at_hr,
            approved_at_direktur=log.approved_at_direktur,
            alasan_penolakan=log.alasan_penolakan,
        )
        for log in logs
    ]


## fungsi untuk get status sesuai role
def get_ongoing_statuses(user: User) -> list[str]:
    match user.role:
        case "karyawan":
            if user.id_departemen != 1:
                return ["menunggu_pm", "disetujui_pm", "menunggu_hr"]
            else:
                return ["menunggu_hr"]
        case "pm":
            return ["menunggu_hr"]
        case "hr":
            return ["menunggu_direktur"]
    return []


## fungsi untuk menampilkan ringkasan cuti dashboard
async def get_my_ringkasan_cuti(user_id: int, db: AsyncSession) -> RingkasanCutiOut:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    return RingkasanCutiOut(
        periode_tahun=date.today().year,
        total_cuti=user.total_cuti,
        cuti_terpakai=user.total_cuti - user.sisa_cuti,
        sisa_cuti=user.sisa_cuti
    )


## fungsi mengurangi jatah cuti
async def kurangi_jatah_cuti(user_id: int, durasi: int, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak cukup")

    user.sisa_cuti -= durasi
    db.add(user)
    await db.flush()


async def kurangi_jatah_by_kalender():
    pass


# async def get_all_leaves(db: AsyncSession) -> list[LogCuti]:
#     result = await db.execute(select(LogCuti))
#     return result.scalars().all()


# def get_all_approval_steps(user: User) -> list[str]:
#     match user.role:
#         case "karyawan":
#             if user.id_departemen != 1:
#                 return ["disetujui_pm", "disetujui_hr", "disetujui_direktur"]
#             else:
#                 return ["disetujui_hr", "disetujui_direktur"]
#         case "pm":
#             return ["disetujui_pm", "disetujui_hr", "disetujui_direktur"]
#         case "hr":
#             return ["disetujui_hr", "disetujui_direktur"]
#     return []


# def get_passed_approvals(log: LogCuti, all_steps: list[str]) -> list[str]:
#     passed = []
#     status_order = {
#         "disetujui_pm": 0,
#         "disetujui_hr": 1,
#         "disetujui_direktur": 2,
#     }
#     current_map = {
#         "menunggu_pm": -1, "disetujui_pm": 0, "ditolak_pm": -1,
#         "menunggu_hr": 0, "disetujui_hr": 1, "ditolak_hr": 1,
#         "menunggu_direktur": 1, "disetujui_direktur": 2, "ditolak_direktur": 2,
#     }
#     current_level = current_map.get(log.status, -1)
#     for step in all_steps:
#         step_level = status_order.get(step, -1)
#         if step_level <= current_level and log.status != f"ditolak_{step.split('_')[1]}":
#             passed.append(step)
#         elif "ditolak" in log.status:
#             break
#     return passed


# async def get_ongoing_leave(user_id: int, db: AsyncSession) -> PengajuanOngoingOut | None:
#     result_user = await db.execute(select(User).where(User.id_user == user_id))
#     user = result_user.scalar_one()

#     ongoing_statuses = get_ongoing_statuses(user)
#     result = await db.execute(
#         select(LogCuti).where(
#             LogCuti.id_user == user_id,
#             LogCuti.status.in_(ongoing_statuses)
#         ).order_by(LogCuti.id_log_cuti.desc())
#     )
#     log = result.scalars().first()

#     if not log:
#         return None

#     all_steps = get_all_approval_steps(user)
#     all_status = get_passed_approvals(log, all_steps)

#     return PengajuanOngoingOut(
#         jenis_cuti=log.jenis_cuti,
#         durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
#         keterangan=log.keterangan_cuti,
#         tanggal_mulai=log.tanggal_mulai,
#         tanggal_selesai=log.tanggal_selesai,
#         status_sekarang=log.status,
#         all_status=all_status,
#         alasan_penolakan=log.alasan_penolakan,
#     )
