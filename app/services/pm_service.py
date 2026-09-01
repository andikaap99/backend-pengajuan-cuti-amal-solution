from datetime import date
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.pm import PMDashboardRingkasanOut, PMDashboardTimOut, PMPersetujuanRingkasanTimOut, PMHistoryPersetujuanOut, PMRekapCutiRingkasanOut, PMRekapCutiDetailJatah
from app.services.tambah_cuti_service import get_effective_sisa_cuti



## dashboard
## dasboard ringkasan pm
async def get_dashboard_ringkasan(pm_id: int, db: AsyncSession) -> PMDashboardRingkasanOut:
    user = await db.execute(select(User).where(User.id_user == pm_id))
    pm = user.scalar_one()
    effective_pm_sisa = await get_effective_sisa_cuti(pm, date.today().year, db)

    result_team = await db.execute(select(User.id_user).where(User.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return PMDashboardRingkasanOut(
            sisa_cuti=effective_pm_sisa,
            cuti_terpakai=pm.total_cuti-effective_pm_sisa,
            tim_menunggu_appoval=0,
            total_pengajuan_tim=0,
            total_pengajuan_acc_tim=0,
            total_pengajuan_decline_tim=0
        )

    result_menunggu = await db.execute(select(
        func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids), LogCuti.status == "menunggu_pm"
        )
    )
    tim_menunggu_approval = result_menunggu.scalar_one() or 0

    result_total = await db.execute(select(
        func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids)
        )
    )
    total_pengajuan = result_total.scalar() or 0

    pm_approved_statuses = ["disetujui_pm", "menunggu_hr", "disetujui_hr", "ditolak_hr"]
    result_acc = await db.execute(select(
        func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids), LogCuti.status.in_(pm_approved_statuses)
        )
    )
    total_pengajuan_acc_tim = result_acc.scalar() or 0

    result_decline = await db.execute(select(
        func.count(LogCuti.id_log_cuti)).where(
            LogCuti.id_user.in_(team_ids), LogCuti.status == "ditolak_pm"
        )
    )
    total_pengajuan_decline_tim = result_decline.scalar() or 0

    return PMDashboardRingkasanOut(
        sisa_cuti=effective_pm_sisa,
        cuti_terpakai=pm.total_cuti-effective_pm_sisa,
        tim_menunggu_appoval=tim_menunggu_approval,
        total_pengajuan_tim=total_pengajuan,
        total_pengajuan_acc_tim= total_pengajuan_acc_tim,
        total_pengajuan_decline_tim=total_pengajuan_decline_tim
    )

## dashboard anggota tim yang cuti
async def get_dashboard_tim(pm_id: int, db: AsyncSession) -> list[PMDashboardTimOut]:
    result_team = await db.execute(select(User.id_user).where(User.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return []

    result = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log)).where(
            LogCuti.id_user.in_(team_ids), LogCuti.status.in_(
                ["menunggu_pm", "disetujui_pm", "ditolak_pm",])
                ).order_by(LogCuti.tanggal_mulai.asc())
    )
    logs = result.scalars().all()

    return [
        PMDashboardTimOut(
            nama=log.user_log.nama,
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            status=log.status
        ) for log in logs
    ] 


## persetujuan
## ringkasan tim
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


## history cuti
async def get_history_cuti_tim(pm_id: int, db:AsyncSession) -> list[PMHistoryPersetujuanOut]:
    result_team = await db.execute(select(User.id_user).where(User.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return []

    result = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log),
        selectinload(LogCuti.user_backup)).where(
            LogCuti.id_user.in_(team_ids),
            LogCuti.status == "disetujui_hr"
        ).order_by(LogCuti.tanggal_mulai.desc())
    )
    logs = result.scalars().all()

    return [
        PMHistoryPersetujuanOut(
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            nama=log.user_log.nama,
            jenis_cuti=log.jenis_cuti,
            keterangan=log.keterangan_cuti,
            durasi=(log.tanggal_selesai-log.tanggal_mulai).days+1,
            pengganti=log.user_backup.nama if log.user_backup else "-",
            status=log.status
        ) for log in logs
    ]


## rekap cuti
## ringkasan
async def get_rekap_cuti_ringkasan(pm_id: int, db: AsyncSession) -> PMRekapCutiRingkasanOut:
    result_team = await db.execute(select(User.id_user).where(User.id_pm == pm_id))
    team_ids = [row[0] for row in result_team.all()]

    if not team_ids:
        return PMRekapCutiRingkasanOut(
            total_anggota_aktif=0,
            total_cuti_all=0
        )

    total_anggota_aktif = len(team_ids)

    result_total = await db.execute(select(func.count(
        LogCuti.id_log_cuti)).where(LogCuti.id_user.in_(team_ids)))
    total_cuti_all = result_total.scalar() or 0

    return PMRekapCutiRingkasanOut(
        total_anggota_aktif=total_anggota_aktif,
        total_cuti_all=total_cuti_all
    )

## detail jatah
async def get_rekap_cuti_detail(pm_id: int, db: AsyncSession) -> list[PMRekapCutiDetailJatah]:
    today = date.today()

    result_team = await db.execute(select(
        User).options(selectinload(User.user_departemen))
        .where(User.id_pm == pm_id))
    users = result_team.scalars().all()

    if not users:
        return []

    result_cuti = await db.execute(select(LogCuti.id_user).where(
        LogCuti.id_user.in_([u.id_user for u in users]),
        LogCuti.tanggal_mulai <= today,
        LogCuti.tanggal_selesai >= today,
        LogCuti.status == "disetujui_direktur"
    ))
    sedang_cuti_ids = {row[0] for row in result_cuti.all()}

    detail = []
    for user in users:
        effective_sisa = await get_effective_sisa_cuti(user, today.year, db)
        detail.append(PMRekapCutiDetailJatah(
            nama=user.nama,
            nama_departemen=user.user_departemen.nama_departemen,
            penggunaan_cuti=user.total_cuti-effective_sisa,
            sisa_cuti=effective_sisa,
            status="Sedang Cuti" if user.id_user in sedang_cuti_ids else "Aktif"
        ))

    return detail

    