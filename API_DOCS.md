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
