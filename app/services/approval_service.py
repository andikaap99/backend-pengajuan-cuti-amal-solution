### ==kode baru==
from datetime import datetime
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.log_cuti_approval_pm import LogCutiApprovalPM
from app.models.log_cuti_date import LogCutiDate
from app.models.user import User
from app.models.user_pm import UserPM
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.log_cuti import ApprovalPMDetail
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.services.email_service import send_status_email, send_pengajuan_notification, generate_surat_cuti
from app.services.tambah_cuti_service import konsumsi_cuti


async def get_queue_card(current_user: User, db: AsyncSession) -> list[PersetujuanQueueCutiOut]:
    ## map status berdasarkan role
    ROLE_STATUS_MAP = {
        "pm": "menunggu_pm",
        "hr_manager": "menunggu_hr",
        "direktur": "menunggu_direktur",
        "staff_hr": "menunggu_hr",
    }

    target_status = ROLE_STATUS_MAP.get(current_user.role)
    if not target_status:
        raise HTTPException(status_code=403, detail="Role tidak memiliki akses queue approval")

    ## pm: filter berdasarkan team via userpm
    if current_user.role == "pm":
        result_team = await db.execute(select(UserPM.id_karyawan).where(UserPM.id_pm == current_user.id_user))
        team_ids = [row[0] for row in result_team.all()]
        if not team_ids:
            return []

        ## ambil log_cuti yang masih menunggu approval PM ini
        result_pending_pm = await db.execute(
            select(LogCutiApprovalPM.id_log_cuti).where(
                LogCutiApprovalPM.id_pm == current_user.id_user,
                LogCutiApprovalPM.status == "menunggu",
            )
        )
        pending_log_ids = [row[0] for row in result_pending_pm.all()]

        result = await db.execute(
            select(LogCuti)
            .options(
                selectinload(LogCuti.user_log).selectinload(User.user_departemen),
                selectinload(LogCuti.user_backup),
                selectinload(LogCuti.tanggal_list),
                selectinload(LogCuti.approval_pm_list).selectinload(LogCutiApprovalPM.pm),
            )
            .where(
                LogCuti.id_user.in_(team_ids),
                LogCuti.status == target_status,
                LogCuti.id_log_cuti.in_(pending_log_ids),
            )
        )
    else:
        ## hr dan direktur: lihat semua pengajuan dengan status yang sesuai (kecuali milik sendiri)
        result = await db.execute(
            select(LogCuti)
            .options(
                selectinload(LogCuti.user_log).selectinload(User.user_departemen),
                selectinload(LogCuti.user_backup),
                selectinload(LogCuti.tanggal_list),
                selectinload(LogCuti.approval_pm_list).selectinload(LogCutiApprovalPM.pm),
            )
            .where(LogCuti.status == target_status, LogCuti.id_user != current_user.id_user)
        )

    logs = result.scalars().all()

    queue = []
    for log in logs:
        queue.append(PersetujuanQueueCutiOut(
            id_log_cuti=log.id_log_cuti,
            nama=log.user_log.nama,
            nama_departemen=log.user_log.user_departemen.nama_departemen,
            jenis_cuti=log.jenis_cuti,
            tanggal=[t.tanggal for t in log.tanggal_list],
            durasi=len(log.tanggal_list),
            pengganti=log.user_backup.nama if log.user_backup else "Tidak ada",
            sisa_cuti=log.user_log.sisa_cuti,
            alasan=log.keterangan_cuti,
            tanggal_pengajuan=log.tanggal_pengajuan,
            approval_pm_detail=[
                ApprovalPMDetail(
                    nama_pm=apm.pm.nama,
                    status=apm.status,
                    processed_at=apm.processed_at,
                )
                for apm in log.approval_pm_list if apm.pm
            ],
        ))

    return queue



## map acceptable status based on role
PROCESSABLE_STATUSES = {
    "pm": "menunggu_pm",
    "hr_manager": "menunggu_hr",
    "direktur": "menunggu_direktur",
    "staff_hr": "menunggu_hr",
}

