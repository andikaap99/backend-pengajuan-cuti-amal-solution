from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.log_cuti_approval_pm import LogCutiApprovalPM
from app.models.user import User
from app.schemas.user import ActivityOut


async def get_recent_activities(user_id: int, db: AsyncSession) -> list[ActivityOut]:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    activities: list[ActivityOut] = []

    result_pengajuan = await db.execute(
        select(LogCuti)
        .options(selectinload(LogCuti.tanggal_list))
        .where(LogCuti.id_user == user_id)
    )
    logs_pengajuan = result_pengajuan.scalars().unique().all()

    for log in logs_pengajuan:
        if log.tanggal_pengajuan:
            tanggal_aktivitas = log.tanggal_pengajuan
        elif log.tanggal_list:
            earliest = min(ld.tanggal for ld in log.tanggal_list)
            tanggal_aktivitas = datetime.combine(earliest, datetime.min.time())
        else:
            tanggal_aktivitas = datetime.min

        activities.append(ActivityOut(
            jenis_aktivitas="pengajuan",
            keterangan=f"Mengajukan cuti {log.jenis_cuti}",
            tanggal=tanggal_aktivitas,
        ))

    ## acc / decline (hanya pm via log_cuti_approval_pm)
    if user.role == "pm":
        ## query log approval pm yang diproses oleh pm ini
        result_acc = await db.execute(
            select(LogCutiApprovalPM)
            .options(selectinload(LogCutiApprovalPM.log_cuti).selectinload(LogCuti.user_log))
            .where(
                LogCutiApprovalPM.id_pm == user_id,
                LogCutiApprovalPM.status == "disetujui",
            )
        )
        logs_acc = result_acc.scalars().all()

        for approval in logs_acc:
            if approval.log_cuti and approval.log_cuti.user_log:
                activities.append(ActivityOut(
                    jenis_aktivitas="acc",
                    keterangan=f"Menyetujui cuti {approval.log_cuti.user_log.nama}",
                    tanggal=approval.processed_at,
                ))

        ## query log approval pm yang ditolak
        result_decline = await db.execute(
            select(LogCutiApprovalPM)
            .options(selectinload(LogCutiApprovalPM.log_cuti).selectinload(LogCuti.user_log))
            .where(
                LogCutiApprovalPM.id_pm == user_id,
                LogCutiApprovalPM.status == "ditolak",
            )
        )
        logs_decline = result_decline.scalars().all()

        for approval in logs_decline:
            if approval.log_cuti and approval.log_cuti.user_log:
                activities.append(ActivityOut(
                    jenis_aktivitas="decline",
                    keterangan=f"Menolak cuti {approval.log_cuti.user_log.nama}",
                    tanggal=approval.processed_at,
                ))

    ## acc / decline (hr dan direktur)
    if user.role in ("hr_manager", "direktur", "staff_hr"):
        match user.role:
            case "hr_manager":
                kolom_approve = LogCuti.diproses_hr
                kolom_tanggal = LogCuti.processed_at_hr
                status_acc = "disetujui_hr"
                status_decline = "ditolak_hr"
            case "staff_hr":
                kolom_approve = LogCuti.diproses_hr
                kolom_tanggal = LogCuti.processed_at_hr
                status_acc = "disetujui_hr"
                status_decline = "ditolak_hr"
            case "direktur":
                kolom_approve = LogCuti.diproses_direktur
                kolom_tanggal = LogCuti.processed_at_direktur
                status_acc = "disetujui_direktur"
                status_decline = "ditolak_direktur"

        ## query log yang diacc
        result_acc = await db.execute(
            select(LogCuti).options(selectinload(LogCuti.user_log)).where(
                kolom_approve == user_id,
                LogCuti.status == status_acc,
            )
        )
        logs_acc = result_acc.scalars().all()

        for log in logs_acc:
            activities.append(ActivityOut(
                jenis_aktivitas="acc",
                keterangan=f"Menyetujui cuti {log.user_log.nama}",
                tanggal=getattr(log, kolom_tanggal.key),
            ))

        ## query log yang ditolak
        result_decline = await db.execute(
            select(LogCuti).options(selectinload(LogCuti.user_log)).where(
                kolom_approve == user_id,
                LogCuti.status == status_decline,
            )
        )
        logs_decline = result_decline.scalars().all()

        for log in logs_decline:
            activities.append(ActivityOut(
                jenis_aktivitas="decline",
                keterangan=f"Menolak cuti {log.user_log.nama}",
                tanggal=getattr(log, kolom_tanggal.key),
            ))

    ## sort by tanggal terbaru, ambil 3 teratas
    activities.sort(key=lambda x: x.tanggal if x.tanggal else datetime.min, reverse=True)
    
    return activities[:3]
