from datetime import date, datetime
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.log_cuti import LogCuti
from app.models.log_cuti_date import LogCutiDate
from app.models.log_cuti_approval_pm import LogCutiApprovalPM
from app.models.log_cuti_ekstra import LogCutiEkstra
from app.models.log_penambahan_kerja import LogPenambahanKerja
from app.models.log_penambahan_kerja_date import LogPenambahanKerjaDate
from app.models.log_penambahan_kerja_approval_pm import LogPenambahanKerjaApprovalPM
from app.models.log_reassignment_approval import LogReassignmentApproval
from app.models.user import User
from app.models.user_pm import UserPM
from app.models.departemen import Departemen
from app.schemas.hr import HRDashboardRingkasanOut, HRDashboardPersetujuanOut, HRListCutiKaryawanMendatangOut, HRRekapitulasiOut, HRLogCutiOut, HRRingkasanKaryawanOut, HRTabelKaryawanOut, HRTabelDepartemenOut, HRManajemenJatahCutiRingkasanOut, HRDaftarCutiKaryawanOut, HRLogPenambahanKerjaOut, HRRekapitulasiPenambahanKerjaOut
from app.core.security import hash_password
from app.services.email_service import send_pengajuan_notification
from app.services.cuti_service import hitung_cuti_terpakai


## dashboard
## ringkasan
async def get_dashboard_ringkasan_hr(db: AsyncSession, user_id: int, role: str):
    today = date.today()
    curr_month = today.month
    curr_year = today.year

    result_total = await db.execute(select(func.count(User.id_user)))
    total_karyawan = result_total.scalar_one() or 0

    target_status_cuti = "menunggu_hr" if role in ("hr_manager", "staff_hr") else "menunggu_direktur"
    result_menunggu_cuti = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        LogCuti.status == target_status_cuti
    ))
    total_menunggu_cuti = result_menunggu_cuti.scalar_one() or 0

    target_status_kerja = "menunggu_hr" if role in ("hr_manager", "staff_hr") else "menunggu_direktur"
    result_menunggu_kerja = await db.execute(select(func.count(LogPenambahanKerja.id_pengajuan_kerja)).where(
        LogPenambahanKerja.status == target_status_kerja
    ))
    total_menunggu_kerja = result_menunggu_kerja.scalar_one() or 0

    total_menunggu = total_menunggu_cuti + total_menunggu_kerja

    result_total_cuti = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        extract("month", LogCuti.tanggal_pengajuan) == curr_month,
        extract("year", LogCuti.tanggal_pengajuan) == curr_year,
    ))
    total_log_cuti = result_total_cuti.scalar_one() or 0

    result_total_kerja = await db.execute(select(func.count(LogPenambahanKerja.id_pengajuan_kerja)).where(
        extract("month", LogPenambahanKerja.tanggal_pengajuan) == curr_month,
        extract("year", LogPenambahanKerja.tanggal_pengajuan) == curr_year,
    ))
    total_log_kerja = result_total_kerja.scalar_one() or 0

    total_pengajuan = total_log_cuti + total_log_kerja

    acc_statuses_cuti = ["disetujui_pm", "disetujui_hr", "disetujui_direktur", "cuti_bersama"]
    result_diacc_cuti = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        LogCuti.status.in_(acc_statuses_cuti),
        extract("month", LogCuti.tanggal_pengajuan) == curr_month,
        extract("year", LogCuti.tanggal_pengajuan) == curr_year,
    ))
    diacc_cuti = result_diacc_cuti.scalar_one() or 0

    acc_statuses_kerja = ["disetujui_pm", "disetujui_hr", "disetujui_direktur"]
    result_diacc_kerja = await db.execute(select(func.count(LogPenambahanKerja.id_pengajuan_kerja)).where(
        LogPenambahanKerja.status.in_(acc_statuses_kerja),
        extract("month", LogPenambahanKerja.tanggal_pengajuan) == curr_month,
        extract("year", LogPenambahanKerja.tanggal_pengajuan) == curr_year,
    ))
    diacc_kerja = result_diacc_kerja.scalar_one() or 0

    total_diacc = diacc_cuti + diacc_kerja

    tolak_statuses_cuti = ["ditolak_pm", "ditolak_hr", "ditolak_direktur"]
    result_ditolak_cuti = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(
        LogCuti.status.in_(tolak_statuses_cuti),
        extract("month", LogCuti.tanggal_pengajuan) == curr_month,
        extract("year", LogCuti.tanggal_pengajuan) == curr_year,
    ))
    ditolak_cuti = result_ditolak_cuti.scalar_one() or 0

    result_ditolak_kerja = await db.execute(select(func.count(LogPenambahanKerja.id_pengajuan_kerja)).where(
        LogPenambahanKerja.status.in_(["ditolak_pm", "ditolak_hr", "ditolak_direktur"]),
        extract("month", LogPenambahanKerja.tanggal_pengajuan) == curr_month,
        extract("year", LogPenambahanKerja.tanggal_pengajuan) == curr_year,
    ))
    ditolak_kerja = result_ditolak_kerja.scalar_one() or 0

    total_ditolak = ditolak_cuti + ditolak_kerja

    result_user = await db.execute(select(User).where(User.id_user == user_id))
    user = result_user.scalar_one()

    cuti_terpakai = await hitung_cuti_terpakai(user_id, db)

    return HRDashboardRingkasanOut(
        total_karyawan=total_karyawan,
        menunggu=total_menunggu,
        total_pengajuan=total_pengajuan,
        total_pengajuan_diacc=total_diacc,
        total_pengajuan_ditolak=total_ditolak,
        total_cuti=user.total_cuti,
        cuti_terpakai=cuti_terpakai,
        sisa_cuti=user.sisa_cuti
    )

