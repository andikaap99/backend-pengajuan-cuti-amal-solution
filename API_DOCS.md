# API Documentation - Management Cuti Karyawan

## Base URL
```
http://localhost:8000
```

## Authentication
Semua endpoint yang dilindungi memerlukan header:
```
Authorization: Bearer <token>
```

---

## Auth Endpoints

### 1. Register
**POST** `/auth/register`

Mendaftarkan akun baru (karyawan).

**Request Body (JSON):**
```json
{
  "username": "john_doe",
  "nama": "John Doe",
  "password": "password123",
  "id_departemen": 1,
  "id_pm": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| username | string | Ya | Username untuk login |
| nama | string | Ya | Nama lengkap |
| password | string | Ya | Password (akan di-hash) |
| id_departemen | int | Ya | ID departemen |
| id_pm | int | Tidak | ID Project Manager (nullable) |

**Response 200:**
```json
{
  "id_user": 1,
  "username": "john_doe",
  "nama": "John Doe",
  "role": "karyawan",
  "id_departemen": 1
}
```

**Error 400:**
```json
{
  "detail": "Username sudah terdaftar"
}
```

---

### 2. Login
**POST** `/auth/login`

Login dan dapatkan JWT token.

**Request Body (Form Data):**
```
username: john_doe
password: password123
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error 401:**
```json
{
  "detail": "Username atau password salah"
}
```

---

### 3. Get Current User
**GET** `/auth/me`

Mendapatkan data user yang sedang login beserta info PM.

**Headers:**
```
Authorization: Bearer <token>
```

**Response 200:**
```json
{
  "id_user": 1,
  "username": "john_doe",
  "nama": "John Doe",
  "role": "karyawan",
  "id_departemen": 1,
  "id_pm": 5,
  "total_cuti": 12,
  "sisa_cuti": 10,
  "pm": {
    "id_user": 5,
    "username": "pm_jane",
    "nama": "Jane Smith"
  }
}
```

---

### 4. Change Password
**PUT** `/auth/change-password`

