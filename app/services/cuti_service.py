from datetime import date, datetime, timedelta
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.log_cuti_approval_pm import LogCutiApprovalPM
from app.models.holiday import Holiday
from app.models.user import User
from app.models.user_pm import UserPM
from app.schemas.log_cuti import PengajuanCutiOut, PengajuanCutiUpdate, RiwayatCutiOut, EmpDashboardPengajuanOngoingOut, EmpDashboardRingkasanOut, ApprovalPMDetail
from app.services.ongoing_status_role_service import get_ongoing_statuses, get_finished_statuses
from app.services.holiday_service import get_next_pending_holiday_days
from app.services.email_service import send_pengajuan_notification


## hitung cuti terpakai dari log_cuti yang sudah final
FINAL_STATUSES = ["disetujui_hr", "disetujui_direktur", "cuti_bersama"]

async def hitung_cuti_terpakai(user_id: int, db: AsyncSession) -> int:
    result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    func.datediff(LogCuti.tanggal_selesai, LogCuti.tanggal_mulai) + 1
                ),
                0
            )
        ).where(
            LogCuti.id_user == user_id,
            LogCuti.status.in_(FINAL_STATUSES)
        )
    )
    return result.scalar_one()


pengajuan_statuses = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]

## fungsi pengajuan cuti
async def create_pengajuan_cuti(data: PengajuanCutiOut, user_id: int, db: AsyncSession, background_tasks: BackgroundTasks) -> LogCuti:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    if user.role == "direktur":
        raise HTTPException(status_code=400, detail="Direktur tidak bisa mengajukan cuti")

    if data.tanggal_mulai < date.today():
        raise HTTPException(status_code=400, detail="Tanggal cuti tidak boleh di masa lalu")

    aktif_statuses = ["menunggu_pm", "menunggu_hr", "menunggu_direktur"]
    existing = await db.execute(select(LogCuti).where(
        LogCuti.id_user == user_id,
        LogCuti.status.in_(aktif_statuses)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Masih ada pengajuan cuti yang sedang diproses")

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

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak mencukupi")

    sisa_setelah_potong = user.sisa_cuti - next_holiday_days

    if sisa_setelah_potong < durasi:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sisa cuti tidak mencukupi setelah potongan cuti bersama mendatang")

    result_holiday = await db.execute(
        select(Holiday).where(
            Holiday.is_cuti_bersama == True,
            Holiday.sudah_dikurangi == False,
        )
    )
    holidays = result_holiday.scalars().all()

    if holidays:
        jumlah_cuti_bersama = len(holidays)
        if user.sisa_cuti < jumlah_cuti_bersama:
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
    await db.flush()

    ## buat baris approval PM untuk setiap PM yang terdaftar
    if status_pengajuan == "menunggu_pm":
        result_pm = await db.execute(select(UserPM).where(UserPM.id_karyawan == user_id))
        user_pm_list = result_pm.scalars().all()

        for upm in user_pm_list:
            approval_pm = LogCutiApprovalPM(
                id_log_cuti=log.id_log_cuti,
                id_pm=upm.id_pm,
                status="menunggu",
            )
            db.add(approval_pm)

    await db.commit()
    await db.refresh(log)

    ## kirim email notifikasi ke approver
    if status_pengajuan == "menunggu_pm":
        result_pm_notify = await db.execute(select(UserPM).where(UserPM.id_karyawan == user_id))
        pm_list = result_pm_notify.scalars().all()
        for upm in pm_list:
            pm_user = await db.execute(select(User).where(User.id_user == upm.id_pm))
            pm = pm_user.scalar_one_or_none()
            if pm:
                background_tasks.add_task(
                    send_pengajuan_notification, user, pm, "cuti tahunan",
                    data.tanggal_mulai, data.tanggal_selesai, data.keterangan_cuti
                )
    elif status_pengajuan == "menunggu_hr":
        result_hr = await db.execute(select(User).where(User.role == "hr"))
        hr_users = result_hr.scalars().all()
        for hr_user in hr_users:
            background_tasks.add_task(
                send_pengajuan_notification, user, hr_user, "cuti tahunan",
                data.tanggal_mulai, data.tanggal_selesai, data.keterangan_cuti
            )
    elif status_pengajuan == "menunggu_direktur":
        result_dir = await db.execute(select(User).where(User.role == "direktur"))
        direktur_users = result_dir.scalars().all()
        for direktur in direktur_users:
            background_tasks.add_task(
                send_pengajuan_notification, user, direktur, "cuti tahunan",
                data.tanggal_mulai, data.tanggal_selesai, data.keterangan_cuti
            )

    return log


## fugnsi get all cuti pribadi
async def get_my_cuti(user_id: int, db: AsyncSession, user: User = None) -> list[RiwayatCutiOut]:
    finished_statuses = get_finished_statuses(user) if user else []

    result = await db.execute(
        select(LogCuti).options(
            selectinload(LogCuti.approval_pm_list).selectinload(LogCutiApprovalPM.pm)
        ).where(
            LogCuti.id_user == user_id,
            LogCuti.status.in_(finished_statuses),
        )
    )
    logs = result.scalars().unique().all()

    list_pengganti_ids = [log.pengganti for log in logs if log.pengganti is not None]
    result_pengganti = await db.execute(select(User).where(User.id_user.in_(list_pengganti_ids))) if list_pengganti_ids else None
    map_pengganti = {u.id_user: u.nama for u in result_pengganti.scalars().all()} if result_pengganti else {}

    list_approver_ids = set()
    for log in logs:
        if log.diproses_hr:
            list_approver_ids.add(log.diproses_hr)
        if log.diproses_direktur:
            list_approver_ids.add(log.diproses_direktur)

    map_approver = {}
    if list_approver_ids:
        result_approver = await db.execute(select(User).where(User.id_user.in_(list_approver_ids)))
        map_approver = {u.id_user: u.nama for u in result_approver.scalars().all()}

    return [
        RiwayatCutiOut(
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            nama_pengganti=map_pengganti.get(log.pengganti, "Tidak ada") if log.pengganti else "Tidak ada",
            keterangan_cuti=log.keterangan_cuti,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            tanggal_pengajuan=log.tanggal_pengajuan,
            status=log.status,
            approval_pm_detail=[
                ApprovalPMDetail(
                    nama_pm=apm.pm.nama,
                    status=apm.status,
                    processed_at=apm.processed_at,
                ) for apm in log.approval_pm_list
            ],
            approved_by_hr=map_approver.get(log.diproses_hr),
            approved_at_hr=log.processed_at_hr,
            approved_by_direktur=map_approver.get(log.diproses_direktur),
            approved_at_direktur=log.processed_at_direktur,
        )
        for log in logs
    ]


## fungsi get all cuti pribadi (ongoing only)
REJECTED_STATUSES = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]
APPROVED_STATUSES = ["disetujui_pm", "disetujui_hr", "disetujui_direktur"]
REJECT_EXPIRE_DAYS = 3


def _get_reject_date(log: LogCuti) -> date | None:
    if log.status == "ditolak_pm":
        return None
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


async def _get_approval_pm_detail(log_cuti_id: int, db: AsyncSession) -> list[ApprovalPMDetail]:
    result = await db.execute(
        select(LogCutiApprovalPM, User.nama).join(User, LogCutiApprovalPM.id_pm == User.id_user).where(
            LogCutiApprovalPM.id_log_cuti == log_cuti_id
        )
    )
    rows = result.all()

    return [
        ApprovalPMDetail(
            nama_pm=row[1],
            status=row[0].status,
            processed_at=row[0].processed_at,
        )
        for row in rows
    ]


async def get_my_ongoing_cuti(user_id: int, db: AsyncSession) -> list[EmpDashboardPengajuanOngoingOut]:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    result = await db.execute(
        select(LogCuti).where(
            LogCuti.id_user == user_id,
        ).order_by(LogCuti.tanggal_pengajuan.desc())
    )
    logs = result.scalars().all()

    if not logs:
        
        return []

    latest = logs[0]

    approval_pm_detail = await _get_approval_pm_detail(latest.id_log_cuti, db)

    nama_hr = None
    nama_direktur = None
    if latest.diproses_hr:
        result_hr = await db.execute(select(User.nama).where(User.id_user == latest.diproses_hr))
        nama_hr = result_hr.scalar_one_or_none()
    if latest.diproses_direktur:
        result_dir = await db.execute(select(User.nama).where(User.id_user == latest.diproses_direktur))
        nama_direktur = result_dir.scalar_one_or_none()

    return [EmpDashboardPengajuanOngoingOut(
        jenis_cuti=latest.jenis_cuti,
        durasi=(latest.tanggal_selesai - latest.tanggal_mulai).days + 1,
        keterangan_cuti=latest.keterangan_cuti,
        tanggal_mulai=latest.tanggal_mulai,
        tanggal_selesai=latest.tanggal_selesai,
        tanggal_pengajuan=latest.tanggal_pengajuan,
        status_sekarang=latest.status,
        approved_by_hr=nama_hr,
        approved_at_hr=latest.processed_at_hr,
        approved_by_direktur=nama_direktur,
        approved_at_direktur=latest.processed_at_direktur,
        alasan_penolakan=latest.alasan_penolakan,
        id_pengganti=latest.pengganti,
        approval_pm_detail=approval_pm_detail,
    )]


## fungsi untuk menampilkan ringkasan cuti dashboard
async def get_my_ringkasan_cuti(user_id: int, db: AsyncSession) -> EmpDashboardRingkasanOut:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    cuti_terpakai = await hitung_cuti_terpakai(user_id, db)

    return EmpDashboardRingkasanOut(
        periode_tahun=date.today().year,
        total_cuti=user.total_cuti,
        cuti_terpakai=cuti_terpakai,
        sisa_cuti=user.sisa_cuti
    )


## editable status pengajuan cuti
EDITABLE_STATUSES = [
    "ditolak_pm", "ditolak_hr", "ditolak_direktur",
    "menunggu_pm", "menunggu_hr", "menunggu_direktur"
]

## status ditolak (resubmit)
RESUBMIT_STATUSES = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]

