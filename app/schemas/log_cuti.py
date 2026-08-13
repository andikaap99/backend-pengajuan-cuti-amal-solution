from datetime import date
from typing import Optional

from pydantic import BaseModel


class LogCutiBase(BaseModel):
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan: str


class LogCutiCreate(LogCutiBase):
    pass


class LogCutiUpdateStatus(BaseModel):
    status: str
    alasan_penolakan: Optional[str] = None


class LogCutiOut(BaseModel):
    id_log_cuti: int
    id_user: int
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan: str
    status: str
    alasan_penolakan: Optional[str] = None
    disetujui_pm: Optional[int] = None
    disetujui_hr: Optional[int] = None
    disetujui_direktur: Optional[int] = None
    approved_at_pm: Optional[date] = None
    approved_at_hr: Optional[date] = None
    approved_at_direktur: Optional[date] = None

    model_config = {"from_attributes": True}