Mengubah password user yang sedang login.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body (JSON):**
```json
{
  "password_lama": "oldpassword123",
  "password_baru": "newpassword456",
  "konfirmasi_password_baru": "newpassword456"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| password_lama | string | Ya | Password saat ini |
| password_baru | string | Ya | Password baru |
| konfirmasi_password_baru | string | Ya | Konfirmasi password baru |

**Response 200:**
```json
{
  "detail": "Password berhasil diubah"
}
```

**Error 400:**
```json
{
  "detail": "Password lama salah"
}
```

```json
{
  "detail": "Konfirmasi password baru tidak cocok"
}
```

```json
{
  "detail": "Password baru tidak boleh sama dengan password lama"
}
```

---

### 5. Get All Users
**GET** `/auth/users`

Mendapatkan daftar semua user (id_user dan nama).

**Headers:**
```
Authorization: Bearer <token>
```

**Response 200:**
```json
[
  {
    "id_user": 1,
    "nama": "John Doe"
  },
  {
    "id_user": 2,
    "nama": "Jane Smith"
  },
  {
    "id_user": 3,
    "nama": "Budi Santoso"
  }
]
```

---

### 6. Update Profile
**PUT** `/auth/profile`

Mengupdate data profile (email, no_telp, tanggal_bergabung). Semua field bersifat optional.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body (JSON):**
```json
{
  "email": "john@example.com",
  "no_telp": "08123456789",
  "tanggal_bergabung": "2024-01-15"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Tidak | Alamat email |
| no_telp | string | Tidak | Nomor telepon |
| tanggal_bergabung | date | Tidak | Tanggal bergabung (YYYY-MM-DD) |

**Response 200:**
```json
{
  "detail": "Profile berhasil diupdate"
}
```

---

## Departemen Endpoints

### 1. Get All Departemen
**GET** `/departemen`

Mendapatkan daftar semua departemen.

**Response 200:**
```json
[
  {
    "id_departemen": 1,
    "nama_departemen": "Engineering"
  },
  {
    "id_departemen": 2,
    "nama_departemen": "Human Resources"
  }
]
```

---

## Karyawan Endpoints

### 1. Pengajuan Cuti
**POST** `/karyawan/cuti`

Mengajukan cuti baru (hanya untuk karyawan). Jenis cuti otomatis "cuti tahunan".

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body (JSON):**
```json
{
  "tanggal_mulai": "2026-08-20",
  "tanggal_selesai": "2026-08-22",
  "keterangan": "Libur keluarga",
  "pengganti": 3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| tanggal_mulai | date | Ya | Tanggal mulai cuti (YYYY-MM-DD) |
| tanggal_selesai | date | Ya | Tanggal selesai cuti (YYYY-MM-DD) |
| keterangan | string | Ya | Keterangan/surat izin cuti |
| pengganti | int | Tidak | ID user pengganti (nullable) |

**Response 200:**
```json
{
  "id_log_cuti": 1,
  "id_user": 1,
  "jenis_cuti": "cuti tahunan",
  "tanggal_mulai": "2026-08-20",
  "tanggal_selesai": "2026-08-22",
  "keterangan_cuti": "Libur keluarga",
  "status": "menunggu_pm",
  "alasan_penolakan": null,
  "disetujui_pm": null,
  "disetujui_hr": null,
  "disetujui_direktur": null,
  "approved_at_pm": null,
  "approved_at_hr": null,
  "approved_at_direktur": null
}
```

**Error 400:**
```json
{
  "detail": "Tanggal cuti tidak boleh di masa lalu"
}
```

```json
{
  "detail": "Maksimal pengajuan 10 hari sebelum hari pertama cuti"
}
```

```json
{
  "detail": "Tanggal tidak valid"
}
```

```json
{
  "detail": "Maksimal cuti selama 4 hari"
}
```

```json
{
  "detail": "Sisa cuti tidak cukup"
}
```

```json
{
  "detail": "Pengganti tidak boleh diri sendiri"
}
```

```json
{
  "detail": "Direktur tidak bisa mengajukan cuti"
}
```

**Error 403:**
```json
{
  "detail": "Anda tidak memiliki akses"
}
```

**Error 404:**
```json
{
  "detail": "User tidak ditemukan"
}
```

```json
{
  "detail": "User pengganti tidak ditemukan"
}
```

---

### 2. Riwayat Pengajuan Cuti
**GET** `/karyawan/cuti`

Melihat semua riwayat pengajuan cuti milik user yang sedang login.

**Headers:**
```
Authorization: Bearer <token>
```

**Response 200:**
```json
[
  {
    "jenis_cuti": "cuti tahunan",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "keterangan": "Libur keluarga",
    "nama_pengganti": "Budi Santoso",
    "durasi": 3,
    "status": "menunggu_pm"
  },
  {
    "jenis_cuti": "cuti tahunan",
    "tanggal_mulai": "2026-07-10",
    "tanggal_selesai": "2026-07-11",
    "keterangan": "Sakit flu",
    "nama_pengganti": "Andi Wijaya",
    "durasi": 2,
    "status": "disetujui_direktur"
  }
]
```

---

### 3. Pengajuan Cuti Ongoing
**GET** `/karyawan/cuti/ongoing`

Melihat semua cuti yang masih dalam proses (belum selesai/ditolak).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** karyawan, hr, pm

**Response 200:**
```json
[
  {
    "jenis_cuti": "cuti tahunan",
    "durasi": 3,
    "keterangan": "Libur keluarga",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "status_sekarang": "menunggu_hr",
    "disetujui_pm": 5,
    "disetujui_hr": null,
    "disetujui_direktur": null,
    "approved_at_pm": "2026-08-18",
    "approved_at_hr": null,
    "approved_at_direktur": null,
    "alasan_penolakan": null
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| jenis_cuti | string | Jenis cuti (selalu "cuti tahunan") |
| durasi | int | Durasi cuti dalam hari |
| keterangan | string | Keterangan cuti |
| tanggal_mulai | date | Tanggal mulai cuti |
| tanggal_selesai | date | Tanggal selesai cuti |
| status_sekarang | string | Status pengajuan saat ini |
| disetujui_pm | int \| null | ID PM yang menyetujui (null jika belum) |
| disetujui_hr | int \| null | ID HR yang menyetujui (null jika belum) |
| disetujui_direktur | int \| null | ID Direktur yang menyetujui (null jika belum) |
| approved_at_pm | date \| null | Tanggal PM menyetujui |
| approved_at_hr | date \| null | Tanggal HR menyetujui |
| approved_at_direktur | date \| null | Tanggal Direktur menyetujui |
| alasan_penolakan | string \| null | Alasan penolakan (null jika tidak ditolak) |

---

### 4. Ringkasan Cuti Dashboard
**GET** `/karyawan/cuti/ringkasan`

Melihat ringkasan cuti untuk dashboard karyawan.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** karyawan, pm, hr

**Response 200:**
```json
{
  "periode_tahun": 2026,
  "total_cuti": 12,
  "cuti_terpakai": 3,
  "sisa_cuti": 9
}
```

| Field | Type | Description |
|-------|------|-------------|
| periode_tahun | int | Tahun periode cuti |
| total_cuti | int | Total jatah cuti per tahun |
| cuti_terpakai | int | Jumlah cuti yang sudah terpakai |
| sisa_cuti | int | Sisa jatah cuti |

---

### 5. Kalender Cuti Saya
**GET** `/karyawan/kalender-cuti-saya`

Melihat kalender cuti pribadi (data per hari).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** karyawan, pm, hr

**Response 200:**
```json
[
  {
    "tanggal": "2026-07-07",
    "nama": "John Doe",
    "keterangan": "Libur keluarga",
    "jenis_cuti": "cuti tahunan",
    "status": "disetujui_direktur"
  },
  {
    "tanggal": "2026-07-08",
    "nama": "John Doe",
    "keterangan": "Libur keluarga",
    "jenis_cuti": "cuti tahunan",
    "status": "disetujui_direktur"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| tanggal | date | Tanggal cuti (per hari) |
| nama | string | Nama karyawan |
| keterangan | string | Keterangan cuti |
| jenis_cuti | string | Jenis cuti |
| status | string | Status pengajuan |

---

### 6. Kalender Cuti Tim
**GET** `/karyawan/kalender-cuti-tim`

Melihat kalender cuti seluruh anggota tim (data per hari).
- **PM**: melihat cuti sendiri + anggota tim
- **Karyawan**: melihat cuti semua yang satu tim (id_pm sama)

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** karyawan, pm, hr

**Response 200:**
```json
[
  {
    "tanggal": "2026-07-07",
    "nama": "John Doe",
    "keterangan": "Libur keluarga",
    "jenis_cuti": "cuti tahunan",
    "status": "disetujui_direktur"
  },
  {
    "tanggal": "2026-07-07",
    "nama": "Budi Santoso",
    "keterangan": "Sakit",
    "jenis_cuti": "cuti tahunan",
    "status": "menunggu_pm"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| tanggal | date | Tanggal cuti (per hari) |
| nama | string | Nama karyawan |
| keterangan | string | Keterangan cuti |
| jenis_cuti | string | Jenis cuti |
| status | string | Status pengajuan |

---

## Project Manager Endpoints

### 1. Get All PM
**GET** `/pm`

Mendapatkan daftar semua Project Manager.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** hr, direktur

**Response 200:**
```json
[
  {
    "id_user": 5,
    "nama": "Jane Smith"
  },
  {
    "id_user": 8,
    "nama": "Robert Johnson"
  }
]
```

---

### 2. Ringkasan Tim
**GET** `/pm/ringkasan-tim`

Mendapatkan ringkasan data tim yang dikelola PM (total pengajuan, menunggu persetujuan, sedang cuti).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** pm

**Response 200:**
```json
{
  "tahun": 2026,
  "total_pengajuan": 15,
  "menunggu_persetujuan": 3,
  "sedang_cuti": 1
}
```

| Field | Type | Description |
|-------|------|-------------|
| tahun | int | Tahun saat ini |
| total_pengajuan | int | Total pengajuan cuti dari anggota tim |
| menunggu_persetujuan | int | Pengajuan yang masih menunggu persetujuan PM |
| sedang_cuti | int | Anggota tim yang sedang cuti |

---

### 3. Queue Card
**GET** `/pm/queue-card`

Mendapatkan daftar pengajuan cuti yang menunggu persetujuan PM.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** pm

**Response 200:**
```json
[
  {
    "nama": "John Doe",
    "nama_departemen": "Engineering",
    "jenis_cuti": "cuti tahunan",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "durasi": 3,
    "pengganti": "Budi Santoso",
    "sisa_cuti": 9,
    "alasan": "Libur keluarga"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| nama | string | Nama karyawan yang mengajukan |
| nama_departemen | string | Nama departemen karyawan |
| jenis_cuti | string | Jenis cuti |
| tanggal_mulai | date | Tanggal mulai cuti |
| tanggal_selesai | date | Tanggal selesai cuti |
| durasi | int | Durasi cuti dalam hari |
| pengganti | string | Nama pengganti (atau "Tidak ada") |
| sisa_cuti | int | Sisa jatah cuti karyawan |
| alasan | string | Keterangan/alasan cuti |

---

### 4. Dashboard Ringkasan PM
**GET** `/pm/dashboard`

Mendapatkan ringkasan dashboard PM (sisa cuti pribadi, total pengajuan tim, menunggu approval, acc, dan decline).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** pm

**Response 200:**
```json
{
  "sisa_cuti": 9,
  "cuti_terpakai": 3,
  "tim_menunggu_appoval": 2,
  "total_pengajuan_tim": 10,
  "total_pengajuan_acc_tim": 7,
  "total_pengajuan_decline_tim": 1
}
```

| Field | Type | Description |
|-------|------|-------------|
| sisa_cuti | int | Sisa jatah cuti PM |
| cuti_terpakai | int | Jatah cuti yang sudah terpakai |
| tim_menunggu_appoval | int | Pengajuan tim yang menunggu approval PM |
| total_pengajuan_tim | int | Total pengajuan cuti dari seluruh anggota tim |
| total_pengajuan_acc_tim | int | Total pengajuan tim yang disetujui (disetujui_pm) |
| total_pengajuan_decline_tim | int | Total pengajuan tim yang ditolak (ditolak_pm) |

---

### 5. Dashboard Status Cuti Anggota Tim
**GET** `/pm/dashboard-tim`

Mendapatkan daftar status cuti anggota tim yang sedang dalam proses (belum selesai/ditolak).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** pm

**Response 200:**
```json
[
  {
    "nama": "John Doe",
    "jenis_cuti": "cuti tahunan",
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "status": "menunggu_pm"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| nama | string | Nama anggota tim |
| jenis_cuti | string | Jenis cuti |
| tanggal_mulai | date | Tanggal mulai cuti |
| tanggal_selesai | date | Tanggal selesai cuti |
| status | string | Status pengajuan saat ini |

---

### 6. Riwayat Cuti Tim
**GET** `/pm/history-cuti-tim`

Mendapatkan riwayat seluruh pengajuan cuti anggota tim (semua status).

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** pm

**Response 200:**
```json
[
  {
    "tanggal_mulai": "2026-08-20",
    "tanggal_selesai": "2026-08-22",
    "nama": "John Doe",
    "jenis_cuti": "cuti tahunan",
    "keterangan": "Libur keluarga",
    "durasi": 3,
    "pengganti": "Budi Santoso",
    "status": "disetujui_direktur"
  }
]
```

| Field | Type | Description |
|-------|------|-------------|
| tanggal_mulai | date | Tanggal mulai cuti |
| tanggal_selesai | date | Tanggal selesai cuti |
| nama | string | Nama karyawan yang mengajukan |
| jenis_cuti | string | Jenis cuti |
| keterangan | string | Keterangan/alasan cuti |
| durasi | int | Durasi cuti dalam hari |
| pengganti | string | Nama pengganti (atau "-" jika tidak ada) |
| status | string | Status pengajuan terkini |

---

## Human Resources Endpoints

### 1. Get All HR
**GET** `/hr`

Mendapatkan daftar semua HR.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** hr, direktur

**Response 200:**
```json
[
  {
    "id_user": 3,
    "nama": "Sarah Williams"
  },
  {
    "id_user": 6,
    "nama": "Michael Brown"
  }
]
```

---

## Direktur Endpoints

### 1. Get All Direktur
**GET** `/direktur`

Mendapatkan daftar semua Direktur.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** direktur

**Response 200:**
```json
[
  {
    "id_user": 2,
    "nama": "David Lee"
  }
]
```

---

## Holidays Endpoints

### 1. Sync Holidays
**POST** `/holidays/sync`

Sinkronisasi data libur nasional dan cuti bersama dari API Kemendesa ke database.

**Headers:**
```
Authorization: Bearer <token>
```

**Role Akses:** hr, direktur

**Response 200:**
```json
{
  "detail": "Berhasil sync 8 data libur tahun 2026"
}
```

---

### 2. Next Cuti Bersama
**GET** `/holidays/next`

Melihat cuti bersama berikutnya yang paling dekat (termasuk yang berturut-turut).

**Headers:**
```
Authorization: Bearer <token>
```

**Response 200:**
```json
{
  "nama_libur": "Idul Fitri 1447 Hijriah",
  "tanggal_mulai": "2026-03-20",
  "tanggal_selesai": "2026-03-21",
  "total_hari": 2,
  "sisa_hari": 214
}
```

**Response (tidak ada data):**
```json
null
```

| Field | Type | Description |
|-------|------|-------------|
| nama_libur | string | Nama cuti bersama |
| tanggal_mulai | date | Tanggal mulai cuti bersama |
| tanggal_selesai | date | Tanggal selesai cuti bersama (bergabung jika berturut-turut) |
| total_hari | int | Total hari cuti bersama |
| sisa_hari | int | Sisa hari hingga cuti bersama dimulai |

---

## Health Check
**GET** `/health`

**Response 200:**
```json
{
  "status": "ok"
}
```

---

## Roles
| Role | Deskripsi |
|------|-----------|
| karyawan | Karyawan biasa, bisa ajukan cuti |
| pm | Project Manager, approve cuti karyawan |
| hr | HR, approve cuti setelah PM |
| direktur | Direktur, approve cuti final |

---

## Status Cuti
Alur status pengajuan cuti:
```
menunggu_pm → disetujui_pm / ditolak_pm
    ↓ disetujui_pm
menunggu_hr → disetujui_hr / ditolak_hr
    ↓ disetujui_hr
menunggu_direktur → disetujui_direktur / ditolak_direktur
```

---

## Swagger UI
Untuk testing interaktif, akses:
```
http://localhost:8000/docs
```
