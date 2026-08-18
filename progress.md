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

---

## Catatan
- Jalankan migration: `.venv/bin/alembic upgrade head`
- Task di `todo.md` sudah semua selesai
