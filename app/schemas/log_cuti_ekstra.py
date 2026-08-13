from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class LogCutiEkstraBase(BaseModel):
    id_direktur: int
    jumlah_hari: int = 1
    keterangan: str


class LogCutiEkstraOut(BaseModel):
    id_log_cuti_ekstra: int
    id_direktur: int
    jumlah_hari: int
    keterangan: str
    created_at: datetime

    model_config = {"from_attributes": True}
