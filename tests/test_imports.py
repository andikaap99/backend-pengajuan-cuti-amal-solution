## semua router & service harus bisa diimport tanpa error
## (deteksi referensi kolom/field yang terlewat setelah drop tanggal_mulai/selesai)


def test_import_app_and_routers():
    from app.main import app  # noqa: F401
    from app.routers import approval, auth, department, direktur, holiday, hr, karyawan, pm, role  # noqa: F401


def test_import_services():
    from app.services import (  # noqa: F401
        approval_service,
        auto_aktifkan_user_service,
        cuti_service,
        email_service,
        export_excel_service,
        holiday_quota_service,
        hr_service,
        penambahan_kerja_service,
        pm_service,
    )


def test_schemas_tidak_punya_range_lagi():
    from app.schemas.hr import HRListCutiKaryawanMendatangOut, HRLogCutiOut, HRLogPenambahanKerjaOut
    from app.schemas.log_cuti import EmpDashboardPengajuanOngoingOut, PengajuanCutiOut, RiwayatCutiOut
    from app.schemas.pengajuan import PersetujuanQueueCutiOut
    from app.schemas.penambahan_kerja import PenambahanKerjaCreate, PenambahanKerjaOut, PenambahanKerjaQueueOut
    from app.schemas.pm import PMDashboardTimOut, PMHistoryPersetujuanOut, TanggalKerjaItem

    for schema in (
        PengajuanCutiOut,
        RiwayatCutiOut,
        EmpDashboardPengajuanOngoingOut,
        PersetujuanQueueCutiOut,
        PenambahanKerjaCreate,
        PenambahanKerjaOut,
        PenambahanKerjaQueueOut,
        PMDashboardTimOut,
        PMHistoryPersetujuanOut,
        TanggalKerjaItem,
        HRListCutiKaryawanMendatangOut,
        HRLogCutiOut,
        HRLogPenambahanKerjaOut,
    ):
        fields = schema.model_fields
        assert "tanggal_mulai" not in fields, schema.__name__
        assert "tanggal_selesai" not in fields, schema.__name__


def test_models_tidak_punya_kolom_range():
    from app.models.log_cuti import LogCuti
    from app.models.log_penambahan_kerja import LogPenambahanKerja

    assert "tanggal_mulai" not in LogCuti.__table__.columns
    assert "tanggal_selesai" not in LogCuti.__table__.columns
    assert "tanggal_mulai" not in LogPenambahanKerja.__table__.columns
    assert "tanggal_selesai" not in LogPenambahanKerja.__table__.columns
    assert "tanggal_list" in LogPenambahanKerja.__mapper__.relationships
