from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel



## dashboard
## ringkasan
class HRDashboardRingkasanOut(BaseModel):
    total_karyawan: int
    menunggu: int
    total_pengajuan: int
    total_pengajuan_diacc: int
    total_pengajuan_ditolak: int
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int

## list cuti mendatang
class HRListCutiKaryawanMendatangOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal: list[date] = []
    tanggal_pengajuan: datetime
    status: str


## persetujuan
## ringkasan persetujuan
class HRDashboardPersetujuanOut(BaseModel):
    total_menunggu: int
    disetujui_bulan_ini: int
    ditolak_bulan_ini: int


## rekap cuti
## rekapitulasi
class HRRekapitulasiOut(BaseModel):
    nama: str
    nama_departemen: str
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int

## log cuti
class HRLogCutiOut(BaseModel):
    nama: str
    tanggal: list[date] = []
    durasi: int
    jenis_cuti: str
    keterangan: str
    pengganti: str
    tanggal_pengajuan: datetime
    status: Literal[
            "menunggu_pm", "disetujui_pm", "ditolak_pm",
            "menunggu_hr", "disetujui_hr", "ditolak_hr",
            "menunggu_direktur", "disetujui_direktur", "ditolak_direktur",
            "cuti_bersama"
        ]
    approved_by: Optional[str] = None


## data karyawan
## ringkasan
class HRRingkasanKaryawanOut(BaseModel):
    total_karyawan: int
    total_departemen: int
    total_project_manager: int

## tabel karyawan
class HRTabelKaryawanOut(BaseModel):
    id_user: int
    username: str
    password: str
    nama: str
    departemen: str
    jabatan: str
    email: Optional[str] = None
    no_telp: Optional[str] = None
    tanggal_bergabung: Optional[date] = None
    nama_pm: list[str] = []
    status: str

## tabel departemen
class HRTabelDepartemenOut(BaseModel):
    nama_departemen: str
    jumlah_karyawan: int


## manajemen jatah cuti
## ringkasan
class HRManajemenJatahCutiRingkasanOut(BaseModel):
    total_karyawan_aktif: int
    total_karyawan_cuti: int

class HRDaftarCutiKaryawanOut(BaseModel):
    nama: str
    nama_departemen: str
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int


## edit karyawan
class EditKaryawanRequest(BaseModel):
    username: Optional[str] = None
    nama: Optional[str] = None
    role: Optional[str] = None
    id_departemen: Optional[int] = None
    email: Optional[str] = None
    no_telp: Optional[str] = None
    tanggal_bergabung: Optional[date] = None
    status: Optional[Literal["Aktif", "Cuti"]] = None
    password: Optional[str] = None
    pm_add: Optional[list[int]] = None
    pm_remove: Optional[list[int]] = None

class EditKaryawanResponse(BaseModel):
    detail: str


## reset password
class ResetPasswordResponse(BaseModel):
    detail: str


## delete karyawan
class DeleteKaryawanResponse(BaseModel):
    detail: str


## log pengajuan kerja
class HRLogPenambahanKerjaOut(BaseModel):
    nama: str
    tanggal: list[date] = []
    durasi: int
    keterangan: str
    tanggal_pengajuan: datetime
    status: Literal["menunggu_pm", "disetujui_pm", "ditolak_pm", "menunggu_hr", "disetujui_hr", "ditolak_hr", "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"]
    pengganti: str
    approved_by: Optional[str] = None


## rekapitulasi pengajuan kerja
class HRRekapitulasiPenambahanKerjaOut(BaseModel):
    nama: str
    nama_departemen: str
    total_pengajuan: int
    disetujui: int
    ditolak: int
    approved_by: Optional[str] = None