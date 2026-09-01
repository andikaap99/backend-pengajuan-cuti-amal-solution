# Progress - 14 Agustus 2026

## Ringkasan Pekerjaan Hari Ini

### 1. Fix Riwayat Cuti Pribadi
- Update schema `RiwayatCutiOut` — tambah field `nama_pengganti` (ganti dari `pengganti: int`)
- Update service `get_my_leaves()` — konversi SQLAlchemy ke Pydantic schema + hitung `durasi`
- Update router `GET /karyawan/cuti` — response `list[RiwayatCutiOut]`

### 2. Fix Pengajuan Cuti
- Hapus field `jenis_cuti` dari request body — otomatis diisi "cuti tahunan"
- Update schema `LogCutiBase` — hapus `jenis_cuti`

### 3. Endpoint Get Data Petinggi
- `GET /pm` — get semua PM (akses: pm, hr, direktur)
- `GET /hr` — get semua HR (akses: hr, direktur)
- `GET /direktur` — get semua Direktur (akses: direktur)
- Schema `PMOut` — hanya `id_user` dan `nama` (hapus `username`)

### 4. Endpoint Pengajuan Ongoing
- Schema `PengajuanOngoingOut` — jenis_cuti, durasi, keterangan, tanggal_mulai, tanggal_selesai, status_sekarang, disetujui_pm/hr/direktur, approved_at_pm/hr/direktur, alasan_penolakan
- Service `get_my_ongoing_leaves()` — filter ongoing sesuai role
- Service `get_ongoing_statuses()` — definisi status ongoing per role
- `GET /karyawan/cuti/ongoing` — list semua cuti yang masih ongoing

### 5. Endpoint Get All Users
- `GET /auth/users` — get semua user (id_user, nama)
- Schema `ExecutiveOut`

### 6. Update Profile
- Tambah field di tabel `users`: `email`, `no_telp`, `tanggal_bergabung` (nullable)
- Schema `UpdateProfile` — untuk update profile
- Schema `UserMeOut` — tambah field email, no_telp, tanggal_bergabung
- `PUT /auth/profile` — update profile (semua field optional)

### 7. Database Migration
- `add kolom tanggal_pengajuan di log_cuti`
- `add email no_telp tanggal_bergabung to users`

### 8. Dokumentasi API
- Update `API_DOCS.md` dengan semua endpoint baru

---

# Progress - 20 Agustus 2026

## HR Dashboard Endpoints

### 1. Ringkasan
**Endpoint:** `GET /hr/dashboard`

**Output:**
```json
{
  "total_karyawan": 25,
  "menunggu_hr": 5,
  "total_cuti_bulan_ini": 12,
  "total_cuti_bulan_depan": 8
}
```

### 2. List Cuti Karyawan Mendatang
**Endpoint:** `GET /hr/list-cuti-mendatang`

**Output:**
```json
[
  {
    "nama": "Budi Santoso",
    "jenis_cuti": "cuti tahunan",
    "tanggal_mulai": "2026-08-25",
    "tanggal_selesai": "2026-08-28",
    "status": "menunggu_hr"
  }
]
```

### 3. Ringkasan Persetujuan
**Endpoint:** `GET /hr/dashboard-persetujuan`

**Output:**
```json
{
  "total_menunggu": 5,
  "disetujui_bulan_ini": 12,
  "ditolak_bulan_ini": 3
}
```

### 4. Rekapitulasi
**Endpoint:** `GET /hr/rekapitulasi`

**Output:**
```json
[
  {
    "nama": "Budi Santoso",
    "departemen": "Engineering",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "total_cuti": 12,
    "sisa_cuti": 7
  }
]
```

### 5. Log Cuti
**Endpoint:** `GET /hr/log-cuti`

**Output:**
```json
[
  {
    "nama": "Budi Santoso",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "durasi": 3,
    "jenis_cuti": "cuti tahunan",
    "keterangan": "Cuti keluarga",
    "pengganti": "Andi",
    "status": "disetujui_direktur",
    "hr_approved_by": "Siti HR"
  }
]
```

### 6. Dashboard Master
**Endpoint:** `GET /hr/dashboard-master`

**Output:**
```json
{
  "total_karyawan": 25,
  "total_departemen": 5,
  "total_project_manager": 4
}
```

### 7. Tabel Karyawan
**Endpoint:** `GET /hr/tabel-karyawan`

**Output:**
```json
[
  {
    "nama": "Budi Santoso",
    "departemen": "Engineering",
    "jabatan": "Karyawan",
    "email": "budi@email.com",
    "status": "Aktif"
  }
]
```

### 8. Tabel Departemen
**Endpoint:** `GET /hr/tabel-departemen`

**Output:**
```json
[
  {
    "nama_departemen": "Engineering",
    "jumlah_karyawan": 10
  }
]
```

### 9. Manajemen Jatah Cuti
**Endpoint:** `GET /hr/manajemen-jatah-cuti`

