from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class LogCutiEkstraCreate(BaseModel):
    jumlah_hari: int
    keterangan: str

    @field_validator("jumlah_hari")
    @classmethod
    def jumlah_hari_tidak_boleh_nol(cls, v: int) -> int:
        if v == 0:
            raise ValueError("jumlah_hari tidak boleh 0")
        return v


class LogCutiEkstraOut(BaseModel):
    id_log_cuti_ekstra: int
    id_user: int
    id_penambah: int
    jumlah_hari: int
    keterangan: str
    added_at: date
    tahun: int

    model_config = {"from_attributes": True}
