from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.pengajuan import PersetujuanQueueCutiOut


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

    return [
        PersetujuanQueueCutiOut(
            nama=log.user_log.nama,
            nama_departemen=log.user_log.user_departemen.nama_departemen,
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            pengganti=log.user_backup.nama if log.user_backup else "Tidak ada",
            sisa_cuti=log.user_log.sisa_cuti,
            alasan=log.keterangan_cuti,
        )
        for log in logs
    ]