**Output:**
```json
{
  "total_karyawan_aktif": 20,
  "total_karyawan_cuti": 5
}
```

### 10. Daftar Cuti Karyawan
**Endpoint:** `GET /hr/daftar-cuti-karyawan`

**Output:**
```json
[
  {
    "nama": "Budi Santoso",
    "nama_departemen": "Engineering",
    "total_cuti": 12,
    "cuti_terpakai": 5,
    "sisa_cuti": 7
  }
]
```

---

## Daftar Endpoint Lengkap

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/auth/register` | Register karyawan |
| POST | `/auth/register-admin` | Register admin (hr/direktur) |
| POST | `/auth/login` | Login |
| GET | `/auth/me` | Get current user |
| PUT | `/auth/change-password` | Ganti password |
| GET | `/auth/users` | Get semua user |
| PUT | `/auth/profile` | Update profile |
| GET | `/departemen` | Get semua departemen |
| POST | `/karyawan/cuti` | Pengajuan cuti |
| GET | `/karyawan/cuti` | Riwayat cuti |
| GET | `/karyawan/cuti/ongoing` | Cuti ongoing |
| GET | `/pm` | Get semua PM |
| GET | `/hr` | Get semua HR |
| GET | `/direktur` | Get semua Direktur |
| GET | `/hr/dashboard` | Dashboard ringkasan HR |
| GET | `/hr/list-cuti-mendatang` | List cuti mendatang |
| GET | `/hr/dashboard-persetujuan` | Ringkasan persetujuan |
| GET | `/hr/rekapitulasi` | Rekapitulasi cuti |
| GET | `/hr/log-cuti` | Log cuti |
| GET | `/hr/dashboard-master` | Dashboard master |
| GET | `/hr/tabel-karyawan` | Tabel karyawan |
| GET | `/hr/tabel-departemen` | Tabel departemen |
| GET | `/hr/manajemen-jatah-cuti` | Manajemen jatah cuti |
| GET | `/hr/daftar-cuti-karyawan` | Daftar cuti karyawan |

---

## Catatan
- Jalankan migration: `.venv/bin/alembic upgrade head`
- Task di `todo.md` sudah semua selesai

---

# Progress - 1 September 2026

## Data Demo Seeder

### File: `seed_demo.py`
Membuat data demo lengkap untuk testing:

**Departemen:**
1. Engineering (id=1)
2. Marketing (id=2)
3. Design (id=3)

**Users (7 orang):**

| ID | Username | Nama | Role | Dept | PM | Sisa Cuti |
|----|----------|------|------|------|-----|-----------|
| 2 | andika99 | Andika Aryadi Putra | hr | 1 | - | 9 |
| 3 | airinr | Airin Ristiana | pm | 1 | - | 10 |
| 4 | rizza | Rizza Alyda Yahya | karyawan | 2 | 3 | 8 |
| 5 | achmad | Achmad Rizqi Ramadhan | direktur | 1 | - | 12 |
| 6 | topik | Topik Nur Rahman | pm | 1 | - | 12 |
| 7 | rissa | Rissa | karyawan | 3 | 3 | 8 |
| 8 | arneta | Arneta Ristiana | karyawan | 2 | 3 | 12 |

**Password semua user:** `untukdevajaya`

**Alur Approval:**
- Karyawan dept 2 & 3 → PM → HR (selesai)
- Karyawan dept 1 → HR (selesai)
- PM → HR (selesai)
- HR → Direktur (selesai)

**Log Cuti (13 data):**

| User | Durasi | Status | Keterangan |
|------|--------|--------|------------|
| Rizza | 4 hari | disetujui_hr | Cuti awal tahun |
| Rizza | 3 hari | ditolak_pm | Keperluan keluarga |
| Rizza | 3 hari | menunggu_pm | Traveling dengan teman |
| Topik | 3 hari | menunggu_hr | Lebaran |
| Topik | 3 hari | ditolak_hr | Pernikahan saudara |
| Topik | 4 hari | menunggu_hr | Liburan akhir tahun |
| Rissa | 4 hari | disetujui_hr | Cuti menikah |
| Rissa | 3 hari | ditolak_pm | Ulang tahun |
| Rissa | 3 hari | menunggu_pm | Keperluan pribadi |
| Airin | 3 hari | menunggu_hr | Cuti keluarga |
| Airin | 2 hari | disetujui_hr | Idul Fitri |
| Andika | 3 hari | menunggu_direktur | Cuti Lebaran |
| Andika | 3 hari | disetujui_direktur | Acara keluarga |

### Cara Jalankan
```bash
# Drop & buat ulang database
mysql -u root -e "DROP DATABASE IF EXISTS db_cuti_karyawan; CREATE DATABASE db_cuti_karyawan;"

# Jalankan migrasi
alembic upgrade head

# Jalankan seeder
python seed_demo.py --force
```
