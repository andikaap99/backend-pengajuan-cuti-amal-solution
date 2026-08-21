from datetime import date
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.user import User
from app.models.departemen import Departemen
from app.schemas.hr import HRDashboardRingkasanOut, HRDashboardPersetujuanOut, HRListCutiKaryawanMendatangOut, HRRekapitulasiOut, HRLogCutiOut, HRRingkasanKaryawanOut, HRTabelKaryawanOut, HRTabelDepartemenOut, HRManajemenJatahCutiRingkasanOut, HRDaftarCutiKaryawanOut


## dashboard
## ringkasan
async def get_dashboard_ringkasan_hr(db: AsyncSession):
    today = date.today()
    curr_month = today.month
    curr_year = today.year
    next_month = curr_month + 1
    next_year = curr_year
    if next_year > 12:
        next_year += 1

    result_total = await db.execute(select(func.count(User.id_user)))
    total_karyawan = result_total.scalar_one() or 0

    result_menunggu = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        LogCuti.status == "menunggu_hr"
    ))
    total_menunggu_hr = result_menunggu.scalar_one() or 0

    approved_statuses = ["disetujui_hr", "disetujui_direktur"]

    result_bulan_ini = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        extract("month", LogCuti.tanggal_mulai) == curr_month, 
        extract("year", LogCuti.tanggal_mulai) == curr_year,
        LogCuti.status.in_(approved_statuses)
    ))
    total_cuti_bulan_ini = result_bulan_ini.scalar_one() or 0

    result_bulan_depan = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        extract("month", LogCuti.tanggal_mulai) == next_month,
        extract("year", LogCuti.tanggal_mulai) == next_year,
        LogCuti.status.in_(approved_statuses)
    ))
    total_cuti_bulan_depan = result_bulan_depan.scalar_one() or 0

    return HRDashboardRingkasanOut(
        total_karyawan=total_karyawan,
        menunggu_hr=total_menunggu_hr,
        total_cuti_bulan_ini=total_cuti_bulan_ini,
        total_cuti_bulan_depan=total_cuti_bulan_depan
    )

## list cuti mendatang
async def get_list_cuti_karyawan_mendatang(db: AsyncSession) -> list[HRListCutiKaryawanMendatangOut]:
    today = date.today()

    approved_statuses = ["disetujui_hr", "disetujui_direktur"]

    result = await db.execute(select(LogCuti).options(selectinload(
        LogCuti.user_log)).where(LogCuti.tanggal_mulai >= today,
        LogCuti.status.in_(approved_statuses)).order_by(LogCuti.tanggal_mulai.asc())
    )
    logs = result.scalars().all()

    return [
        HRListCutiKaryawanMendatangOut(
            nama=log.user_log.nama,
            jenis_cuti=log.jenis_cuti,
            tanggal_mulai=log.tanggal_selesai,
            tanggal_selesai=log.tanggal_selesai,
            status=log.status
        ) for log in logs
    ]


## persetujuan
## ringkasan persetujuan
async def get_persetujuan(db: AsyncSession) -> HRDashboardPersetujuanOut:
    today = date.today()
    curr_month = today.month
    curr_year = today.year

    result_menunggu = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(LogCuti.status == "menunggu_hr"))
    total_menunggu = result_menunggu.scalar_one() or 0

    result_disetujui = await db.execute(select(func.count(
        LogCuti.id_log_cuti)).where(
            LogCuti.status == "disetujui_hr",
            extract("month", LogCuti.tanggal_mulai) == curr_month,
            extract("year", LogCuti.tanggal_mulai) == curr_year
            )
        )
    total_disetujui_bulan_ini = result_disetujui.scalar_one() or 0

    result_ditolak = await db.execute(select(func.count(
        LogCuti.id_log_cuti)).where(
            LogCuti.status == "ditolak_hr",
            extract("month", LogCuti.tanggal_mulai) == curr_month,
            extract("year", LogCuti.tanggal_mulai) == curr_year
            )
        )
    total_ditolak_bulan_ini = result_ditolak.scalar_one() or 0

    return HRDashboardPersetujuanOut(
        total_menunggu=total_menunggu,
        disetujui_bulan_ini=total_disetujui_bulan_ini,
        ditolak_bulan_ini=total_ditolak_bulan_ini
    )


