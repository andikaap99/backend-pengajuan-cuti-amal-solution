from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.pm import PMPersetujuanRingkasanTimOut, PMPersetujuanQueueCutiOut


async def get_ringkasan_tim(pm_id: int, db: AsyncSession) -> PMPersetujuanRingkasanTimOut:
    today = date.today()
    year = today.year

    # get all team members under this PM
    result_team = await db.execute(
        select(User.id_user).where(User.id_pm == pm_id)
    )
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return PMPersetujuanRingkasanTimOut(
            tahun=year,
            total_pengajuan=0,
            menunggu_persetujuan=0,
            sedang_cuti=0,
        )

    # total pengajuan
    result_total = await db.execute(
        select(func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids),
        )
    )
    total_pengajuan = result_total.scalar() or 0

    # menunggu persetujuan (status masih menunggu_pm)
    result_menunggu = await db.execute(
        select(func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids),
            LogCuti.status == "menunggu_pm",
        )
    )
    menunggu_persetujuan = result_menunggu.scalar() or 0

    # sedang cuti (sudah disetujui direktur dan tanggal sekarang dalam range cuti)
    result_sedang = await db.execute(
        select(func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids),
            LogCuti.status == "disetujui_direktur",
            LogCuti.tanggal_mulai <= today,
            LogCuti.tanggal_selesai >= today,
        )
    )
    sedang_cuti = result_sedang.scalar() or 0

    return PMPersetujuanRingkasanTimOut(
        tahun=year,
        total_pengajuan=total_pengajuan,
        menunggu_persetujuan=menunggu_persetujuan,
        sedang_cuti=sedang_cuti,
    )


async def get_queue_card(pm_id: int, db: AsyncSession) -> list[PMPersetujuanQueueCutiOut]:
    # get all team members under this PM
    result_team = await db.execute(
        select(User.id_user).where(User.id_pm == pm_id)
    )
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return []

    # get all pending leave requests from team
    result = await db.execute(
        select(LogCuti)
        .options(
            selectinload(LogCuti.user_log).selectinload(User.user_departemen),
            selectinload(LogCuti.user_backup),
        )
        .where(
            LogCuti.id_user.in_(team_ids),
            LogCuti.status == "menunggu_pm",
        )
    )
    logs = result.scalars().all()

    return [
        PMPersetujuanQueueCutiOut(
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