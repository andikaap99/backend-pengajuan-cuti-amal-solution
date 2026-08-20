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