## list cuti mendatang
async def get_list_cuti_karyawan_mendatang(db: AsyncSession) -> list[HRListCutiKaryawanMendatangOut]:
    today = date.today()

    approved_statuses = ["disetujui_hr", "disetujui_direktur", "cuti_bersama"]

    ## tanggal mulai = min(tanggal_list) per log (pengganti kolom tanggal_mulai lama)
    min_tgl = (
        select(LogCutiDate.id_log_cuti, func.min(LogCutiDate.tanggal).label("mulai"))
        .group_by(LogCutiDate.id_log_cuti)
        .subquery()
    )

    result = await db.execute(
        select(LogCuti)
        .join(min_tgl, min_tgl.c.id_log_cuti == LogCuti.id_log_cuti)
        .options(
            selectinload(LogCuti.user_log),
            selectinload(LogCuti.tanggal_list),
        )
        .where(min_tgl.c.mulai >= today, LogCuti.status.in_(approved_statuses))
        .order_by(min_tgl.c.mulai.asc())
    )
    logs = result.scalars().unique().all()

    return [
        HRListCutiKaryawanMendatangOut(
            nama=log.user_log.nama,
            jenis_cuti=log.jenis_cuti,
            tanggal=sorted([ld.tanggal for ld in log.tanggal_list]),
            tanggal_pengajuan=log.tanggal_pengajuan,
            status=log.status
        ) for log in logs
    ]


