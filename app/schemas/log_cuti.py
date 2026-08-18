from datetime import date
from typing import Optional, Literal

from pydantic import BaseModel


class PengajuanCutiBase(BaseModel):
    tanggal_mulai: date
    tanggal_selesai: date
    pengganti: Optional[int] = None
    keterangan_cuti: str


class PengajuanCutiCreate(PengajuanCutiBase):
    pass


class PengajuanCutiOut(PengajuanCutiBase):
    id_log_cuti: int
    id_user: int
    jenis_cuti: str
    status: Literal[
            "menunggu_pm", "disetujui_pm", "ditolak_pm",
            "menunggu_hr", "disetujui_hr", "ditolak_hr",
            "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
        ]
    alasan_penolakan: Optional[str] = None
    disetujui_pm: Optional[int] = None
    disetujui_hr: Optional[int] = None
    disetujui_direktur: Optional[int] = None
    approved_at_pm: Optional[date] = None
    approved_at_hr: Optional[date] = None
    approved_at_direktur: Optional[date] = None

    model_config = {"from_attributes": True}


class RiwayatCutiOut(BaseModel):
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan_cuti: str
    nama_pengganti: str
    durasi: int
    status: Literal[
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
    ]


class EmpDashboardPengajuanOngoingOut(BaseModel):
    jenis_cuti: str
    durasi: int
    keterangan_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    status_sekarang: Literal[
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
    ]
    disetujui_pm: Optional[int] = None
    disetujui_hr: Optional[int] = None
    disetujui_direktur: Optional[int] = None
    approved_at_pm: Optional[date] = None
    approved_at_hr: Optional[date] = None
    approved_at_direktur: Optional[date] = None
    alasan_penolakan: Optional[str] = None


class EmpDashboardRingkasanOut(BaseModel):
    periode_tahun: int
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int

# class LogCutiUpdateStatus(BaseModel):
#     status: str
#     alasan_penolakan: Optional[str] = None

