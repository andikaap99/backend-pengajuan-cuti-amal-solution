from datetime import date, datetime
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.log_penambahan_kerja_date import LogPenambahanKerjaDate
from app.models.log_penambahan_kerja_approval_pm import LogPenambahanKerjaApprovalPM
from app.models.user import User
from app.models.user_pm import UserPM
from app.models.departemen import Departemen
from app.schemas.penambahan_kerja import PenambahanKerjaOut, PenambahanKerjaQueueOut, PenambahanKerjaApprovalResponse, PenambahanKerjaApprovalPMDetail
from app.services.email_service import send_pengajuan_notification, send_penambahan_kerja_status_email
from app.services.ongoing_status_role_service import get_ongoing_statuses, get_finished_statuses


## subquery tanggal mulai (min) per pengajuan kerja, pengganti kolom range lama
def _min_tanggal_kerja_subquery():
    return (
        select(
            LogPenambahanKerjaDate.id_pengajuan_kerja,
            func.min(LogPenambahanKerjaDate.tanggal).label("mulai"),
        )
        .group_by(LogPenambahanKerjaDate.id_pengajuan_kerja)
        .subquery()
    )


## pengajuan kerja (semua role kecuali direktur)
async def create_penambahan_kerja(user_id: int, tanggal: list[date], keterangan: str, db:AsyncSession, background_tasks: BackgroundTasks) -> PenambahanKerjaOut:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan!")

    if user.role == "direktur":
        raise HTTPException(status_code=400, detail="Direktur tidak dapat mengajukan penambahan kerja!")

    if not tanggal:
        raise HTTPException(status_code=400, detail="Tanggal kerja harus diisi")

    for t in tanggal:
        if t < date.today():
            raise HTTPException(status_code=400, detail="Tanggal kerja tidak boleh di masa lalu")

    if len(set(tanggal)) != len(tanggal):
        raise HTTPException(status_code=400, detail="Tanggal kerja tidak boleh ganda")

    aktif_statuses = ["menunggu_pm", "menunggu_hr", "menunggu_direktur"]
    existing = await db.execute(select(LogPenambahanKerja).where(
        LogPenambahanKerja.id_user == user_id,
        LogPenambahanKerja.status.in_(aktif_statuses)
    ))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Masih ada pengajuan penambahan kerja yang sedang diproses")

    ## cek overlapping per tanggal (seperti pengajuan cuti)
    for t in sorted(tanggal):
        overlapping = await db.execute(
            select(LogPenambahanKerjaDate.id)
            .join(LogPenambahanKerja, LogPenambahanKerja.id_pengajuan_kerja == LogPenambahanKerjaDate.id_pengajuan_kerja)
            .where(
                LogPenambahanKerja.id_user == user_id,
                LogPenambahanKerjaDate.tanggal == t,
                LogPenambahanKerja.status.notin_(["ditolak_pm", "ditolak_hr", "ditolak_direktur"]),
            )
        )
        if overlapping.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Tanggal {t} sudah ada!")

    status_pengajuan = get_ongoing_statuses(user)[0]
    tanggal_sorted = sorted(tanggal)

    log = LogPenambahanKerja(
        id_user=user_id,
        keterangan_pengajuan=keterangan,
        status=status_pengajuan,
    )
    db.add(log)
    await db.flush()

    ## insert tanggal individual
    for t in tanggal_sorted:
        db.add(LogPenambahanKerjaDate(id_pengajuan_kerja=log.id_pengajuan_kerja, tanggal=t))

    ## buat approval PM hanya jika status menunggu_pm
    if status_pengajuan == "menunggu_pm":
        result_pm = await db.execute(select(UserPM.id_pm).where(UserPM.id_karyawan == user_id))
        pm_ids = [row[0] for row in result_pm.all()]

        for pm_id in pm_ids:
            approval = LogPenambahanKerjaApprovalPM(
                id_pengajuan_kerja=log.id_pengajuan_kerja,
                id_pm=pm_id,
                status="menunggu"
            )
            db.add(approval)

    await db.commit()
    await db.refresh(log)

    ## kirim email notifikasi sesuai status awal
    if status_pengajuan == "menunggu_pm":
        result_pm = await db.execute(select(UserPM.id_pm).where(UserPM.id_karyawan == user_id))
        pm_ids = [row[0] for row in result_pm.all()]
        for pm_id in pm_ids:
            pm_user = await db.execute(select(User).where(User.id_user == pm_id))
            pm = pm_user.scalar_one_or_none()
            if pm:
                background_tasks.add_task(
                    send_pengajuan_notification, user, pm, "penambahan kerja",
                    tanggal_sorted, keterangan
                )
    elif status_pengajuan == "menunggu_hr":
        result_hr = await db.execute(select(User).where(User.role.in_(["hr_manager", "staff_hr"])))
        hr_users = result_hr.scalars().all()
        for hr_user in hr_users:
            if hr_user.email:
                background_tasks.add_task(
                    send_pengajuan_notification, user, hr_user, "penambahan kerja",
                    tanggal_sorted, keterangan
                )
    elif status_pengajuan == "menunggu_direktur":
        result_dir = await db.execute(select(User).where(User.role == "direktur"))
        direktur_users = result_dir.scalars().all()
        for direktur in direktur_users:
            if direktur.email:
                background_tasks.add_task(
                    send_pengajuan_notification, user, direktur, "penambahan kerja",
                    tanggal_sorted, keterangan
                )

    return PenambahanKerjaOut(
        id_pengajuan_kerja=log.id_pengajuan_kerja,
        id_user=log.id_user,
        tanggal=tanggal_sorted,
        keterangan_pengajuan=log.keterangan_pengajuan,
        status=log.status,
        tanggal_pengajuan=log.tanggal_pengajuan,
        approval_pm_detail=[],
        approved_by_hr=None,
        approved_at_hr=log.processed_at_hr,
        approved_by_direktur=None,
        approved_at_direktur=log.processed_at_direktur,
    )


