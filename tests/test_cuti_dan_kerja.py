from datetime import date, datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.models.log_cuti_date import LogCutiDate
from app.schemas.log_cuti import PengajuanCutiCreate
from app.services.approval_service import get_queue_card
from app.services.cuti_service import create_pengajuan_cuti, get_my_cuti, get_my_ongoing_cuti, hitung_cuti_terpakai
from app.services.export_excel_service import get_approved_logs_for_year
from app.services.penambahan_kerja_service import (
    create_penambahan_kerja,
    get_my_penambahan_kerja,
    get_penambahan_kerja_queue,
    get_penambahan_kerja_queue_hr,
)

from conftest import add_log_cuti, assign_pm, future, make_user, seed_departemen


async def test_create_cuti_pakai_list_tanggal(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await db.commit()

    dates = future(10, 11, 13)
    data = PengajuanCutiCreate(tanggal=dates, pengganti=None, keterangan_cuti="libur")
    result = await create_pengajuan_cuti(data, karyawan.id_user, db, BackgroundTasks())

    assert result.tanggal == sorted(dates)
    assert result.durasi == 3
    assert not hasattr(result, "tanggal_mulai")

    ## pastikan baris tanggal tersimpan
    rows = (
        await db.execute(select(LogCutiDate).where(LogCutiDate.id_log_cuti == result.id_log_cuti))
    ).scalars().all()
    assert sorted(r.tanggal for r in rows) == sorted(dates)


async def test_riwayat_dan_ongoing_pakai_list(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await db.commit()

    dates = future(1, 2)
    await add_log_cuti(db, karyawan, "disetujui_hr", dates)

    riwayat = await get_my_cuti(karyawan.id_user, db, karyawan)
    assert len(riwayat) == 1
    assert riwayat[0].tanggal == sorted(dates)
    assert riwayat[0].durasi == 2
    assert "tanggal_mulai" not in type(riwayat[0]).model_fields

    ongoing = await get_my_ongoing_cuti(karyawan.id_user, db)
    assert ongoing[0].tanggal == sorted(dates)
    assert ongoing[0].durasi == 2


async def test_hitung_cuti_terpakai_dari_tabel_tanggal(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    await add_log_cuti(db, karyawan, "disetujui_hr", future(1, 2, 3))
    await add_log_cuti(db, karyawan, "menunggu_hr", future(5))

    terpakai = await hitung_cuti_terpakai(karyawan.id_user, db)
    assert terpakai == 3


async def test_approval_queue_pakai_list_plus_detail_pm(db):
    await seed_departemen(db)
    pm = await make_user(db, "pm1", "pm")
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await assign_pm(db, karyawan, pm)
    await db.commit()

    dates = future(7, 8)
    data = PengajuanCutiCreate(tanggal=dates, pengganti=None, keterangan_cuti="cuti")
    await create_pengajuan_cuti(data, karyawan.id_user, db, BackgroundTasks())
    await db.commit()

    queue = await get_queue_card(pm, db)
    assert len(queue) == 1
    card = queue[0]
    assert card.tanggal == sorted(dates)
    assert card.durasi == 2
    assert "tanggal_mulai" not in type(card).model_fields
    ## ada tahap PM karena karyawan dept != 1
    assert len(card.approval_pm_detail) == 1
    assert card.approval_pm_detail[0].status == "menunggu"


async def test_export_year_filter_pakai_tanggal_min(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    ## log mulai 31 Des tahun lama, selesai 1 Jan tahun ini -> dihitung di tahun lama
    this_year = date.today().year
    spanning = [date(this_year - 1, 12, 31), date(this_year, 1, 1)]
    await add_log_cuti(db, karyawan, "disetujui_hr", spanning)
    ## log murni tahun ini
    await add_log_cuti(db, karyawan, "disetujui_hr", future(10, 11))

    logs_old_year = await get_approved_logs_for_year(karyawan.id_user, this_year - 1, db)
    logs_new_year = await get_approved_logs_for_year(karyawan.id_user, this_year, db)

    assert len(logs_old_year) == 1
    assert len(logs_new_year) == 1
    old_dates = sorted(ld.tanggal for ld in logs_old_year[0].tanggal_list)
    assert old_dates == sorted(spanning)


async def test_penambahan_kerja_pakai_list_tanggal(db):
    await seed_departemen(db)
    pm = await make_user(db, "pm1", "pm")
    hr = await make_user(db, "hr1", "staff_hr")
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await assign_pm(db, karyawan, pm)
    await db.commit()

    dates = future(20, 22, 23)  ## non-kontigu, seperti cuti
    result = await create_penambahan_kerja(
        karyawan.id_user, dates, "lembur", db, BackgroundTasks()
    )
    assert result.tanggal == sorted(dates)
    assert "tanggal_mulai" not in type(result).model_fields

    ## GET terbaru mengembalikan list yang sama
    my = await get_my_penambahan_kerja(karyawan.id_user, db)
    assert my[0].tanggal == sorted(dates)

    ## queue PM memakai list tanggal
    queue = await get_penambahan_kerja_queue(pm.id_user, db)
    assert len(queue) == 1
    assert queue[0].tanggal == sorted(dates)

    ## queue HR: setelah semua PM acc status jadi menunggu_hr
    from app.services.penambahan_kerja_service import process_penambahan_kerja
    await process_penambahan_kerja(result.id_pengajuan_kerja, pm.id_user, "acc", None, db, BackgroundTasks())
    hr_queue = await get_penambahan_kerja_queue_hr(db, hr.id_user)
    assert len(hr_queue) == 1
    assert hr_queue[0].tanggal == sorted(dates)


async def test_penambahan_kerja_flow_sama_cuti(db):
    """flow & final status penambahan kerja identik cuti:
    staff_hr selesai di HR (disetujui_hr), hr_manager lewat direktur (disetujui_direktur),
    self-approval ditolak, queue HR kecuali pengajuan sendiri."""
    import pytest
    from fastapi import HTTPException

    from app.models.log_penambahan_kerja import LogPenambahanKerja
    from app.services.penambahan_kerja_service import (
        process_penambahan_kerja_direktur,
        process_penambahan_kerja_hr,
    )

    await seed_departemen(db)
    staff1 = await make_user(db, "staff1", "staff_hr")
    staff2 = await make_user(db, "staff2", "staff_hr")
    hr_mgr = await make_user(db, "hrmgr1", "hr_manager")
    direktur = await make_user(db, "dir1", "direktur")
    await db.commit()

    ## staff_hr submit -> langsung menunggu_hr (tanpa tahap PM)
    r1 = await create_penambahan_kerja(staff1.id_user, future(10), "kerja staff", db, BackgroundTasks())
    assert r1.status == "menunggu_hr"

    ## queue HR: tampil untuk HR lain, tidak untuk diri sendiri
    q_lain = await get_penambahan_kerja_queue_hr(db, staff2.id_user)
    assert len(q_lain) == 1
    q_diri = await get_penambahan_kerja_queue_hr(db, staff1.id_user)
    assert len(q_diri) == 0

    ## self-approval ditolak
    with pytest.raises(HTTPException) as exc_self:
        await process_penambahan_kerja_hr(r1.id_pengajuan_kerja, staff1, "acc", None, db, BackgroundTasks())
    assert exc_self.value.status_code == 400

    ## HR lain acc -> FINAL disetujui_hr (tidak naik ke direktur)
    resp1 = await process_penambahan_kerja_hr(r1.id_pengajuan_kerja, staff2, "acc", None, db, BackgroundTasks())
    assert resp1.status_baru == "disetujui_hr"

    ## hr_manager submit -> lewat direktur
    r2 = await create_penambahan_kerja(hr_mgr.id_user, future(20), "kerja hrmgr", db, BackgroundTasks())
    assert r2.status == "menunggu_direktur"

    ## direktur acc -> FINAL disetujui_direktur + kolom direktur terisi
    resp2 = await process_penambahan_kerja_direktur(r2.id_pengajuan_kerja, direktur, "acc", None, db, BackgroundTasks())
    assert resp2.status_baru == "disetujui_direktur"

    log2 = (await db.execute(
        select(LogPenambahanKerja).where(LogPenambahanKerja.id_pengajuan_kerja == r2.id_pengajuan_kerja)
    )).scalar_one()
    assert log2.diproses_direktur == direktur.id_user
    assert log2.processed_at_direktur is not None
    assert log2.diproses_hr is None
    assert log2.diproses_hr is None


async def test_penambahan_kerja_overlap_per_tanggal(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await db.commit()

    dates = future(30, 31, 32)
    await create_penambahan_kerja(karyawan.id_user, dates, "pertama", db, BackgroundTasks())

    ## status masih menunggu -> diajukan lagi harus ditolak (single in-flight)
    import pytest
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        await create_penambahan_kerja(karyawan.id_user, future(40), "kedua", db, BackgroundTasks())

    ## setelah ditolak, tanggal yang sama boleh diajukan ulang (rejected tidak menutup tanggal)
    from app.models.log_penambahan_kerja import LogPenambahanKerja
    kerja = (
        await db.execute(select(LogPenambahanKerja))
    ).scalars().first()
    kerja.status = "ditolak_hr"
    db.add(kerja)
    await db.commit()

    ulang = await create_penambahan_kerja(
        karyawan.id_user,
        [dates[0], future(50)[0]],
        "setelah ditolak",
        db,
        BackgroundTasks(),
    )
    assert ulang.tanggal == sorted([dates[0], future(50)[0]])

    ## setelah disetujui, satu tanggal yang sama harus overlap
    log_baru = (
        await db.execute(select(LogPenambahanKerja).where(LogPenambahanKerja.id_pengajuan_kerja == ulang.id_pengajuan_kerja))
    ).scalars().first()
    log_baru.status = "disetujui_hr"
    db.add(log_baru)
    await db.commit()

    with pytest.raises(HTTPException) as exc:
        await create_penambahan_kerja(
            karyawan.id_user,
            [dates[0], future(60)[0]],
            "overlap",
            db,
            BackgroundTasks(),
        )
    assert "sudah ada" in exc.value.detail


async def test_cuti_bersama_terhitung_terpakai(db):
    ## cuti bersama yang dibuat job malam kini ikut punya baris tanggal
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    d = future(3)[0]
    await add_log_cuti(db, karyawan, "disetujui_hr", [d], jenis="cuti bersama")

    assert await hitung_cuti_terpakai(karyawan.id_user, db) == 1
