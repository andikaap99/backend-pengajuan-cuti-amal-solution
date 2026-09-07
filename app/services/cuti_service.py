from datetime import date, timedelta
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.holiday import Holiday
from app.models.user import User
from app.schemas.log_cuti import PengajuanCutiOut, PengajuanCutiUpdate, RiwayatCutiOut, EmpDashboardPengajuanOngoingOut, EmpDashboardRingkasanOut
from app.services.ongoing_status_role_service import get_ongoing_statuses
from app.services.holiday_service import get_next_pending_holiday_days
from app.services.tambah_cuti_service import get_effective_sisa_cuti



pengajuan_statuses = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]

## fungsi pengajuan cuti
async def create_pengajuan_cuti(data: PengajuanCutiOut, user_id: int, db: AsyncSession) -> LogCuti:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if user.role == "direktur":
        raise HTTPException(status_code=400, detail="Direktur tidak bisa mengajukan cuti")

    if data.tanggal_mulai < date.today():
        raise HTTPException(status_code=400, detail="Tanggal cuti tidak boleh di masa lalu")

    if (data.tanggal_mulai - date.today()).days < 10:
        raise HTTPException(status_code=400, detail="Maksimal pengajuan 10 hari sebelum hari pertama cuti")

    overlapping = await db.execute(select(LogCuti).where(
        LogCuti.id_user == user_id, 
        LogCuti.tanggal_mulai <= data.tanggal_selesai, 
        LogCuti.tanggal_selesai >= data.tanggal_mulai,
        LogCuti.status.notin_(pengajuan_statuses))
    )

    if overlapping.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tanggal cuti sudah pernah diambil atau tertumpang tindih!")

    durasi = (data.tanggal_selesai - data.tanggal_mulai).days + 1

    if durasi <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tanggal tidak valid")

    if durasi > 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maksimal cuti selama 4 hari")

    next_holiday_days = await get_next_pending_holiday_days(db)
    effective_sisa = await get_effective_sisa_cuti(user, date.today().year, db)
    if effective_sisa < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak mencukupi (termasuk potongan cuti bersama mendatang)")

    effective_sisa -= next_holiday_days

    result_holiday = await db.execute(
        select(Holiday).where(
            Holiday.is_cuti_bersama == True,
            Holiday.sudah_dikurangi == False,
        )
    )
    holidays = result_holiday.scalars().all()

    if holidays:
        jumlah_cuti_bersama = len(holidays)
        effective_sisa_no_holiday = await get_effective_sisa_cuti(user, date.today().year, db)
        if effective_sisa_no_holiday < jumlah_cuti_bersama:
            raise HTTPException(status_code=400, detail="Sisa cuti sudah habis dan hanya menyisakan cuti bersama")

    if data.pengganti is not None:
        if data.pengganti == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pengganti tidak boleh diri sendiri")

        pengganti = await db.execute(select(User).where(User.id_user == data.pengganti))
        if not pengganti.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User pengganti tidak ditemukan")

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
REJECTED_STATUSES = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]
APPROVED_STATUSES = ["disetujui_pm", "disetujui_hr", "disetujui_direktur"]
REJECT_EXPIRE_DAYS = 3


def _get_reject_date(log: LogCuti) -> date | None:
    if log.status == "ditolak_pm":
        return log.processed_at_pm
    if log.status == "ditolak_hr":
        return log.processed_at_hr
    if log.status == "ditolak_direktur":
        return log.processed_at_direktur
    return None


def _is_rejected_expired(log: LogCuti) -> bool:
    if log.status not in REJECTED_STATUSES:
        return False
    reject_date = _get_reject_date(log)
    if not reject_date:
        return False
    return (date.today() - reject_date).days > REJECT_EXPIRE_DAYS


async def get_my_ongoing_cuti(user_id: int, db: AsyncSession) -> list[EmpDashboardPengajuanOngoingOut]:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    ongoing_statuses = get_ongoing_statuses(user)
    visible_statuses = ongoing_statuses + REJECTED_STATUSES + APPROVED_STATUSES

    result = await db.execute(
        select(LogCuti).where(
            LogCuti.id_user == user_id,
            LogCuti.status.in_(visible_statuses),
        )
    )
    logs = result.scalars().all()

    return [
        EmpDashboardPengajuanOngoingOut(
            jenis_cuti=log.jenis_cuti,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            keterangan_cuti=log.keterangan_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            status_sekarang=log.status,
            diproses_pm=log.diproses_pm,
            diproses_hr=log.diproses_hr,
            diproses_direktur=log.diproses_direktur,
            processed_at_pm=log.processed_at_pm,
            processed_at_hr=log.processed_at_hr,
            processed_at_direktur=log.processed_at_direktur,
            alasan_penolakan=log.alasan_penolakan,
        )
        for log in logs
        if not _is_rejected_expired(log)
    ]


