from datetime import date
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.user import ActivityOut


async def get_recent_activities(user_id: int, db: AsyncSession) -> list[ActivityOut]:
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan")

    activities: list[ActivityOut] = []

    result_pengajuan = await db.execute(
        select(LogCuti).where(LogCuti.id_user == user_id)
    )
    logs_pengajuan = result_pengajuan.scalars().all()

    for log in logs_pengajuan:
        activities.append(ActivityOut(
            jenis_aktivitas="pengajuan",
            keterangan=f"Mengajukan cuti {log.jenis_cuti}",
            tanggal=log.tanggal_pengajuan or log.tanggal_mulai,
        ))

    # === 2. Acc / Decline (hanya PM, HR, Direktur) ===
    if user.role in ("pm", "hr", "direktur"):
        # tentukan kolom berdasarkan role
        match user.role:
            case "pm":
                kolom_approve = LogCuti.disetujui_pm
                kolom_tanggal = LogCuti.approved_at_pm
                status_acc = "disetujui_pm"
                status_decline = "ditolak_pm"
            case "hr":
                kolom_approve = LogCuti.disetujui_hr
                kolom_tanggal = LogCuti.approved_at_hr
                status_acc = "disetujui_hr"
                status_decline = "ditolak_hr"
            case "direktur":
                kolom_approve = LogCuti.disetujui_direktur
                kolom_tanggal = LogCuti.approved_at_direktur
                status_acc = "disetujui_direktur"
                status_decline = "ditolak_direktur"

        # query log yang di-acc
        result_acc = await db.execute(
            select(LogCuti).where(
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

        # query log yang ditolak
        result_decline = await db.execute(
            select(LogCuti).where(
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

    # === 3. Sort by tanggal terbaru, ambil 3 teratas ===
    activities.sort(key=lambda x: x.tanggal, reverse=True)
    return activities[:3]
