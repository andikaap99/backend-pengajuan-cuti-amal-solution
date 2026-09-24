from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


## dashboard
## ringkasan
class PMDashboardRingkasanOut(BaseModel):
    sisa_cuti: int
    jatah_cuti: int
    cuti_terpakai: int
    total_anggota_tim: int
    tim_menunggu_appoval: int
    total_pengajuan_tim: int
    total_pengajuan_acc_tim: int
    total_pengajuan_decline_tim: int

## cuti tim
class PMDashboardTimOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal: list[date] = []
    tanggal_pengajuan: datetime
    status: str


## pesetujuan
## ringkasan
class PMPersetujuanRingkasanTimOut(BaseModel):
    tahun: int
    total_pengajuan: int
    menunggu_persetujuan: int
    sedang_cuti: int

## history
class PMHistoryPersetujuanOut(BaseModel):
    tanggal: list[date] = []
    nama: str
    jenis_cuti: str
    keterangan: str
    durasi: int
    pengganti: str
    tanggal_pengajuan: datetime
    status: str


## rekap cuti
## ringkasan
class PMRekapCutiRingkasanOut(BaseModel):
    total_anggota_aktif: int
    total_cuti_all: int

## detail jatah
class PMRekapCutiDetailJatah(BaseModel):
    nama: str
    nama_departemen: str
    penggunaan_cuti: int
    sisa_cuti: int
    status: str


## rekap penambahan kerja detail
class TanggalKerjaItem(BaseModel):
    tanggal: list[date] = []

class PMRekapPenambahanKerjaDetail(BaseModel):
    nama: str
    nama_departemen: str
    total_pengajuan: int
    disetujui: int
    ditolak: int
    status: str
    tanggal_kerja: list[TanggalKerjaItem]