## persetujuan
## ringkasan persetujuan
async def get_persetujuan(db: AsyncSession, role: str) -> HRDashboardPersetujuanOut:
    today = date.today()
    curr_month = today.month
    curr_year = today.year

    ## tanggal mulai log = min(tanggal_list) per log
    min_tgl = (
        select(LogCutiDate.id_log_cuti, func.min(LogCutiDate.tanggal).label("mulai"))
        .group_by(LogCutiDate.id_log_cuti)
        .subquery()
    )

    target_status = "menunggu_hr" if role in ("hr_manager", "staff_hr") else "menunggu_direktur"
    result_menunggu = await db.execute(select(func.count(LogCuti.id_log_cuti)).where(LogCuti.status == target_status))
    total_menunggu = result_menunggu.scalar_one() or 0

    acc_status = "disetujui_hr" if role in ("hr_manager", "staff_hr") else "disetujui_direktur"
    result_disetujui = await db.execute(
        select(func.count(LogCuti.id_log_cuti))
        .select_from(LogCuti)
        .join(min_tgl, min_tgl.c.id_log_cuti == LogCuti.id_log_cuti)
        .where(
            LogCuti.status.in_([acc_status, "cuti_bersama"]),
            extract("month", min_tgl.c.mulai) == curr_month,
            extract("year", min_tgl.c.mulai) == curr_year,
        )
    )
    total_disetujui_bulan_ini = result_disetujui.scalar_one() or 0

    reject_status = "ditolak_hr" if role in ("hr_manager", "staff_hr") else "ditolak_direktur"
    result_ditolak = await db.execute(
        select(func.count(LogCuti.id_log_cuti))
        .select_from(LogCuti)
        .join(min_tgl, min_tgl.c.id_log_cuti == LogCuti.id_log_cuti)
        .where(
            LogCuti.status == reject_status,
            extract("month", min_tgl.c.mulai) == curr_month,
            extract("year", min_tgl.c.mulai) == curr_year,
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

    approved_statuses = ["disetujui_hr", "disetujui_direktur", "cuti_bersama"]

    result = await db.execute(
        select(User).options(selectinload(User.user_departemen)).where(
            User.role.in_(["karyawan", "pm", "hr_manager", "staff_hr"])
        ).order_by(User.nama.asc())
    )
    users = result.scalars().all()

    rekap = []
    for user in users:
        has_approved = await db.execute(
            select(LogCuti.id_log_cuti).where(
                LogCuti.id_user == user.id_user,
                LogCuti.status.in_(approved_statuses)
            ).limit(1)
        )
        if not has_approved.scalar_one_or_none():
            continue

        rekap.append(HRRekapitulasiOut(
            nama=user.nama,
            nama_departemen=user.user_departemen.nama_departemen,
            total_cuti=user.total_cuti,
            cuti_terpakai=await hitung_cuti_terpakai(user.id_user, db),
            sisa_cuti=user.sisa_cuti
        ))

    return rekap

## log cuti
async def get_cuti_log(db: AsyncSession) -> list[HRLogCutiOut]:
    min_tgl = (
        select(LogCutiDate.id_log_cuti, func.min(LogCutiDate.tanggal).label("mulai"))
        .group_by(LogCutiDate.id_log_cuti)
        .subquery()
    )

    result = await db.execute(select(LogCuti).options(
        selectinload(LogCuti.user_log),
        selectinload(LogCuti.user_backup),
        selectinload(LogCuti.hr_log),
        selectinload(LogCuti.direktur_log),
        selectinload(LogCuti.approval_pm_list).selectinload(LogCutiApprovalPM.pm),
        selectinload(LogCuti.tanggal_list),
    )
    .join(min_tgl, min_tgl.c.id_log_cuti == LogCuti.id_log_cuti)
    .order_by(min_tgl.c.mulai.desc()))
    logs = result.scalars().unique().all()

    def get_approved_by(log: LogCuti) -> str:
        if log.hr_log:
            return log.hr_log.nama
        if log.direktur_log:
            return log.direktur_log.nama
        rejected_pm = [a.pm.nama for a in log.approval_pm_list if a.status == "ditolak"]
        if rejected_pm:
            return rejected_pm[0]
        return "-"

    return [
        HRLogCutiOut(
            nama=log.user_log.nama,
            tanggal=sorted([ld.tanggal for ld in log.tanggal_list]),
            durasi=len(log.tanggal_list),
            jenis_cuti=log.jenis_cuti,
            keterangan=log.keterangan_cuti,
            pengganti=log.user_backup.nama if log.user_backup else "-",
            tanggal_pengajuan=log.tanggal_pengajuan,
            status=log.status,
            approved_by=get_approved_by(log)
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
        selectinload(User.user_departemen),
        selectinload(User.karyawan_pm_list).selectinload(UserPM.pm)).order_by(User.nama.asc()))
    users = result.scalars().all()

    return [
        HRTabelKaryawanOut(
            id_user=user.id_user,
            username=user.username,
            password=user.password,
            nama=user.nama,
            departemen=user.user_departemen.nama_departemen,
            jabatan=user.role,
            email=user.email,
            no_telp=user.no_telp,
            tanggal_bergabung=user.tanggal_bergabung,
            nama_pm=[upm.pm.nama for upm in user.karyawan_pm_list],
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
    roles = ["karyawan", "pm", "hr_manager", "staff_hr"]
    today = date.today()

    result = await db.execute(select(User).options(
        selectinload(User.user_departemen)).where(User.role.in_(roles)))
    users = result.scalars().all()

    daftar = []
    for user in users:
        cuti_terpakai = await hitung_cuti_terpakai(user.id_user, db)
        daftar.append(HRDaftarCutiKaryawanOut(
            nama=user.nama,
            nama_departemen=user.user_departemen.nama_departemen,
            total_cuti=user.total_cuti,
            cuti_terpakai=cuti_terpakai,
            sisa_cuti=user.sisa_cuti
        ))

    return daftar


## edit karyawan
async def edit_karyawan(user_id: int, data: dict, db: AsyncSession, background_tasks: BackgroundTasks) -> str:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan!")

    pm_add = data.pop("pm_add", None)
    pm_remove = data.pop("pm_remove", None)
    password = data.pop("password", None)

    ## hash password jika ada
    if password:
        user.password = hash_password(password)

    ## validasi username
    username = data.get("username")
    if username:
        if " " in username:
            raise HTTPException(status_code=400, detail="Username tidak boleh mengandung spasi")
        result_existing = await db.execute(
            select(User).where(User.username == username, User.id_user != user_id)
        )
        if result_existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username sudah digunakan")

    for field, value in data.items():
        if value is not None:
            setattr(user, field, value)

    db.add(user)

    if pm_remove:
        for pm_id in pm_remove:
            ## hapus record user_pm
            result_pm = await db.execute(
                select(UserPM).where(UserPM.id_karyawan == user_id, UserPM.id_pm == pm_id)
            )
            existing = result_pm.scalar_one_or_none()
            if existing:
                await db.delete(existing)

            ## cari semua log_cuti karyawan ini yang masih menunggu_pm
            result_pending_logs = await db.execute(
                select(LogCuti.id_log_cuti).where(
                    LogCuti.id_user == user_id,
                    LogCuti.status == "menunggu_pm",
                )
            )
            pending_log_ids = [row[0] for row in result_pending_logs.all()]

            ## hapus approval log_cuti pm lama yang masih menunggu
            if pending_log_ids:
                result_approvals = await db.execute(
                    select(LogCutiApprovalPM).where(
                        LogCutiApprovalPM.id_log_cuti.in_(pending_log_ids),
                        LogCutiApprovalPM.id_pm == pm_id,
                        LogCutiApprovalPM.status == "menunggu",
                    )
                )
                for approval in result_approvals.scalars().all():
                    await db.delete(approval)

            ## cari semua log_penambahan_kerja karyawan ini yang masih menunggu_pm
            result_pending_kerja = await db.execute(
                select(LogPenambahanKerja.id_pengajuan_kerja).where(
                    LogPenambahanKerja.id_user == user_id,
                    LogPenambahanKerja.status == "menunggu_pm",
                )
            )
            pending_kerja_ids = [row[0] for row in result_pending_kerja.all()]

            ## hapus approval log_penambahan_kerja pm lama yang masih menunggu
            if pending_kerja_ids:
                result_approvals_kerja = await db.execute(
                    select(LogPenambahanKerjaApprovalPM).where(
                        LogPenambahanKerjaApprovalPM.id_pengajuan_kerja.in_(pending_kerja_ids),
                        LogPenambahanKerjaApprovalPM.id_pm == pm_id,
                        LogPenambahanKerjaApprovalPM.status == "menunggu",
                    )
                )
                for approval in result_approvals_kerja.scalars().all():
                    await db.delete(approval)

    ## handle pm_add, tambah user_pm dan reassign approval ke pm baru
    new_pm_ids = []
    if pm_add:
        for pm_id in pm_add:
            result_pm_user = await db.execute(select(User).where(User.id_user == pm_id, User.role == "pm"))
            pm_user = result_pm_user.scalar_one_or_none()
            if not pm_user:
                raise HTTPException(status_code=400, detail=f"User dengan ID {pm_id} tidak ditemukan atau bukan role PM!")

            result_existing = await db.execute(
                select(UserPM).where(UserPM.id_karyawan == user_id, UserPM.id_pm == pm_id)
            )
            if not result_existing.scalar_one_or_none():
                new_pm = UserPM(id_karyawan=user_id, id_pm=pm_id)
                db.add(new_pm)
                new_pm_ids.append(pm_id)

        ## buat approval record "menunggu" untuk setiap pm baru
        if new_pm_ids:
            ## ambil pending log_cuti yang masih menunggu_pm
            result_pending_logs = await db.execute(
                select(LogCuti.id_log_cuti).where(
                    LogCuti.id_user == user_id,
                    LogCuti.status == "menunggu_pm",
                )
            )
            pending_log_ids = [row[0] for row in result_pending_logs.all()]

            ## ambil pending log_penambahan_kerja yang masih menunggu_pm
            result_pending_kerja = await db.execute(
                select(LogPenambahanKerja.id_pengajuan_kerja).where(
                    LogPenambahanKerja.id_user == user_id,
                    LogPenambahanKerja.status == "menunggu_pm",
                )
            )
            pending_kerja_ids = [row[0] for row in result_pending_kerja.all()]

            for new_pm_id in new_pm_ids:
                ## ambil data pm baru untuk email notifikasi
                result_new_pm = await db.execute(select(User).where(User.id_user == new_pm_id))
                new_pm_user = result_new_pm.scalar_one_or_none()

                ## buat approval record log_cuti untuk pm baru
                for log_id in pending_log_ids:
                    ## skip jika pm sudah punya record apapun untuk log ini
                    result_existing = await db.execute(
                        select(LogCutiApprovalPM).where(
                            LogCutiApprovalPM.id_log_cuti == log_id,
                            LogCutiApprovalPM.id_pm == new_pm_id,
                        )
                    )
                    if result_existing.scalar_one_or_none():
                        continue

                    new_approval = LogCutiApprovalPM(
                        id_log_cuti=log_id,
                        id_pm=new_pm_id,
                        status="menunggu",
                    )
                    db.add(new_approval)

                    log_reassign = LogReassignmentApproval(
                        id_log_cuti=log_id,
                        id_pm_lama=None,
                        id_pm_baru=new_pm_id,
                        alasan="penambahan assignment PM",
                        waktu_perubahan=datetime.utcnow(),
                    )
                    db.add(log_reassign)

                    ## kirim email notifikasi ke pm baru
                    if new_pm_user and new_pm_user.email:
                        result_log = await db.execute(
                            select(LogCuti)
                            .options(selectinload(LogCuti.tanggal_list))
                            .where(LogCuti.id_log_cuti == log_id)
                        )
                        log_cuti = result_log.scalar_one_or_none()
                        if log_cuti:
                            background_tasks.add_task(
                                send_pengajuan_notification, user, new_pm_user, "cuti tahunan",
                                sorted([ld.tanggal for ld in log_cuti.tanggal_list]), log_cuti.keterangan_cuti,
                            )

                ## buat approval record log_penambahan_kerja untuk pm baru
                for kerja_id in pending_kerja_ids:
                    ## skip jika pm sudah punya record apapun untuk log ini
                    result_existing = await db.execute(
                        select(LogPenambahanKerjaApprovalPM).where(
                            LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == kerja_id,
                            LogPenambahanKerjaApprovalPM.id_pm == new_pm_id,
                        )
                    )
                    if result_existing.scalar_one_or_none():
                        continue

                    new_approval = LogPenambahanKerjaApprovalPM(
                        id_pengajuan_kerja=kerja_id,
                        id_pm=new_pm_id,
                        status="menunggu",
                    )
                    db.add(new_approval)

                    log_reassign = LogReassignmentApproval(
                        id_pengajuan_kerja=kerja_id,
                        id_pm_lama=None,
                        id_pm_baru=new_pm_id,
                        alasan="penambahan assignment PM",
                        waktu_perubahan=datetime.utcnow(),
                    )
                    db.add(log_reassign)

                    ## kirim email notifikasi ke pm baru
                    if new_pm_user and new_pm_user.email:
                        result_log_kerja = await db.execute(
                            select(LogPenambahanKerja)
                            .options(selectinload(LogPenambahanKerja.tanggal_list))
                            .where(LogPenambahanKerja.id_pengajuan_kerja == kerja_id)
                        )
                        log_kerja = result_log_kerja.scalar_one_or_none()
                        if log_kerja:
                            background_tasks.add_task(
                                send_pengajuan_notification, user, new_pm_user, "penambahan kerja",
                                sorted([ld.tanggal for ld in log_kerja.tanggal_list]), log_kerja.keterangan_pengajuan,
                            )

    ## set status final berdasarkan approval records
    result_all_logs = await db.execute(
        select(LogCuti.id_log_cuti).where(LogCuti.id_user == user_id)
    )
    all_log_ids = [row[0] for row in result_all_logs.all()]

    for log_id in all_log_ids:
        result_statuses = await db.execute(
            select(LogCutiApprovalPM.status).where(LogCutiApprovalPM.id_log_cuti == log_id)
        )
        all_statuses = [row[0] for row in result_statuses.all()]

        result_log = await db.execute(select(LogCuti).where(LogCuti.id_log_cuti == log_id))
        log_cuti = result_log.scalar_one_or_none()
        if not log_cuti:
            continue

        if not all_statuses:
            ## tidak ada approval records, butuh PM baru, tetap di menunggu_pm
            if log_cuti.status == "menunggu_hr":
                log_cuti.status = "menunggu_pm"
                db.add(log_cuti)
        elif any(s == "menunggu" for s in all_statuses):
            ## masih ada yang menunggu, status menunggu_pm
            if log_cuti.status != "menunggu_pm":
                log_cuti.status = "menunggu_pm"
                db.add(log_cuti)
        elif all(s == "disetujui" for s in all_statuses):
            ## semua sudah acc, status menunggu_hr
            if log_cuti.status != "menunggu_hr":
                log_cuti.status = "menunggu_hr"
                db.add(log_cuti)

    result_all_kerja = await db.execute(
        select(LogPenambahanKerja.id_pengajuan_kerja).where(LogPenambahanKerja.id_user == user_id)
    )
    all_kerja_ids = [row[0] for row in result_all_kerja.all()]

    for kerja_id in all_kerja_ids:
        result_statuses = await db.execute(
            select(LogPenambahanKerjaApprovalPM.status).where(
                LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == kerja_id
            )
        )
        all_statuses = [row[0] for row in result_statuses.all()]

        result_log = await db.execute(
            select(LogPenambahanKerja).where(LogPenambahanKerja.id_pengajuan_kerja == kerja_id)
        )
        log_kerja = result_log.scalar_one_or_none()
        if not log_kerja:
            continue

        if not all_statuses:
            if log_kerja.status == "menunggu_hr":
                log_kerja.status = "menunggu_pm"
                db.add(log_kerja)
        elif any(s == "menunggu" for s in all_statuses):
            if log_kerja.status != "menunggu_pm":
                log_kerja.status = "menunggu_pm"
                db.add(log_kerja)
        elif all(s == "disetujui" for s in all_statuses):
            if log_kerja.status != "menunggu_hr":
                log_kerja.status = "menunggu_hr"
                db.add(log_kerja)

    ## validasi karyawan non departemen 1 harus punya minimal 1 pm
    if user.role == "karyawan" and user.id_departemen != 1:
        result_pm_count = await db.execute(
            select(func.count(UserPM.id_user_pm)).where(UserPM.id_karyawan == user_id)
        )
        pm_count = result_pm_count.scalar_one() or 0
        if pm_count == 0:
            raise HTTPException(
                status_code=400,
                detail="Karyawan non-departemen 1 harus memiliki minimal 1 Project Manager",
            )

    await db.commit()

    return "Data karyawan berhasil diupdate!"


## log pengajuan kerja
async def get_log_penambahan_kerja(db: AsyncSession) -> list[HRLogPenambahanKerjaOut]:
    min_tgl = (
        select(LogPenambahanKerjaDate.id_pengajuan_kerja, func.min(LogPenambahanKerjaDate.tanggal).label("mulai"))
        .group_by(LogPenambahanKerjaDate.id_pengajuan_kerja)
        .subquery()
    )

    result = await db.execute(select(LogPenambahanKerja).options(
        selectinload(LogPenambahanKerja.user_log),
        selectinload(LogPenambahanKerja.tanggal_list),
        selectinload(LogPenambahanKerja.approval_pm_list).selectinload(LogPenambahanKerjaApprovalPM.pm)
    )
    .join(min_tgl, min_tgl.c.id_pengajuan_kerja == LogPenambahanKerja.id_pengajuan_kerja)
    .order_by(min_tgl.c.mulai.desc()))
    logs = result.scalars().unique().all()

    ## kumpulkan id prosesor hr & direktur untuk approved_by
    prosesor_ids = [log.diproses_hr for log in logs if log.diproses_hr]
    prosesor_ids += [log.diproses_direktur for log in logs if log.diproses_direktur]
    prosesor_users = {}
    if prosesor_ids:
        prosesor_result = await db.execute(select(User).where(User.id_user.in_(prosesor_ids)))
        prosesor_users = {u.id_user: u.nama for u in prosesor_result.scalars().all()}

    def get_approved_by(log: LogPenambahanKerja) -> str:
        id_prosesor = log.diproses_direktur if log.status in ("disetujui_direktur", "ditolak_direktur") else log.diproses_hr
        if id_prosesor and id_prosesor in prosesor_users:
            return prosesor_users[id_prosesor]
        rejected_pm = [a.pm.nama for a in log.approval_pm_list if a.status == "ditolak"]
        if rejected_pm:
            return rejected_pm[0]
        return "-"

    return [
        HRLogPenambahanKerjaOut(
            nama=log.user_log.nama,
            tanggal=sorted([ld.tanggal for ld in log.tanggal_list]),
            durasi=len(log.tanggal_list),
            keterangan=log.keterangan_pengajuan,
            tanggal_pengajuan=log.tanggal_pengajuan,
            status=log.status,
            pengganti="-",
            approved_by=get_approved_by(log)
        ) for log in logs
    ]


## rekapitulasi pengajuan kerja
async def get_rekapitulasi_penambahan_kerja(db: AsyncSession) -> list[HRRekapitulasiPenambahanKerjaOut]:
    result = await db.execute(
        select(User).options(selectinload(User.user_departemen)).where(
            User.role.in_(["karyawan", "pm", "hr_manager", "staff_hr"])
        ).order_by(User.nama.asc())
    )
    users = result.scalars().all()

    rekap = []
    for user in users:
        result_all = await db.execute(
            select(LogPenambahanKerja).where(LogPenambahanKerja.id_user == user.id_user).order_by(LogPenambahanKerja.tanggal_pengajuan.desc())
        )
        all_logs = result_all.scalars().all()

        total_pengajuan = len(all_logs)
        final_acc = ("disetujui_pm", "disetujui_hr", "disetujui_direktur")
        final_tolak = ("ditolak_pm", "ditolak_hr", "ditolak_direktur")
        disetujui = sum(1 for log in all_logs if log.status in final_acc)
        ditolak = sum(1 for log in all_logs if log.status in final_tolak)

        approved_by = "-"
        if all_logs:
            latest = all_logs[0]
            if latest.status in ("disetujui_hr", "ditolak_hr"):
                if latest.diproses_hr:
                    hr_user_result = await db.execute(select(User).where(User.id_user == latest.diproses_hr))
                    hr_user = hr_user_result.scalar_one_or_none()
                    approved_by = hr_user.nama if hr_user else "-"
            elif latest.status in ("disetujui_direktur", "ditolak_direktur"):
                if latest.diproses_direktur:
                    dir_user_result = await db.execute(select(User).where(User.id_user == latest.diproses_direktur))
                    dir_user = dir_user_result.scalar_one_or_none()
                    approved_by = dir_user.nama if dir_user else "-"
            elif latest.status == "ditolak_pm":
                result_approval = await db.execute(
                    select(LogPenambahanKerjaApprovalPM, User.nama).join(User, LogPenambahanKerjaApprovalPM.id_pm == User.id_user).where(
                        LogPenambahanKerjaApprovalPM.id_pengajuan_kerja == latest.id_pengajuan_kerja,
                        LogPenambahanKerjaApprovalPM.status == "ditolak"
                    )
                )
                row = result_approval.first()
                if row:
                    approved_by = row[1]

        rekap.append(HRRekapitulasiPenambahanKerjaOut(
            nama=user.nama,
            nama_departemen=user.user_departemen.nama_departemen,
            total_pengajuan=total_pengajuan,
            disetujui=disetujui,
            ditolak=ditolak,
            approved_by=approved_by,
        ))

    return rekap


## delete karyawan
async def delete_karyawan(user_id: int, current_user: User, db: AsyncSession) -> str:
    result = await db.execute(select(User).where(User.id_user == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan!")

    if user.id_user == current_user.id_user:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus diri sendiri!")

    ## cek PM terakhir untuk karyawan non-dept-1
    if user.role == "pm":
        result_karyawan_pm = await db.execute(
            select(UserPM.id_karyawan).where(UserPM.id_pm == user_id)
        )
        karyawan_ids = [row[0] for row in result_karyawan_pm.all()]
        for k_id in karyawan_ids:
            result_karyawan = await db.execute(select(User).where(User.id_user == k_id))
            karyawan = result_karyawan.scalar_one_or_none()
            if karyawan and karyawan.role == "karyawan" and karyawan.id_departemen != 1:
                result_pm_count = await db.execute(
                    select(func.count(UserPM.id_user_pm)).where(UserPM.id_karyawan == k_id)
                )
                pm_count = result_pm_count.scalar_one() or 0
                if pm_count <= 1:
                    raise HTTPException(
                        status_code=400,
                        detail="User ini adalah satu-satunya PM untuk beberapa karyawan, tidak bisa dihapus!",
                    )

    ## cek HR_manager terakhir
    if user.role == "hr_manager":
        result_hr_count = await db.execute(
            select(func.count(User.id_user)).where(User.role == "hr_manager")
        )
        hr_count = result_hr_count.scalar() or 0
        if hr_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Tidak bisa menghapus HR Manager terakhir!",
            )

    ## cek Direktur terakhir
    if user.role == "direktur":
        result_dir_count = await db.execute(
            select(func.count(User.id_user)).where(User.role == "direktur")
        )
        dir_count = result_dir_count.scalar() or 0
        if dir_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Tidak bisa menghapus Direktur terakhir!",
            )

    ## hapus log_cuti_approval_pm (pm sebagai approver)
    result_approval_pm = await db.execute(
        select(LogCutiApprovalPM).where(LogCutiApprovalPM.id_pm == user_id)
    )
    for approval in result_approval_pm.scalars().all():
        await db.delete(approval)

    ## hapus log_penambahan_kerja_approval_pm (pm sebagai approver)
    result_approval_kerja = await db.execute(
        select(LogPenambahanKerjaApprovalPM).where(LogPenambahanKerjaApprovalPM.id_pm == user_id)
    )
    for approval in result_approval_kerja.scalars().all():
        await db.delete(approval)

    ## hapus log_reassignment_approval
    result_reassign_lama = await db.execute(
        select(LogReassignmentApproval).where(LogReassignmentApproval.id_pm_lama == user_id)
    )
    for reassign in result_reassign_lama.scalars().all():
        await db.delete(reassign)

    result_reassign_baru = await db.execute(
        select(LogReassignmentApproval).where(LogReassignmentApproval.id_pm_baru == user_id)
    )
    for reassign in result_reassign_baru.scalars().all():
        await db.delete(reassign)

    ## hapus log_cuti_ekstra
    result_ekstra_user = await db.execute(
        select(LogCutiEkstra).where(LogCutiEkstra.id_user == user_id)
    )
    for ekstra in result_ekstra_user.scalars().all():
        await db.delete(ekstra)

    result_ekstra_penambah = await db.execute(
        select(LogCutiEkstra).where(LogCutiEkstra.id_penambah == user_id)
    )
    for ekstra in result_ekstra_penambah.scalars().all():
        await db.delete(ekstra)

    ## hapus log_cuti (akan cascade delete approval_pm via relationship)
    result_log_cuti = await db.execute(
        select(LogCuti).where(LogCuti.id_user == user_id)
    )
    for log in result_log_cuti.scalars().all():
        await db.delete(log)

    ## hapus log_penambahan_kerja
    result_log_kerja = await db.execute(
        select(LogPenambahanKerja).where(LogPenambahanKerja.id_user == user_id)
    )
    for log in result_log_kerja.scalars().all():
        await db.delete(log)

    ## hapus user_pm (karyawan dan pm)
    result_user_pm_karyawan = await db.execute(
        select(UserPM).where(UserPM.id_karyawan == user_id)
    )
    for upm in result_user_pm_karyawan.scalars().all():
        await db.delete(upm)

    result_user_pm_pm = await db.execute(
        select(UserPM).where(UserPM.id_pm == user_id)
    )
    for upm in result_user_pm_pm.scalars().all():
        await db.delete(upm)

    ## terakhir, hapus user
    await db.delete(user)
    await db.commit()

    return "User berhasil dihapus!"