## get riwayat penambahan kerja (yang terbaru saja)
async def get_my_penambahan_kerja(user_id: int, db: AsyncSession, user: User = None):
    result = await db.execute(
        select(LogPenambahanKerja)
        .options(
            selectinload(LogPenambahanKerja.tanggal_list),
            selectinload(LogPenambahanKerja.approval_pm_list).selectinload(LogPenambahanKerjaApprovalPM.pm),
        )
        .where(
            LogPenambahanKerja.id_user == user_id,
        )
        .order_by(LogPenambahanKerja.tanggal_pengajuan.desc())
    )
    logs = result.scalars().unique().all()

    if not logs:
        return []

    latest = logs[0]

    approval_pm_detail = [
        PenambahanKerjaApprovalPMDetail(
            nama_pm=apm.pm.nama,
            status=apm.status,
            processed_at=apm.processed_at,
        ) for apm in latest.approval_pm_list if apm.pm
    ]

    approver_ids = [i for i in (latest.diproses_hr, latest.diproses_direktur) if i]
    map_approver = {}
    if approver_ids:
        result_users = await db.execute(select(User).where(User.id_user.in_(approver_ids)))
        map_approver = {u.id_user: u.nama for u in result_users.scalars().all()}

    return [PenambahanKerjaOut(
        id_pengajuan_kerja=latest.id_pengajuan_kerja,
        id_user=latest.id_user,
        tanggal=sorted([ld.tanggal for ld in latest.tanggal_list]),
        keterangan_pengajuan=latest.keterangan_pengajuan,
        status=latest.status,
        tanggal_pengajuan=latest.tanggal_pengajuan,
        approval_pm_detail=approval_pm_detail,
        approved_by_hr=map_approver.get(latest.diproses_hr),
        approved_at_hr=latest.processed_at_hr,
        approved_by_direktur=map_approver.get(latest.diproses_direktur),
        approved_at_direktur=latest.processed_at_direktur,
    )]


def _queue_out(log: LogPenambahanKerja) -> PenambahanKerjaQueueOut:
    return PenambahanKerjaQueueOut(
        id_pengajuan_kerja=log.id_pengajuan_kerja,
        nama=log.user_log.nama,
        nama_departemen=log.user_log.user_departemen.nama_departemen,
        tanggal=sorted([ld.tanggal for ld in log.tanggal_list]),
        keterangan=log.keterangan_pengajuan,
        tanggal_pengajuan=log.tanggal_pengajuan,
        status=log.status,
        approval_pm_detail=[
            PenambahanKerjaApprovalPMDetail(
                nama_pm=apm.pm.nama,
                status=apm.status,
                processed_at=apm.processed_at,
            ) for apm in log.approval_pm_list if apm.pm
        ],
    )


