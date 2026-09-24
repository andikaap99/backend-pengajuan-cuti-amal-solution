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

    ## semua role/departemen dengan pengajuan kerja sudah final (acc tahap akhir)
    ## menempel di window hari libur -> dikecualikan dari potongan cuti bersama
    ## final: disetujui_pm (legacy), disetujui_hr (jalur HR), disetujui_direktur (jalur direktur)
    result_kerja = await db.execute(select(LogPenambahanKerja.id_user).where(
        LogPenambahanKerja.status.in_(["disetujui_pm", "disetujui_hr", "disetujui_direktur"]),
        LogPenambahanKerja.id_pengajuan_kerja.in_(
            select(LogPenambahanKerjaDate.id_pengajuan_kerja).where(
                LogPenambahanKerjaDate.tanggal.between(holiday_dates[0], holiday_dates[-1])
            )
        ),
    ).distinct())
    excluded_user_ids = {row[0] for row in result_kerja.all()}

    query = select(User).where(User.role.in_(["karyawan", "pm", "staff_hr", "hr_manager"]))
    if excluded_user_ids:
        query = query.where(User.id_user.notin_(excluded_user_ids))

    result_users = await db.execute(query)
    users = result_users.scalars().all()

    for user in users:
        if user.sisa_cuti > 0:
            user.sisa_cuti -= jumlah_hari
            db.add(user)

        for holiday in holidays:
            if user.role == "hr_manager":
                log_status = "disetujui_direktur"
            else:
                log_status = "disetujui_hr"

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

            ## tanggal individual agar terhitung hitung_cuti_terpakai & kalender
            db.add(LogCutiDate(id_log_cuti=log.id_log_cuti, tanggal=holiday.tanggal))

    for holiday in holidays:
        holiday.sudah_dikurangi = True
        db.add(holiday)

    await db.commit()

    return jumlah_hari
