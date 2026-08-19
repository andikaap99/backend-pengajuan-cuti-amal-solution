from datetime import date
from typing import Optional

from pydantic import BaseModel


## dashboard
## ringkasan
class PMDashboardRingkasanOut(BaseModel):
    sisa_cuti: int
    cuti_terpakai: int
    tim_menunggu_appoval: int
    total_pengajuan_tim: int
    total_pengajuan_acc_tim: int
    total_pengajuan_decline_tim: int

## cuti tim
class PMDashboardTimOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    status: str


## pesetujuan
##

##


## history
class PMHistoryPersetujuanOut(BaseModel):
    tanggal_mulai: date
    tanggal_selesai: date
    nama: str
    jenis_cuti: str
    keterangan: str
    durasi: int
    pengganti: str
    status: str


class PMPersetujuanRingkasanTimOut(BaseModel):
    tahun: int
    total_pengajuan: int
    menunggu_persetujuan: int
    sedang_cuti: int

class PMPersetujuanQueueCutiOut(BaseModel):
    nama: str
    nama_departemen: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    durasi: int
    pengganti: str
    sisa_cuti: int
    alasan: str



class PMRekapCutiRingkasanOut(BaseModel):
    total_anggota_aktif: int
    total_cuti_all: int

class PMRekapCutiDetailJatah(BaseModel):
    nama: str
    nama_departemen: str
    penggunaan_cuti: int
    sisa_cuti: int
    status: str