## edit pengajuan cuti
async def edit_pengajuan_cuti(
    log_cuti_id: int, user_id: int, data: PengajuanCutiUpdate, db: AsyncSession, background_tasks: BackgroundTasks
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

    if user.sisa_cuti < durasi:
        raise HTTPException(status_code=400, detail="Sisa cuti tidak mencukupi!")

    sisa_setelah_potong = user.sisa_cuti - next_holiday_days

    if sisa_setelah_potong < durasi:
        raise HTTPException(status_code=400, detail="Sisa cuti tidak mencukupi setelah potongan cuti bersama mendatang!")

    result_holiday = await db.execute(
        select(Holiday).where(Holiday.is_cuti_bersama == True, Holiday.sudah_dikurangi == False)
    )
    holidays = result_holiday.scalars().all()

    if holidays:
        jumlah_cuti_bersama = len(holidays)
        if user.sisa_cuti < jumlah_cuti_bersama:
            raise HTTPException(status_code=400, detail="Sisa cuti sudah habis dan hanya menyisakan cuti bersama")

    if new_pengganti is not None:
        if new_pengganti == user_id:
            raise HTTPException(status_code=400, detail="Pengganti tidak boleh diri sendiri")
        pengganti_user = await db.execute(select(User).where(User.id_user == new_pengganti))
        if not pengganti_user.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="User pengganti tidak ditemukan")

    log.tanggal_mulai = new_tanggal_mulai
    log.tanggal_selesai = new_tanggal_selesai
    log.pengganti = new_pengganti
    log.keterangan_cuti = new_keterangan
    log.edited_at = datetime.now()

    if log.status in RESUBMIT_STATUSES:
        new_status = get_ongoing_statuses(user)[0]
        log.status = new_status
        log.tanggal_pengajuan = datetime.now()
        log.alasan_penolakan = None
        log.diproses_hr = None
        log.diproses_direktur = None
        log.processed_at_hr = None
        log.processed_at_direktur = None

        ## hapus approval PM lama dan buat baru
        old_approvals = await db.execute(
            select(LogCutiApprovalPM).where(LogCutiApprovalPM.id_log_cuti == log_cuti_id)
        )
        for old in old_approvals.scalars().all():
            await db.delete(old)

        ## buat baris approval PM baru
        if new_status == "menunggu_pm":
            result_pm = await db.execute(select(UserPM).where(UserPM.id_karyawan == user_id))
            user_pm_list = result_pm.scalars().all()

            for upm in user_pm_list:
                approval_pm = LogCutiApprovalPM(
                    id_log_cuti=log_cuti_id,
                    id_pm=upm.id_pm,
                    status="menunggu",
                )
                db.add(approval_pm)

    db.add(log)
    await db.commit()
    await db.refresh(log)

    ## kirim email notifikasi ke approver jika resubmit
    if log.status in ["menunggu_pm", "menunggu_hr", "menunggu_direktur"]:
        if log.status == "menunggu_pm":
            result_pm_notify = await db.execute(select(UserPM).where(UserPM.id_karyawan == user_id))
            pm_list = result_pm_notify.scalars().all()
            for upm in pm_list:
                pm_user = await db.execute(select(User).where(User.id_user == upm.id_pm))
                pm = pm_user.scalar_one_or_none()
                if pm:
                    background_tasks.add_task(
                        send_pengajuan_notification, user, pm, "cuti tahunan",
                        log.tanggal_mulai, log.tanggal_selesai, log.keterangan_cuti
                    )
        elif log.status == "menunggu_hr":
            result_hr = await db.execute(select(User).where(User.role == "hr"))
            hr_users = result_hr.scalars().all()
            for hr_user in hr_users:
                background_tasks.add_task(
                    send_pengajuan_notification, user, hr_user, "cuti tahunan",
                    log.tanggal_mulai, log.tanggal_selesai, log.keterangan_cuti
                )
        elif log.status == "menunggu_direktur":
            result_dir = await db.execute(select(User).where(User.role == "direktur"))
            direktur_users = result_dir.scalars().all()
            for direktur in direktur_users:
                background_tasks.add_task(
                    send_pengajuan_notification, user, direktur, "cuti tahunan",
                    log.tanggal_mulai, log.tanggal_selesai, log.keterangan_cuti
                )

    return log
