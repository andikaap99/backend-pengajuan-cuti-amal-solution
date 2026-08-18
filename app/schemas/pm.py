from datetime import date
from typing import Optional

from pydantic import BaseModel


## apa aja yang dikirim waktu register
class PMDashboardRingkasanOut(BaseModel):
    sisa_cuti: int
    cuti_terpakai: int
    tim_menunggu_approval: int
    rekap_bulan_ini: int

class PMDashboardTimOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
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

class PMHistoryPersetujuanOut(BaseModel):
    tanggal_mulai: date
    tanggal_selesai: date
    nama: str
    jenis_cuti: str
    keterangan: str
    durasi: int
    pengganti: str
    status: str

class PMRekapCutiRingkasanOut(BaseModel):
    total_anggota_aktif: int
    total_cuti_all: int

class PMRekapCutiDetailJatah(BaseModel):
    nama: str
    nama_departemen: str
    penggunaan_cuti: int
    status: str