## rekap cuti
## rekapitulasi
async def get_rekapitulasi_cuti(db: AsyncSession) -> list[HRRekapitulasiOut]:
    today = date.today()

    approved_statuses = ["disetujui_hr", "disetujui_direktur"]

    result = await db.execute(select(LogCuti).options(selectinload(
        LogCuti.user_log).selectinload(User.user_departemen)).where(
            LogCuti.status.in_(approved_statuses),
            LogCuti.tanggal_mulai <= today,
            LogCuti.tanggal_selesai >= today
        ).order_by(LogCuti.tanggal_mulai.asc())
    )
    logs = result.scalars().all()

    return [
        HRRekapitulasiOut(
            nama=log.user_log.nama,
            nama_departemen=log.user_departemen.nama_departemen,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            total_cuti=log.user_cuti.total_cuti,
            sisa_cuti=log.user_cuti.sisa_cuti
        ) for log in logs
    ]

## log cuti
async def get_cuti_log(db: AsyncSession) -> list[HRLogCutiOut]:
    result = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log),
        selectinload(LogCuti.user_backup),
        selectinload(LogCuti.hr_log)
    ).order_by(LogCuti.tanggal_mulai.desc()))
    logs = result.scalars().all()

    return [
        HRLogCutiOut(
            nama=log.user_log.nama,
            tanggal_mulai=log.tanggal_mulai,
            tanggal_selesai=log.tanggal_selesai,
            durasi=(log.tanggal_selesai - log.tanggal_mulai).days + 1,
            jenis_cuti=log.jenis_cuti,
            keterangan=log.keterangan_cuti,
            pengganti=log.user_backup.nama if log.user_backup else "-",
            status=log.status,
            hr_approved_by=log.hr_log.nama if log.hr_log else "-"
        ) for log in logs
    ]


## data karyawan
## ringkasan
async def get_ringkasan_karyawan(db: AsyncSession) -> HRRingkasanKaryawanOut:
    result_karyawan = await db.execute(select(func.count(User.id_user)))
    total_karyawan = result_karyawan.scalar_one() or 0

    result_departemen = await db.execute(select(func.count(Departemen.id_departemen)))
    total_departemen = result_departemen.scalar_one() or 0

    result_pm = await db.execute(select(func.count(User.id_user)).where(User.role == "pm"))
    total_pm = result_pm.scalar_one() or 0

    return HRRingkasanKaryawanOut(
        total_karyawan=total_karyawan,
        total_departemen=total_departemen,
        total_project_manager=total_pm
    )

## tabel karyawan
async def get_tabel_karyawan(db: AsyncSession) -> list[HRTabelKaryawanOut]:
    result = await db.execute(select(User).options(
        selectinload(User.user_departemen)).order_by(User.nama.asc()))
    users = result.scalars().all()

    return [
        HRTabelKaryawanOut(
            nama=user.nama,
            departemen=user.user_departemen.nama_departemen,
            jabatan=user.role,
            email=user.email,
            status=user.status
        ) for user in users
    ]

## tabel departemen
async def get_tabel_departemen(db: AsyncSession) -> list[HRTabelDepartemenOut]:
    result = await db.execute(select(Departemen).options(
        selectinload(Departemen.user_departemen)
    ).order_by(Departemen.nama_departemen.asc()))
    departements = result.scalars().all()

    return [
        HRTabelDepartemenOut(
            nama_departemen=departement.nama_departemen,
            jumlah_karyawan=len(departement.user_departemen)
        ) for departement in departements
    ]


## manajemen jatah cuti
## ringkasan
async def get_manajemen_jatah_cuti(db: AsyncSession) -> HRManajemenJatahCutiRingkasanOut:
    result_karyawan_aktif = await db.execute(select(
        func.count(User.id_user)).where(User.status == "Aktif"))
    karyawan_aktif = result_karyawan_aktif.scalar_one() or 0

    result_karyawan_cuti = await db.execute(select(
        func.count(User.id_user)).where(User.status == "Cuti"))
    karyawan_cuti = result_karyawan_cuti.scalar_one() or 0

    return HRManajemenJatahCutiRingkasanOut(
        total_karyawan_aktif=karyawan_aktif,
        total_karyawan_cuti=karyawan_cuti
    )

## daftar cuti karyawan
async def get_daftar_cuti_karyawan(db: AsyncSession) -> list[HRDaftarCutiKaryawanOut]:
    roles = ["karyawan", "pm", "hr"]

    result = await db.execute(select(User).options(
        selectinload(User.user_departemen)).where(User.role.in_(roles)))
    users = result.scalars().all()

    return [
        HRDaftarCutiKaryawanOut(
            nama=user.nama,
            nama_departemen=user.user_departemen.nama_departemen,
            total_cuti=user.total_cuti,
            cuti_terpakai=user.total_cuti - user.sisa_cuti,
            sisa_cuti=user.sisa_cuti
        ) for user in users
    ]
