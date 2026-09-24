from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class PenambahanKerjaCreate(BaseModel):
    tanggal: list[date]
    keterangan: str


class PenambahanKerjaApprovalPMDetail(BaseModel):
    nama_pm: str
    status: str
    processed_at: Optional[datetime] = None


class PenambahanKerjaOut(BaseModel):
    id_pengajuan_kerja: int
    id_user: int
    tanggal: list[date] = []
    keterangan_pengajuan: str
    status: Literal["menunggu_pm", "disetujui_pm", "ditolak_pm", "menunggu_hr", "disetujui_hr", "ditolak_hr", "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"]
    tanggal_pengajuan: Optional[datetime] = None
    approval_pm_detail: list[PenambahanKerjaApprovalPMDetail] = []

    model_config = {"from_attributes": True}


class PenambahanKerjaQueueOut(BaseModel):
    id_pengajuan_kerja: int
    nama: str
    nama_departemen: str
    tanggal: list[date] = []
    keterangan: str
    tanggal_pengajuan: Optional[datetime] = None
    status: str
    approval_pm_detail: list[PenambahanKerjaApprovalPMDetail] = []


class PenambahanKerjaApprovalRequest(BaseModel):
    action: Literal["acc", "decline"]
    alasan: Optional[str] = None


class PenambahanKerjaApprovalResponse(BaseModel):
    detail: str
    status_baru: str
