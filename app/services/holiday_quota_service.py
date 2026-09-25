from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.holiday import Holiday
from app.models.user import User
from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.log_penambahan_kerja_date import LogPenambahanKerjaDate
from app.models.log_cuti import LogCuti
from app.models.log_cuti_date import LogCutiDate


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
    
    result_kerja = await db.execute(
        select(LogPenambahanKerja.id_user, LogPenambahanKerjaDate.tanggal)
        .join(LogPenambahanKerjaDate,
              LogPenambahanKerjaDate.id_pengajuan_kerja == LogPenambahanKerja.id_pengajuan_kerja)
        .where(
            LogPenambahanKerja.status.in_(["disetujui_hr", "disetujui_direktur"]),
            LogPenambahanKerjaDate.tanggal.between(holiday_dates[0], holiday_dates[-1]),
        )
    )
    kerja_dates_per_user: dict[int, set[date]] = {}
    for id_user, tanggal in result_kerja.all():
        kerja_dates_per_user.setdefault(id_user, set()).add(tanggal)

    query = select(User).where(User.role.in_(["karyawan", "pm", "staff_hr", "hr_manager"]))
    result_users = await db.execute(query)
    users = result_users.scalars().all()

    for user in users:
        kerja = kerja_dates_per_user.get(user.id_user, set())
        tanggal_dipotong = [h.tanggal for h in holidays if h.tanggal not in kerja]

        ## semua tanggal window di-kerja-i -> tidak dipotong, tidak ada log
        if not tanggal_dipotong:
            continue

        if user.sisa_cuti > 0:
            user.sisa_cuti -= len(tanggal_dipotong)
            db.add(user)

        log_status = "disetujui_direktur" if user.role == "hr_manager" else "disetujui_hr"

        ## 1 log + baris tanggal hanya untuk hari yang benar-benar dipotong
        log = LogCuti(
            id_user=user.id_user,
            jenis_cuti="cuti bersama",
            keterangan_cuti="Potongan cuti bersama nasional",
            status=log_status,
            tanggal_pengajuan=datetime.now(),
            pengganti=None,
            alasan_penolakan=None,
            diproses_hr=None,
            diproses_direktur=None,
            edited_at=None,
        )
        db.add(log)
        await db.flush()

        for t in sorted(tanggal_dipotong):
            db.add(LogCutiDate(id_log_cuti=log.id_log_cuti, tanggal=t))

    for holiday in holidays:
        holiday.sudah_dikurangi = True
        db.add(holiday)

    await db.commit()

    return jumlah_hari
