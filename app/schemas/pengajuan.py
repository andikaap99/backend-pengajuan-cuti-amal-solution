from datetime import date
from typing import Optional

from pydantic import BaseModel


## card queue
class PersetujuanQueueCutiOut(BaseModel):
    nama: str
    nama_departemen: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    durasi: int
    pengganti: str
    sisa_cuti: int
    alasan: str