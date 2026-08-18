from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.schemas.kalender import CutiSayaOut


async def get_my_kalender_cuti(user_id: int, db: AsyncSession) -> list[CutiSayaOut]:
    result = await db.execute(
        select(LogCuti)
        .options(selectinload(LogCuti.user_log))
        .where(LogCuti.id_user == user_id)
    )
    logs = result.scalars().all()

    data = []
    for log in logs:
        current = log.tanggal_mulai
        while current <= log.tanggal_selesai:
            data.append(
                CutiSayaOut(
                    tanggal=current,
                    nama=log.user_log.nama,
                    keterangan=log.keterangan_cuti,
                    jenis_cuti=log.jenis_cuti,
                    status=log.status,
                )
            )
            current += timedelta(days=1)

    return data


async def get_kalender_cuti_tim(user_id: int, db: AsyncSession) -> list[CutiSayaOut]:
    # get user info
    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    if user.role == "pm":
        # PM sees their team members
        result_team = await db.execute(
            select(User.id_user).where(User.id_pm == user_id)
        )
        team_ids = [row[0] for row in result_team.all()]
        all_ids = [user_id] + team_ids
    else:
        # karyawan sees teammates (same id_pm)
        if user.id_pm:
            result_team = await db.execute(
                select(User.id_user).where(User.id_pm == user.id_pm)
            )
            team_ids = [row[0] for row in result_team.all()]
            all_ids = team_ids
        else:
            all_ids = [user_id]

    # get all leave requests from team
    result = await db.execute(
        select(LogCuti)
        .options(selectinload(LogCuti.user_log))
        .where(LogCuti.id_user.in_(all_ids))
    )
    logs = result.scalars().all()

    data = []
    for log in logs:
        current = log.tanggal_mulai
        while current <= log.tanggal_selesai:
            data.append(
                CutiSayaOut(
                    tanggal=current,
                    nama=log.user_log.nama,
                    keterangan=log.keterangan_cuti,
                    jenis_cuti=log.jenis_cuti,
                    status=log.status,
                )
            )
            current += timedelta(days=1)

    return data