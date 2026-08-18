from datetime import date
from typing import Optional

from pydantic import BaseModel


class HolidayOut(BaseModel):
    id_holiday: int
    nama_libur: str
    tanggal: date
    is_cuti_bersama: bool
    tahun: int

    model_config = {"from_attributes": True}


class NextCutiBersamaOut(BaseModel):
    nama_libur: str
    tanggal_mulai: date
    tanggal_selesai: date
    total_hari: int

    model_config = {"from_attributes": True}