## fungsi untuk menampilkan ringkasan cuti dashboard
async def get_my_ringkasan_cuti(user_id: int, db: AsyncSession) -> EmpDashboardRingkasanOut:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()
    effective_sisa = await get_effective_sisa_cuti(user, date.today().year, db)

    return EmpDashboardRingkasanOut(
        periode_tahun=date.today().year,
        total_cuti=user.total_cuti,
        cuti_terpakai=user.total_cuti - effective_sisa,
        sisa_cuti=effective_sisa
    )


# ## get initial status

# ### get_initial_status
# def get_initial_status(user: User) -> str:
#     match user.role:
#         case "karyawan":
#             if user.id_pm is not None:
#                 return "menunggu_pm"
#             else:
#                 return "menunggu_hr"
#         case "pm":
#             return "menunggu_hr"
#         case "hr":
#             return "menunggu_direktur"
#     return "menunggu_hr"


## editable status pengajuan cuti
EDITABLE_STATUSES = [
    "ditolak_pm", "ditolak_hr", "ditolak_direktur",
    "menunggu_pm", "menunggu_hr", "menunggu_direktur"
]

## status ditolak (resubmit)
RESUBMIT_STATUSES = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]

# ### edit_pengajuan_cuti
# EDITABLE_STATUSES = [
#     "ditolak_pm", "ditolak_hr", "ditolak_direktur",
#     "menunggu_pm", "menunggu_hr", "menunggu_direktur",
# ]

