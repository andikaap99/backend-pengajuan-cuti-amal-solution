from datetime import date, datetime, timedelta

from sqlalchemy import select

from app.models.holiday import Holiday
from app.models.log_cuti import LogCuti
from app.models.log_cuti_date import LogCutiDate
from app.services.auto_aktifkan_user_service import aktifkan_user_selesai_cuti
from app.services.cuti_service import hitung_cuti_terpakai
from app.services.export_excel_service import export_cuti_excel
from app.services.hr_service import get_list_cuti_karyawan_mendatang, get_log_penambahan_kerja, get_persetujuan
from app.services.holiday_quota_service import proses_cuti_hari_libur
from app.services.pm_service import get_dashboard_tim, get_history_cuti_tim, get_rekap_penambahan_kerja_detail

from conftest import add_log_cuti, add_log_kerja, assign_pm, future, make_user, seed_departemen


async def test_hr_persetujuan_statistik_bulanan(db):
    """disetujui_bulan_ini / ditolak_bulan_ini dihitung dari bulan tanggal MULAI (min tanggal)."""
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    today = date.today()

    ## log mulai bulan ini
    await add_log_cuti(db, karyawan, "disetujui_hr", future(1, 2))

    ## log lintas bulan: min tanggal = hari terakhir bulan lalu -> dihitung bulan lalu, bukan bulan ini
    prev_month_last = (today.replace(day=1) - timedelta(days=1))
    cur_month_first = today.replace(day=1)
    if prev_month_last != cur_month_first:
        await add_log_cuti(db, karyawan, "disetujui_hr", [prev_month_last, cur_month_first])

    ## ditolak bulan ini
    await add_log_cuti(db, karyawan, "ditolak_hr", future(3))

    result = await get_persetujuan(db, "hr_manager")

    ## yang mulai bulan ini: 1 disetujui (yang lintas bulan dihitung bulan lalu)
    assert result.disetujui_bulan_ini == 1
    assert result.ditolak_bulan_ini == 1


async def test_hr_list_cuti_mendatang_filter(db):
    """filter lama tanggal_mulai >= today -> kini min(tanggal) >= today."""
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    ## cuti murni mendatang -> masuk
    await add_log_cuti(db, karyawan, "disetujui_hr", future(5, 6))
    ## cuti yang mulai kemarin (masih jalan) -> TIDAK masuk (semantik sama dengan kode lama)
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    await add_log_cuti(db, karyawan, "disetujui_hr", [yesterday, today, future(1)[0]])
    ## status belum final -> tidak masuk
    await add_log_cuti(db, karyawan, "menunggu_hr", future(9))

    rows = await get_list_cuti_karyawan_mendatang(db)
    assert len(rows) == 1
    assert rows[0].tanggal == future(5, 6)
    assert "tanggal_mulai" not in type(rows[0]).model_fields


async def test_auto_aktifkan_user(db):
    await seed_departemen(db)
    aktifkan = await make_user(db, "karyawan1", "karyawan", status="Cuti")
    selesai = await make_user(db, "karyawan2", "karyawan", status="Cuti")
    sedang = await make_user(db, "karyawan3", "karyawan", status="Cuti")
    await db.commit()

    ## karyawan1: tanpa log hari ini -> kembali Aktif
    ## karyawan2: log kemarin -> kembali Aktif
    yesterday = date.today() - timedelta(days=1)
    await add_log_cuti(db, aktifkan, "disetujui_hr", [date.today() - timedelta(days=5)])
    await add_log_cuti(db, selesai, "disetujui_hr", [yesterday])
    ## karyawan3: log mencakup hari ini -> tetap Cuti
    await add_log_cuti(db, sedang, "disetujui_hr", future(-1, 0, 1))

    count = await aktifkan_user_selesai_cuti(db)
    assert count == 2

    from app.models.user import User
    statuses = {
        u.username: u.status
        for u in (await db.execute(select(User))).scalars()
    }
    assert statuses["karyawan1"] == "Aktif"
    assert statuses["karyawan2"] == "Aktif"
    assert statuses["karyawan3"] == "Cuti"


