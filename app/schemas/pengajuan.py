from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.log_cuti import ApprovalPMDetail


## card queue
class PersetujuanQueueCutiOut(BaseModel):
    id_log_cuti: int
    nama: str
    nama_departemen: str
    jenis_cuti: str
    tanggal: list[date] = []
    durasi: int
    pengganti: str
    sisa_cuti: int
    alasan: str
    tanggal_pengajuan: datetime
    approval_pm_detail: list[ApprovalPMDetail] = []