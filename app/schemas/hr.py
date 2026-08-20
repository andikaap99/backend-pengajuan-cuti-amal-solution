from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel



## dashboard
## ringkasan
class HRDashboardRingkasanOut(BaseModel):
    total_karyawan: int
    menunggu_hr: int
    total_cuti_bulan_ini: int
    total_cuti_bulan_depan: int

## list cuti mendatang
class HRListCutiKaryawanMendatangOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
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
    tanggal_mulai: date
    tanggal_selesai: date
    total_cuti: int
    sisa_cuti: int

## log cuti
class HRLogCutiOut(BaseModel):
    nama: str
    tanggal_mulai: date
    tanggal_selesai: date
    durasi: int
    jenis_cuti: str
    keterangan: str
    pengganti: str
    status: Literal[
            "menunggu_pm", "disetujui_pm", "ditolak_pm",
            "menunggu_hr", "disetujui_hr", "ditolak_hr",
            "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
        ]
    hr_approved_by: Optional[str] = None

### HRListCutiKaryawanMendatangOut
class HRListCutiKaryawanMendatangOut(BaseModel):
    nama: str
    jenis_cuti: str
    tanggal_mulai: date
    tanggal_selesai: date
    status: Literal[
        "menunggu_pm", "disetujui_pm", "ditolak_pm",
        "menunggu_hr", "disetujui_hr", "ditolak_hr",
        "menunggu_direktur", "disetujui_direktur", "ditolak_direktur"
    ]


### HRDashboardMasterRingkasanOut
class HRDashboardMasterRingkasanOut(BaseModel):
    total_karyawan: int
    total_departemen: int
    total_project_manager: int


### HRTabelKaryawanOut
class HRTabelKaryawanOut(BaseModel):
    nama: str
    departemen: str
    jabatan: str
    email: Optional[str] = None
    status: str


### HRTabelDepartemenOut
class HRTabelDepartemenOut(BaseModel):
    nama_departemen: str
    jumlah_karyawan: int


### HRManajemenJatahCutiRingkasanOut
class HRManajemenJatahCutiRingkasanOut(BaseModel):
    total_karyawan_aktif: int
    total_karyawan_cuti: int


### HRDaftarCutiKaryawanOut
class HRDaftarCutiKaryawanOut(BaseModel):
    nama: str
    nama_departemen: str
    total_cuti: int
    cuti_terpakai: int
    sisa_cuti: int