## queue penambahan kerja untuk pm
async def get_penambahan_kerja_queue(pm_id: int, db: AsyncSession) -> list[PenambahanKerjaQueueOut]:
    result_team = await db.execute(select(UserPM.id_karyawan).where(UserPM.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return []

    min_tgl = _min_tanggal_kerja_subquery()

    ## ambil pengajuan yang menunggu pm ini approve
    result = await db.execute(
        select(LogPenambahanKerja)
        .join(LogPenambahanKerjaApprovalPM, LogPenambahanKerja.id_pengajuan_kerja == LogPenambahanKerjaApprovalPM.id_pengajuan_kerja)
        .join(min_tgl, min_tgl.c.id_pengajuan_kerja == LogPenambahanKerja.id_pengajuan_kerja)
        .options(
            selectinload(LogPenambahanKerja.user_log).selectinload(User.user_departemen),
            selectinload(LogPenambahanKerja.tanggal_list),
            selectinload(LogPenambahanKerja.approval_pm_list).selectinload(LogPenambahanKerjaApprovalPM.pm)
        )
        .where(
            LogPenambahanKerjaApprovalPM.id_pm == pm_id,
            LogPenambahanKerjaApprovalPM.status == "menunggu",
            LogPenambahanKerja.status == "menunggu_pm"
        )
        .order_by(min_tgl.c.mulai.asc())
    )
    logs = result.scalars().unique().all()

    return [_queue_out(log) for log in logs]


## queue penambahan kerja untuk hr (kecuali pengajuan sendiri, seperti cuti)
async def get_penambahan_kerja_queue_hr(db: AsyncSession, current_user_id: int) -> list[PenambahanKerjaQueueOut]:
    min_tgl = _min_tanggal_kerja_subquery()

    result = await db.execute(
        select(LogPenambahanKerja)
        .join(min_tgl, min_tgl.c.id_pengajuan_kerja == LogPenambahanKerja.id_pengajuan_kerja)
        .options(
            selectinload(LogPenambahanKerja.user_log).selectinload(User.user_departemen),
            selectinload(LogPenambahanKerja.tanggal_list),
            selectinload(LogPenambahanKerja.approval_pm_list).selectinload(LogPenambahanKerjaApprovalPM.pm)
        )
        .where(
            LogPenambahanKerja.status == "menunggu_hr",
            LogPenambahanKerja.id_user != current_user_id,
        )
        .order_by(min_tgl.c.mulai.asc())
    )
    logs = result.scalars().unique().all()

    return [_queue_out(log) for log in logs]


## queue penambahan kerja untuk direktur (kecuali pengajuan sendiri, seperti cuti)
async def get_penambahan_kerja_queue_direktur(db: AsyncSession, current_user_id: int) -> list[PenambahanKerjaQueueOut]:
    min_tgl = _min_tanggal_kerja_subquery()

    result = await db.execute(
        select(LogPenambahanKerja)
        .join(min_tgl, min_tgl.c.id_pengajuan_kerja == LogPenambahanKerja.id_pengajuan_kerja)
        .options(
            selectinload(LogPenambahanKerja.user_log).selectinload(User.user_departemen),
            selectinload(LogPenambahanKerja.tanggal_list),
            selectinload(LogPenambahanKerja.approval_pm_list).selectinload(LogPenambahanKerjaApprovalPM.pm)
        )
        .where(
            LogPenambahanKerja.status == "menunggu_direktur",
            LogPenambahanKerja.id_user != current_user_id,
        )
        .order_by(min_tgl.c.mulai.asc())
    )
    logs = result.scalars().unique().all()

    return [_queue_out(log) for log in logs]


## approvement penambahan kerja oleh pm
async def process_penambahan_kerja(
 log_id: int, pm_id: int, action: str, alasan: str | None, db: AsyncSession, background_tasks: BackgroundTasks       
) -> PenambahanKerjaApprovalResponse:
    result = await db.execute(
        select(LogPenambahanKerja)
        .options(selectinload(LogPenambahanKerja.tanggal_list))
        .where(LogPenambahanKerja.id_pengajuan_kerja == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan!")

    if log.id_user == pm_id:
        raise HTTPException(status_code=400, detail="Tidak bisa memproses pengajuan sendiri")

    if log.status != "menunggu_pm":
        raise HTTPException(status_code=400, detail="Pengajuan sudah diproses")

    ## cek apakah pm ini adalah pm untuk karyawan tersebut
    result_pm_check = await db.execute(
        select(UserPM).where(UserPM.id_pm == pm_id, UserPM.id_karyawan == log.id_user)
    )
    if not result_pm_check.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses untuk pengajuan ini!")

    ## update status approval pm ini
    result_approval = await db.execute(
        select(LogPenambahanKerjaApprovalPM).where(
            LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == log_id,
            LogPenambahanKerjaApprovalPM.id_pm == pm_id
        )
    )
    approval = result_approval.scalar_one_or_none()

    if not approval:
        raise HTTPException(status_code=404, detail="Approval record tidak ditemukan!")

    if approval.status != "menunggu":
        raise HTTPException(status_code=400, detail="Anda sudah memproses pengajuan ini!")

    if action == "acc":
        approval.status = "disetujui"
    elif action == "decline":
        if not alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")
        approval.status = "ditolak"

    from datetime import datetime as datetime_type
    approval.processed_at = datetime_type.now()
    db.add(approval)

    ## cek semua approval pm
    result_all = await db.execute(
        select(LogPenambahanKerjaApprovalPM).where(
            LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == log_id
        )
    )
    all_approvals = result_all.scalars().all()

    approved_count = sum(1 for a in all_approvals if a.status == "disetujui")
    rejected_count = sum(1 for a in all_approvals if a.status == "ditolak")
    total_pm = len(all_approvals)

    if rejected_count > 0:
        log.status = "ditolak_pm"
        if action == "decline":
            log.alasan_penolakan = alasan
    elif approved_count == total_pm:
        log.status = "menunggu_hr"

    db.add(log)
    await db.commit()
    await db.refresh(log)

    ## kirim email notifikasi ke karyawan
    result_user = await db.execute(select(User).where(User.id_user == log.id_user))
    user_pengaju = result_user.scalar_one()

    result_pm = await db.execute(select(User).where(User.id_user == pm_id))
    pm_user = result_pm.scalar_one()

    if log.status == "menunggu_hr":
        background_tasks.add_task(
            send_penambahan_kerja_status_email, log, user_pengaju, pm_user, "menunggu_hr"
        )
        ## kirim email ke hr bahwa ada pengajuan menunggu
        result_hr = await db.execute(select(User).where(User.role.in_(["hr_manager", "staff_hr"])))
        hr_users = result_hr.scalars().all()
        for hr_user in hr_users:
            if hr_user.email:
                background_tasks.add_task(
                    send_pengajuan_notification, user_pengaju, hr_user, "penambahan kerja",
                    sorted([ld.tanggal for ld in log.tanggal_list]), log.keterangan_pengajuan,
                )
    elif log.status == "ditolak_pm":
        log_with_alasan = await db.execute(
            select(LogPenambahanKerja)
            .options(selectinload(LogPenambahanKerja.tanggal_list))
            .where(LogPenambahanKerja.id_pengajuan_kerja == log_id)
        )
        log_detail = log_with_alasan.scalar_one()
        background_tasks.add_task(
            send_penambahan_kerja_status_email, log_detail, user_pengaju, pm_user, "ditolak_pm"
        )
    else:
        background_tasks.add_task(
            send_penambahan_kerja_status_email, log, user_pengaju, pm_user, log.status
        )

    return PenambahanKerjaApprovalResponse(
        detail="Pengajuan berhasil disetujui!" if action == "acc" else "Pengajuan berhasil ditolak!",
        status_baru=log.status
    )


## approvement penambahan kerja oleh hr
## (flow sama cuti: staff_hr selesai di HR, tanpa eskalasi ke direktur)
async def process_penambahan_kerja_hr(
    log_id: int, current_user: User, action: str, alasan: str | None, db: AsyncSession, background_tasks: BackgroundTasks
) -> PenambahanKerjaApprovalResponse:
    result = await db.execute(
        select(LogPenambahanKerja)
        .options(selectinload(LogPenambahanKerja.tanggal_list))
        .where(LogPenambahanKerja.id_pengajuan_kerja == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan!")

    if log.id_user == current_user.id_user:
        raise HTTPException(status_code=400, detail="Tidak bisa memproses pengajuan sendiri")

    if log.status != "menunggu_hr":
        raise HTTPException(status_code=400, detail="Pengajuan tidak dalam status menunggu_hr")

    result_owner = await db.execute(select(User).where(User.id_user == log.id_user))
    owner = result_owner.scalar_one_or_none()

    from datetime import datetime as datetime_type
    from zoneinfo import ZoneInfo
    WIB = ZoneInfo("Asia/Jakarta")

    if action == "acc":
        log.status = "disetujui_hr"
        log.processed_at_hr = datetime_type.now(WIB)
        log.diproses_hr = current_user.id_user
        log.keterangan_disetujui_hr = alasan or "Disetujui"
        detail_msg = "Pengajuan berhasil disetujui!"
    elif action == "decline":
        if not alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")
        log.status = "ditolak_hr"
        log.processed_at_hr = datetime_type.now(WIB)
        log.diproses_hr = current_user.id_user
        log.alasan_penolakan = alasan
        log.keterangan_disetujui_hr = alasan
        detail_msg = "Pengajuan berhasil ditolak!"

    db.add(log)
    await db.commit()
    await db.refresh(log)

    ## email notif ke pemohon
    if owner and owner.email:
        background_tasks.add_task(
            send_penambahan_kerja_status_email, log, owner, current_user, log.status
        )

    return PenambahanKerjaApprovalResponse(
        detail=detail_msg,
        status_baru=log.status
    )


## approvement penambahan kerja oleh direktur
async def process_penambahan_kerja_direktur(
    log_id: int, current_user: User, action: str, alasan: str | None, db: AsyncSession, background_tasks: BackgroundTasks
) -> PenambahanKerjaApprovalResponse:
    if current_user.role != "direktur":
        raise HTTPException(status_code=403, detail="Hanya Direktur yang dapat approve!")

    result = await db.execute(
        select(LogPenambahanKerja)
        .options(selectinload(LogPenambahanKerja.tanggal_list))
        .where(LogPenambahanKerja.id_pengajuan_kerja == log_id)
    )
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan!")

    if log.id_user == current_user.id_user:
        raise HTTPException(status_code=400, detail="Tidak bisa memproses pengajuan sendiri")

    if log.status != "menunggu_direktur":
        raise HTTPException(status_code=400, detail="Pengajuan tidak dalam status menunggu_direktur")

    from datetime import datetime as datetime_type
    from zoneinfo import ZoneInfo
    WIB = ZoneInfo("Asia/Jakarta")

    if action == "acc":
        log.status = "disetujui_direktur"
        log.processed_at_direktur = datetime_type.now(WIB)
        log.diproses_direktur = current_user.id_user
        log.keterangan_disetujui_hr = alasan or "Disetujui Direktur"
        detail_msg = "Pengajuan berhasil disetujui Direktur!"
    elif action == "decline":
        if not alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")
        log.status = "ditolak_direktur"
        log.processed_at_direktur = datetime_type.now(WIB)
        log.diproses_direktur = current_user.id_user
        log.alasan_penolakan = alasan
        log.keterangan_disetujui_hr = alasan
        detail_msg = "Pengajuan ditolak Direktur!"

    db.add(log)
    await db.commit()
    await db.refresh(log)

    ## email notif ke pemohon
    result_owner = await db.execute(select(User).where(User.id_user == log.id_user))
    owner = result_owner.scalar_one_or_none()
    if owner and owner.email:
        background_tasks.add_task(
            send_penambahan_kerja_status_email, log, owner, current_user, log.status
        )

    return PenambahanKerjaApprovalResponse(
        detail=detail_msg,
        status_baru=log.status
    )
