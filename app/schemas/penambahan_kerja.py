from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class PenambahanKerjaCreate(BaseModel):
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan: str


class PenambahanKerjaOut(BaseModel):
    id_pengajuan_kerja: int
    id_user: int
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan_pengajuan: str
    status: Literal["menunggu_pm", "disetujui_pm", "ditolak_pm"]
    diproses_pm: Optional[int] = None
    processed_at_pm: Optional[date] = None

    model_config = {"from_attributes": True}


class PenambahanKerjaQueueOut(BaseModel):
    id_pengajuan_kerja: int
    nama: str
    nama_departemen: str
    tanggal_mulai: date
    tanggal_selesai: date
    keterangan: str


class PenambahanKerjaApprovalRequest(BaseModel):
    action: Literal["acc", "decline"]
    alasan: Optional[str] = None


class PenambahanKerjaApprovalResponse(BaseModel):
    detail: str
    status_baru: str