async def test_export_excel_berjalan(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()
    await add_log_cuti(db, karyawan, "disetujui_hr", future(1, 2, 3))

    content = await export_cuti_excel(date.today().year, db)
    assert isinstance(content, bytes) and len(content) > 0


async def test_holiday_quota_potong_sisa_dan_buat_tanggal(db):
    """job cuti bersama: potong sisa, buat log+dates; eksklusi semua role dengan kerja final di window libur."""
    await seed_departemen(db)

    normal = await make_user(db, "karyawan1", "karyawan", id_departemen=2, sisa_cuti=12)
    dept3_biasa = await make_user(db, "karyawan4", "karyawan", id_departemen=3, sisa_cuti=12)
    ## kerja final per role -> tidak dipotong
    pm_kerja = await make_user(db, "pm1", "pm", id_departemen=2, sisa_cuti=12)
    hr_dir = await make_user(db, "hrmgr1", "hr_manager", id_departemen=1, sisa_cuti=12)
    staff_kerja = await make_user(db, "staff1", "staff_hr", id_departemen=1, sisa_cuti=12)
    dept3_final = await make_user(db, "karyawan3", "karyawan", id_departemen=3, sisa_cuti=12)
    ## kerja belum final -> tetap dipotong
    belum_final = await make_user(db, "karyawan5", "karyawan", id_departemen=3, sisa_cuti=12)
    await db.commit()

    holiday_day = date.today() - timedelta(days=1)  ## <= today supaya langsung diproses
    db.add(Holiday(nama_libur="Cuti Bersama Tes", tanggal=holiday_day, is_cuti_bersama=True, tahun=holiday_day.year, sudah_dikurangi=False))
    ## final flow jalur HR: disetujui_hr
    await add_log_kerja(db, pm_kerja, "disetujui_hr", [holiday_day])
    await add_log_kerja(db, staff_kerja, "disetujui_hr", [holiday_day])
    ## final flow jalur direktur: disetujui_direktur (hr_manager)
    await add_log_kerja(db, hr_dir, "disetujui_direktur", [holiday_day])
    ## final flow lama: disetujui_pm tetap dianggap final
    await add_log_kerja(db, dept3_final, "disetujui_pm", [holiday_day])
    ## belum acc tahap akhir
    await add_log_kerja(db, belum_final, "menunggu_hr", [holiday_day])

    processed = await proses_cuti_hari_libur(db)
    assert processed == 1

    await db.refresh(normal)
    await db.refresh(dept3_biasa)
    await db.refresh(pm_kerja)
    await db.refresh(hr_dir)
    await db.refresh(staff_kerja)
    await db.refresh(dept3_final)
    await db.refresh(belum_final)

    assert normal.sisa_cuti == 11
    assert dept3_biasa.sisa_cuti == 11
    ## yang belum final tetap dipotong
    assert belum_final.sisa_cuti == 11
    ## semua role dengan kerja final tidak dipotong
    assert pm_kerja.sisa_cuti == 12
    assert hr_dir.sisa_cuti == 12
    assert staff_kerja.sisa_cuti == 12
    assert dept3_final.sisa_cuti == 12

    ## yang eksklusi tidak dapat log cuti bersama
    for u in (pm_kerja, hr_dir, staff_kerja, dept3_final):
        logs_excl = (await db.execute(
            select(LogCuti).where(LogCuti.id_user == u.id_user)
        )).scalars().all()
        assert logs_excl == []

    ## log cuti bersama punya baris tanggal & terhitung terpakai
    assert await hitung_cuti_terpakai(normal.id_user, db) == 1
    logs = (await db.execute(
        select(LogCuti).where(LogCuti.id_user == normal.id_user)
    )).scalars().all()
    assert len(logs) == 1
    dates = (await db.execute(
        select(LogCutiDate).where(LogCutiDate.id_log_cuti == logs[0].id_log_cuti)
    )).scalars().all()
    assert [d.tanggal for d in dates] == [holiday_day]


async def test_pm_dashboard_dan_history_order(db):
    await seed_departemen(db)
    pm = await make_user(db, "pm1", "pm")
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await assign_pm(db, karyawan, pm)
    await db.commit()

    ## dua log menunggu_pm dengan tanggal berbeda untuk cek urutan
    later = future(20, 21)
    sooner = future(10, 11)
    await add_log_cuti(db, karyawan, "menunggu_pm", later)
    await add_log_cuti(db, karyawan, "menunggu_pm", sooner)

    dashboard = await get_dashboard_tim(pm.id_user, db)
    assert len(dashboard) == 2
    ## urut dari tanggal mulai (min) terkecil
    assert dashboard[0].tanggal == sorted(sooner)
    assert dashboard[1].tanggal == sorted(later)
    assert "tanggal_mulai" not in type(dashboard[0]).model_fields

    ## history disetujui_hr
    await add_log_cuti(db, karyawan, "disetujui_hr", future(1, 2))
    history = await get_history_cuti_tim(pm.id_user, db)
    assert len(history) == 1
    assert history[0].tanggal == future(1, 2)
    assert history[0].durasi == 2


async def test_pm_sedang_kerja_hari_ini(db):
    await seed_departemen(db)
    pm = await make_user(db, "pm1", "pm")
    karyawan = await make_user(db, "karyawan1", "karyawan", id_departemen=2)
    await assign_pm(db, karyawan, pm)
    await db.commit()

    ## kerja disetujui yang mencakup hari ini
    await add_log_kerja(db, karyawan, "disetujui_hr", future(-1, 0, 1))

    detail = await get_rekap_penambahan_kerja_detail(pm.id_user, db)
    assert len(detail) == 1
    item = detail[0]
    assert item.status == "Sedang Kerja"
    assert item.tanggal_kerja[0].tanggal == future(-1, 0, 1)


async def test_hr_log_pakai_list(db):
    await seed_departemen(db)
    karyawan = await make_user(db, "karyawan1", "karyawan")
    await db.commit()

    dates = future(2, 4, 5)
    await add_log_cuti(db, karyawan, "disetujui_hr", dates)
    await add_log_kerja(db, karyawan, "disetujui_hr", future(7, 8))

    from app.services.hr_service import get_cuti_log
    logs = await get_cuti_log(db)
    assert len(logs) == 1
    assert logs[0].tanggal == sorted(dates)
    assert logs[0].durasi == 3
    assert "tanggal_mulai" not in type(logs[0]).model_fields

    kerja_rows = await get_log_penambahan_kerja(db)
    assert len(kerja_rows) == 1
    assert kerja_rows[0].tanggal == future(7, 8)
    assert kerja_rows[0].durasi == 2
    assert "tanggal_mulai" not in type(kerja_rows[0]).model_fields
