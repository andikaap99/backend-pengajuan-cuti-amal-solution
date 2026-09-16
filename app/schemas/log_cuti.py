from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel


class PengajuanCutiBase(BaseModel):
    tanggal_mulai: date
    tanggal_selesai: date
    pengganti: Optional[int] = None
    keterangan_cuti: str


class PengajuanCutiCreate(PengajuanCutiBase):
    pass


class ApprovalPMDetail(BaseModel):
    nama_pm: str
    status: Literal["menunggu", "disetujui", "ditolak"]
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PengajuanCutiOut(PengajuanCutiBase):
    id_log_cuti: int
    id_user: int
    jenis_cuti: str
    status: Literal[
            "menunggu_pm", "disetujui_pm", "ditolak_pm",
            "menunggu_hr", "disetujui_hr", "ditolak_hr",
            "menunggu_direktur", "disetujui_direktur", "ditolak_direktur",
            "cuti_bersama"
        ]
    alasan_penolakan: Optional[str] = None
    diproses_hr: Optional[int] = None
    diproses_direktur: Optional[int] = None
    processed_at_hr: Optional[datetime] = None
    processed_at_direktur: Optional[datetime] = None
    edited_at: Optional[datetime] = None
    tanggal_pengajuan: Optional[datetime] = None
    approval_pm_detail: list[ApprovalPMDetail] = []

    model_config = {"from_attributes": True}


class RiwayatCutiOut(BaseModel):
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan_cuti: str
    nama_pengganti: str
    durasi: int
    tanggal_pengajuan: Optional[datetime] = None
    status: Literal[
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur",
        "cuti_bersama"
    ]
    approval_pm_detail: list[ApprovalPMDetail] = []
    approved_by_hr: Optional[str] = None
    approved_at_hr: Optional[datetime] = None
    approved_by_direktur: Optional[str] = None
    approved_at_direktur: Optional[datetime] = None


class EmpDashboardPengajuanOngoingOut(BaseModel):
    jenis_cuti: str
    durasi: int
    keterangan_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    tanggal_pengajuan: Optional[datetime] = None
    status_sekarang: Literal[
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
    ]
    approved_by_hr: Optional[str] = None
    approved_at_hr: Optional[datetime] = None
    approved_by_direktur: Optional[str] = None
    approved_at_direktur: Optional[datetime] = None
    alasan_penolakan: Optional[str] = None
    id_pengganti: Optional[int] = None
    approval_pm_detail: list[ApprovalPMDetail] = []


class EmpDashboardRingkasanOut(BaseModel):
    periode_tahun: int
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int


class PengajuanCutiUpdate(BaseModel):
    tanggal_mulai: Optional[date] = None
    tanggal_selesai: Optional[date] = None
    pengganti: Optional[int] = None
    keterangan_cuti: Optional[str] = None

