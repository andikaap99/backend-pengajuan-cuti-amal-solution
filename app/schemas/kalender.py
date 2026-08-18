from datetime import date
from typing import Optional

from pydantic import BaseModel



class CutiSayaOut(BaseModel):
    tanggal: date
    nama: str
    keterangan: str
    jenis_cuti: str
    status: str

    model_config = {"from_attributes": True}