## edit pengajuan cuti
async def edit_pengajuan_cuti(
    log_cuti_id: int, user_id: int, data: PengajuanCutiUpdate, db: AsyncSession
) -> LogCuti:
    result = await db.execute(select(LogCuti).where(
        LogCuti.id_log_cuti == log_cuti_id, LogCuti.id_user == user_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Log cuti tidak ditemukan!")

    if log.status not in EDITABLE_STATUSES:
        raise HTTPException(status_code=404, detail="Pengajuan dengan status ini tidak bisa diedit")

    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    new_tanggal_mulai = data.tanggal_mulai if data.tanggal_mulai is not None else log.tanggal_mulai
    new_tanggal_selesai = data.tanggal_selesai if data.tanggal_selesai is not None else log.tanggal_selesai
    new_pengganti = data.pengganti
    new_keterangan = data.keterangan_cuti if data.keterangan_cuti is not None else log.keterangan_cuti

    if new_tanggal_mulai < date.today():
        raise HTTPException(status_code=400, detail="Tanggal tidak boleh di masa lalu!")
    
    if (new_tanggal_mulai - date.today()).days < 10:
        raise HTTPException(status_code=400, detail="Maksimal pengajuan 10 hari sebelum tanggal pertama cuti!")

    durasi = (new_tanggal_selesai - new_tanggal_mulai).days + 1
    if durasi <= 0:
        raise HTTPException(status_code=400, detail="Tanggal tidak valid!")

    if durasi > 4:
        raise HTTPException(status_code=400, detail="Tanggal cuti selama 4 hari")

    overlapping = await db.execute(select(LogCuti).where(
        LogCuti.id_user == user_id, LogCuti.id_log_cuti != log_cuti_id, LogCuti.tanggal_mulai <= new_tanggal_selesai,
        LogCuti.tanggal_selesai >= new_tanggal_mulai, LogCuti.status.notin_(pengajuan_statuses))
    )
    if overlapping.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tanggal cuti sudah pernah diambil atau tertumpang tindih!")

    next_holiday_days = await get_next_pending_holiday_days(db)
    effective_sisa = await get_effective_sisa_cuti(user, date.today().year, db)

    if effective_sisa < durasi:
        raise HTTPException(status_code=400, detail="Sisa cuti tidak mencukupi!")
    
    effective_sisa -= next_holiday_days

    result_holiday = await db.execute(
        select(Holiday).where(Holiday.is_cuti_bersama == True, Holiday.sudah_dikurangi == False)
    )
    holidays = result_holiday.scalars().all()

    if holidays:
        jumlah_cuti_bersama = len(holidays)
        effective_sisa_no_holiday = await get_effective_sisa_cuti(user, date.today().year, db)
        if effective_sisa_no_holiday < jumlah_cuti_bersama:
            raise HTTPException(status_code=400, detail="Sisa cuti sudah habis dan hanya menyisakan cuti bersama")

    if new_pengganti is not None:
        if new_pengganti == user_id:
            raise HTTPException(status_code=400, detail="Pengganti tidak boleh diri sendiri")
        pengganti_user = await db.execute(select(User).where(User.id_user == new_pengganti))
        if not pengganti_user.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="User pengganti tidak ditemukan")

    log.tanggal_mulai = new_tanggal_mulai
    log.tanggal_selesai = new_tanggal_selesai
    log.pengganti = new_pengganti
    log.keterangan_cuti = new_keterangan
    log.edited_at = date.today()

    if log.status in RESUBMIT_STATUSES:
        new_status = get_ongoing_statuses(user)[0]
        log.status = new_status
        log.tanggal_pengajuan = date.today()
        log.alasan_penolakan = None
        log.diproses_pm = None
        log.diproses_hr = None
        log.diproses_direktur = None
        log.processed_at_pm = None
        log.processed_at_hr = None
        log.processed_at_direktur = None

    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log



# async def edit_pengajuan_cuti(
#     log_cuti_id: int, user_id: int, data: PengajuanCutiUpdate, db: AsyncSession
# ) -> LogCuti:
#     result = await db.execute(
#         select(LogCuti).where(LogCuti.id_log_cuti == log_cuti_id, LogCuti.id_user == user_id)
#     )
#     log = result.scalar_one_or_none()
#     if not log:
#         raise HTTPException(status_code=404, detail="Log cuti tidak ditemukan")
#     if log.status not in EDITABLE_STATUSES:
#         raise HTTPException(status_code=400, detail="Pengajuan tidak bisa diedit dalam status ini")
#     result_user = await db.execute(select(User).where(User.id_user == user_id))
#     user = result_user.scalar_one_or_none()
#     if not user:
#         raise HTTPException(status_code=404, detail="User tidak ditemukan")
#     new_tanggal_mulai = data.tanggal_mulai if data.tanggal_mulai is not None else log.tanggal_mulai
#     new_tanggal_selesai = data.tanggal_selesai if data.tanggal_selesai is not None else log.tanggal_selesai
#     new_pengganti = data.pengganti  # boleh None (kosongkan)
#     new_keterangan = data.keterangan_cuti if data.keterangan_cuti is not None else log.keterangan_cuti
#     if new_tanggal_mulai < date.today():
#         raise HTTPException(status_code=400, detail="Tanggal cuti tidak boleh di masa lalu")
#     if (new_tanggal_mulai - date.today()).days < 10:
#         raise HTTPException(status_code=400, detail="Maksimal pengajuan 10 hari sebelum hari pertama cuti")
#     durasi = (new_tanggal_selesai - new_tanggal_mulai).days + 1
#     if durasi <= 0:
#         raise HTTPException(status_code=400, detail="Tanggal tidak valid")
#     if durasi > 4:
#         raise HTTPException(status_code=400, detail="Maksimal cuti selama 4 hari")
#     overlapping = await db.execute(select(LogCuti).where(
#         LogCuti.id_user == user_id,
#         LogCuti.id_log_cuti != log_cuti_id,
#         LogCuti.tanggal_mulai <= new_tanggal_selesai,
#         LogCuti.tanggal_selesai >= new_tanggal_mulai,
#         LogCuti.status.notin_(pengajuan_statuses),
#     ))
#     if overlapping.scalar_one_or_none():
#         raise HTTPException(status_code=400, detail="Tanggal cuti sudah pernah diambil atau tertumpang tindih")
#     next_holiday_days = await get_next_pending_holiday_days(db)
#     effective_sisa = await get_effective_sisa_cuti(user, date.today().year, db)
#     if effective_sisa < durasi:
#         raise HTTPException(status_code=400, detail="Sisa cuti tidak mencukupi")
#     effective_sisa -= next_holiday_days
#     result_holiday = await db.execute(
#         select(Holiday).where(Holiday.is_cuti_bersama == True, Holiday.sudah_dikurangi == False)
#     )
#     holidays = result_holiday.scalars().all()
#     if holidays:
#         jumlah_cuti_bersama = len(holidays)
#         effective_sisa_no_holiday = await get_effective_sisa_cuti(user, date.today().year, db)
#         if effective_sisa_no_holiday < jumlah_cuti_bersama:
#             raise HTTPException(status_code=400, detail="Sisa cuti sudah habis dan hanya menyisakan cuti bersama")

#     if new_pengganti is not None:
#         if new_pengganti == user_id:
#             raise HTTPException(status_code=400, detail="Pengganti tidak boleh diri sendiri")
#         pengganti_user = await db.execute(select(User).where(User.id_user == new_pengganti))
#         if not pengganti_user.scalar_one_or_none():
#             raise HTTPException(status_code=404, detail="User pengganti tidak ditemukan")

#     new_status = get_initial_status(user)

#     log.tanggal_mulai = new_tanggal_mulai
#     log.tanggal_selesai = new_tanggal_selesai
#     log.pengganti = new_pengganti
#     log.keterangan_cuti = new_keterangan
#     log.status = new_status
#     log.tanggal_pengajuan = date.today()
#     log.alasan_penolakan = None
#     log.diproses_pm = None
#     log.diproses_hr = None
#     log.diproses_direktur = None
#     log.processed_at_pm = None
#     log.processed_at_hr = None
#     log.processed_at_direktur = None

#     db.add(log)
#     await db.commit()
#     await db.refresh(log)
#     return log
