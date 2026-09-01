from datetime import date
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday import Holiday
from app.models.user import User
from app.models.log_penambahan_kerja import LogPenambahanKerja


async def proses_cuti_hari_libur(db: AsyncSession) -> int:
    today = date.today()
    result_holiday = await db.execute(select(Holiday).where(
        Holiday.tanggal <= today, 
        Holiday.sudah_dikurangi == False, 
        Holiday.is_cuti_bersama == True)
    )
    holidays = result_holiday.scalars().all()

    if not holidays:
        return 0

    jumlah_hari = len(holidays)

    holiday_dates = [h.tanggal for h in holidays]
    result_kerja = await db.execute(select(LogPenambahanKerja.id_user).where(
        LogPenambahanKerja.tanggal_mulai <= holiday_dates[-1], 
        LogPenambahanKerja.tanggal_selesai >= holiday_dates[0],
        LogPenambahanKerja.status == "disetujui_pm").distinct()
    )
    user_kerja_ids = {row[0] for row in result_kerja.all()}

    result_departemen_3 = await db.execute(select(User.id_user).where(User.id_departemen == 3))
    user_dept3_ids = {row[0] for row in result_departemen_3.all()}

    excluded_user_ids = user_kerja_ids & user_dept3_ids

    if excluded_user_ids:
        await db.execute(update(User).where(
            User.sisa_cuti > 0, 
            User.id_user.notin_(excluded_user_ids)
            ).values(sisa_cuti=User.sisa_cuti - jumlah_hari)
        )
    else:
        await db.execute(update(User).where(User.sisa_cuti > 0).values(sisa_cuti=User.sisa_cuti - jumlah_hari))

    for holiday in holidays:
        holiday.sudah_dikurangi = True
        db.add(holiday)

    await db.commit()

    return jumlah_hari