## map status after accept
AFTER_ACC_STATUSES = {
    "menunggu_pm": "menunggu_hr",
    "menunggu_hr": "disetujui_hr",
    "menunggu_direktur": "disetujui_direktur"
}

## map status after decline
AFTER_DECLINE_STATUSES = {
    "menunggu_pm": "ditolak_pm",
    "menunggu_hr": "ditolak_hr",
    "menunggu_direktur": "ditolak_direktur"
}

## map final approve
FINAL_APPROVED = {"disetujui_hr", "disetujui_direktur", "cuti_bersama"}

async def process_approval(log_cuti_id: int, current_user: User, data: ApprovalRequest, db: AsyncSession, background_tasks: BackgroundTasks) -> ApprovalResponse:
    result_cuti = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log).selectinload(User.user_departemen),
        selectinload(LogCuti.tanggal_list)).where(LogCuti.id_log_cuti == log_cuti_id))
    log_cuti = result_cuti.scalar_one_or_none()

    if not log_cuti:
        raise HTTPException(status_code=404, detail="Log cuti tidak ditemukan!")

    result_user = await db.execute(select(User).options(selectinload(User.user_departemen)).where(User.id_user == log_cuti.id_user))
    user_pengaju = result_user.scalar_one_or_none()

    ## cek self approval
    if log_cuti.id_user == current_user.id_user:
        raise HTTPException(status_code=400, detail="Tidak bisa memproses pengajuan sendiri")

    ## handle approval pm many to many
    if current_user.role == "pm":
        if log_cuti.status != "menunggu_pm":
            raise HTTPException(status_code=400, detail="Pengajuan tidak dalam status menunggu_pm")

        ## cari baris approval pm untuk current_user
        result_approval = await db.execute(
            select(LogCutiApprovalPM).where(
                LogCutiApprovalPM.id_log_cuti == log_cuti_id,
                LogCutiApprovalPM.id_pm == current_user.id_user,
                LogCutiApprovalPM.status == "menunggu",
            )
        )
        approval_pm = result_approval.scalar_one_or_none()

        if not approval_pm:
            raise HTTPException(status_code=400, detail="Anda sudah melakukan approval untuk pengajuan ini")

        if data.action == "acc":
            approval_pm.status = "disetujui"
            approval_pm.processed_at = datetime.now()
            detail_msg = "Pengajuan berhasil disetujui!"
        elif data.action == "decline":
            if not data.alasan:
                raise HTTPException(status_code=400, detail="Alasan harus diisi!")
            approval_pm.status = "ditolak"
            approval_pm.processed_at = datetime.now()
            log_cuti.alasan_penolakan = data.alasan
            detail_msg = "Pengajuan ditolak!"

        db.add(approval_pm)

        ## cek semua approval pm
        result_all_approval = await db.execute(
            select(LogCutiApprovalPM).where(LogCutiApprovalPM.id_log_cuti == log_cuti_id)
        )
        all_approvals = result_all_approval.scalars().all()

        all_approved = all(a.status == "disetujui" for a in all_approvals)
        any_rejected = any(a.status == "ditolak" for a in all_approvals)

        if any_rejected:
            log_cuti.status = "ditolak_pm"
            new_status = "ditolak_pm"
        elif all_approved:
            log_cuti.status = "menunggu_hr"
            new_status = "menunggu_hr"
        else:
            new_status = log_cuti.status

        db.add(log_cuti)
        await db.commit()

        ## kirim email notifikasi
        pending_pm_names = []
        if new_status == "menunggu_pm":
            pending_pm_ids = [a.id_pm for a in all_approvals if a.status == "menunggu"]
            if pending_pm_ids:
                result_pm_names = await db.execute(select(User.nama).where(User.id_user.in_(pending_pm_ids)))
                pending_pm_names = [row[0] for row in result_pm_names.all()]

        if any_rejected:
            background_tasks.add_task(send_status_email, log_cuti, user_pengaju, current_user, new_status)
        elif all_approved:
            background_tasks.add_task(send_status_email, log_cuti, user_pengaju, current_user, new_status)
            ## kirim email ke hr bahwa ada pengajuan menunggu
            result_hr = await db.execute(select(User).where(User.role.in_(["hr_manager", "staff_hr"])))
            hr_users = result_hr.scalars().all()
            for hr_user in hr_users:
                if hr_user.email:
                    background_tasks.add_task(
                        send_pengajuan_notification, user_pengaju, hr_user, "cuti tahunan",
                        sorted([ld.tanggal for ld in log_cuti.tanggal_list]), log_cuti.keterangan_cuti,
                    )
        else:
            background_tasks.add_task(send_status_email, log_cuti, user_pengaju, current_user, new_status, pending_pm_names)

        return ApprovalResponse(
            detail=detail_msg,
            status_baru=new_status
        )

    ## handle approval hr dan direktur (tetap sama seperti sebelumnya)
    target_status = PROCESSABLE_STATUSES.get(current_user.role)
    if not target_status:
        raise HTTPException(status_code=403, detail="Role tidak memiliki akses")

    if log_cuti.status != target_status:
        raise HTTPException(status_code=400, detail=f"Pengajuan tidak dalam status {target_status}")

    if data.action == "acc":
        new_status = AFTER_ACC_STATUSES[log_cuti.status]
        log_cuti.status = new_status

        if current_user.role == "hr_manager":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = datetime.now()
        elif current_user.role == "staff_hr":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = datetime.now()
        elif current_user.role == "direktur":
            log_cuti.diproses_direktur = current_user.id_user
            log_cuti.processed_at_direktur = datetime.now()

        detail_msg = "Pengajuan berhasil disetujui!"
        lama_cuti = len(log_cuti.tanggal_list)

    elif data.action == "decline":
        if not data.alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")

        new_status = AFTER_DECLINE_STATUSES[log_cuti.status]
        log_cuti.status = new_status
        log_cuti.alasan_penolakan = data.alasan

        if current_user.role == "hr_manager":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = datetime.now()
        elif current_user.role == "staff_hr":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = datetime.now()
        elif current_user.role == "direktur":
            log_cuti.diproses_direktur = current_user.id_user
            log_cuti.processed_at_direktur = datetime.now()

        detail_msg = "Pengajuan ditolak!"

    db.add(log_cuti)

    if data.action == "acc" and new_status in FINAL_APPROVED:
        today = datetime.now().date()
        ## set status "cuti" hanya jika cuti sedang berjalan hari ini
        cuti_dates = [ld.tanggal for ld in log_cuti.tanggal_list]
        if today in cuti_dates:
            user_pengaju.status = "Cuti"
        await konsumsi_cuti(user_pengaju, lama_cuti, db)

    await db.commit()

    ## kirim notifikasi email setelah commit berhasil
    if new_status in FINAL_APPROVED:
        ## status final: kirim email dengan surat pdf
        background_tasks.add_task(generate_surat_cuti, log_cuti, user_pengaju, current_user)
    elif new_status == "menunggu_direktur":
        ## kirim notifikasi teks ke karyawan
        background_tasks.add_task(send_status_email, log_cuti, user_pengaju, current_user, new_status)
        ## kirim email ke direktur bahwa ada pengajuan menunggu
        result_dir = await db.execute(select(User).where(User.role == "direktur"))
        direktur_users = result_dir.scalars().all()
        for direktur in direktur_users:
            if direktur.email:
                background_tasks.add_task(
                    send_pengajuan_notification, user_pengaju, direktur, "cuti tahunan",
                    sorted([ld.tanggal for ld in log_cuti.tanggal_list]), log_cuti.keterangan_cuti,
                )
    else:
        ## status belum final: kirim notifikasi teks biasa
        background_tasks.add_task(send_status_email, log_cuti, user_pengaju, current_user, new_status)

    return ApprovalResponse(
        detail=detail_msg,
        status_baru=new_status
    )