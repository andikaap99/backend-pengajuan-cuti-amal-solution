from datetime import date
from typing import Optional

from pydantic import BaseModel


class LogCutiEkstraCreate(BaseModel):
    id_user: int
    jumlah_hari: int = 1
    keterangan: str


class LogCutiEkstraOut(BaseModel):
    id_log_cuti_ekstra: int
    id_user: int
    id_penambah: int
    jumlah_hari: int
    keterangan: str
    added_at: date
    tahun: int

    model_config = {"from_attributes": True}
