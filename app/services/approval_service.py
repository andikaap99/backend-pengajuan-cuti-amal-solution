from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.approval import ApprovalRequest, ApprovalResponse
from app.schemas.pengajuan import PersetujuanQueueCutiOut
from app.services.tambah_cuti_service import get_effective_sisa_cuti


async def get_queue_card(current_user: User, db: AsyncSession) -> list[PersetujuanQueueCutiOut]:
    status_map = {
        "pm": "menunggu_pm",
        "hr": "menunggu_hr",
        "direktur": "menunggu_direktur",
    }
    target_status = status_map.get(current_user.role)
    if not target_status:
        raise HTTPException(status_code=403, detail="Role tidak memiliki akses queue approval")

    query = (
        select(LogCuti)
        .options(
            selectinload(LogCuti.user_log).selectinload(User.user_departemen),
            selectinload(LogCuti.user_backup),
        )
        .where(LogCuti.status == target_status)
    )

    if current_user.role == "pm":
        result_team = await db.execute(select(User.id_user).where(User.id_pm == current_user.id_user))
        team_ids = [row[0] for row in result_team.all()]
        if not team_ids:
            return []
        query = query.where(LogCuti.id_user.in_(team_ids))

    result = await db.execute(query)
    logs = result.scalars().all()

    queue = []
    for log in logs:
        effective_sisa = await get_effective_sisa_cuti(log.user_log, date.today().year, db)
        queue.append(PersetujuanQueueCutiOut(
            id_log_cuti=log.id_log_cuti,
            nama=log.user_log.nama,
            nama_departemen=log.user_log.user_departemen.nama_departemen,
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            pengganti=log.user_backup.nama if log.user_backup else "Tidak ada",
            sisa_cuti=effective_sisa,
            alasan=log.keterangan_cuti,
        ))

    return queue



## map acceptable status based on role
PROCESSABLE_STATUSES = {
    "pm": "menunggu_pm",
    "hr": "menunggu_hr",
    "direktur": "menunggu_direktur"
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
FINAL_APPROVED = {"disetujui_hr", "disetujui_direktur"}

async def process_approval(log_cuti_id: int, current_user: User, data: ApprovalRequest, db: AsyncSession) -> ApprovalResponse:
    result_cuti = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log)).where(LogCuti.id_log_cuti == log_cuti_id))
    log_cuti = result_cuti.scalar_one_or_none()

    if not log_cuti:
        raise HTTPException(status_code=404, detail="Log cuti tidak ditemukan!")

    result_user = await db.execute(select(User).where(User.id_user == log_cuti.id_user))
    user_pengaju = result_user.scalar_one_or_none()

    target_status = PROCESSABLE_STATUSES.get(current_user.role)
    if not target_status:
        raise HTTPException(status_code=403, detail="Role tidak memiliki akses")

    if log_cuti.status != target_status:
        raise HTTPException(status_code=400, detail=f"Pengajuan tidak dalam status {target_status}")

    if current_user.role == "pm":
        if log_cuti.user_log.id_pm != current_user.id_user:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki akses untuk pengajuan ini!")

    if data.action == "acc":
        new_status = AFTER_ACC_STATUSES[log_cuti.status]
        log_cuti.status = new_status

        if current_user.role == "pm":
            log_cuti.diproses_pm = current_user.id_user
            log_cuti.processed_at_pm = date.today()
        elif current_user.role == "hr":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = date.today()
        elif current_user.role == "direktur":
            log_cuti.diproses_direktur = current_user.id_user
            log_cuti.processed_at_direktur = date.today()

        detail_msg = "Pengajuan berhasil disetujui!"
        lama_cuti = (log_cuti.tanggal_selesai - log_cuti.tanggal_mulai).days + 1

    elif data.action == "decline":
        if not data.alasan:
            raise HTTPException(status_code=400, detail="Alasan harus diisi!")

        new_status = AFTER_DECLINE_STATUSES[log_cuti.status]
        log_cuti.status = new_status
        log_cuti.alasan_penolakan = data.alasan

        if current_user.role == "pm":
            log_cuti.diproses_pm = current_user.id_user
            log_cuti.processed_at_pm = date.today()
        elif current_user.role == "hr":
            log_cuti.diproses_hr = current_user.id_user
            log_cuti.processed_at_hr = date.today()
        elif current_user.role == "direktur":
            log_cuti.diproses_direktur = current_user.id_user
            log_cuti.processed_at_direktur = date.today()

        detail_msg = "Pengajuan ditolak!"

    db.add(log_cuti)

    if data.action == "acc" and new_status in FINAL_APPROVED:
        today = date.today()
        # set status "Cuti" hanya jika cuti sedang berjalan hari ini
        if log_cuti.tanggal_mulai <= today <= log_cuti.tanggal_selesai:
            user_pengaju.status = "Cuti"
        user_pengaju.sisa_cuti -= lama_cuti
        db.add(user_pengaju)

    await db.commit()

    return ApprovalResponse(
        detail=detail_msg,
        status_baru=new_status
    )