# Management Cuti Karyawan - Backend API

## Prasyarat

- Python 3.12+
- MySQL 8.0+
- Git

## Instalasi & Menjalankan

### 1. Clone / Pull Repository

```bash
git clone <repository-url>
cd backend_porgram
git pull
```

### 2. Buat Virtual Environment & Aktifkan

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
```

### 3. Install Dependency

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

Salin `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` → sesuai MySQL kamu
- `JWT_SECRET_KEY` → secret key favoritmu
- `MAIL_USERNAME` / `MAIL_PASSWORD` → akun Gmail untuk notifikasi email

### 5. Buat Database

```bash
mysql -u root -e "CREATE DATABASE IF NOT EXISTS db_cuti_karyawan;"
```

### 6. Jalankan Migrasi Database

```bash
alembic upgrade head
```

### 7. Jalankan Seeder

```bash
python seeder.py --force
```

> `--force` akan menghapus semua data lama dan mengisi ulang departemen + 1 user (Saverius).

### 8. Start Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 9. Akses API

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## Struktur Project

```
backend_porgram/
├── app/
│   ├── main.py              # Entry point FastAPI
│   ├── db.py                # Database engine & session
│   ├── core/
│   │   ├── config.py        # Pydantic settings
│   │   └── security.py      # JWT, bcrypt, RBAC
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request/response
│   ├── routers/             # API endpoints
│   └── services/            # Business logic
├── alembic/                 # Database migrations
├── seeder.py                # Seed script
├── seed_demo.py             # Demo seeder (lengkap)
├── seed_log_cuti.py         # Seed log cuti
├── templates/               # HTML templates (surat cuti)
├── requirements.txt         # Python dependencies
├── .env                     # Environment config
├── .env.example             # Env template
├── dockerfile               # Docker config (opsional)
├── alembic.ini              # Alembic config
├── API_DOCS.md              # Dokumentasi API lengkap
├── README.md                # File ini
└── todo.md                  # Catatan tugas
```

## Default User Setelah Seed

| Field | Value |
|-------|-------|
| ID | 1 |
| Username | `saver` |
| Nama | Saverius G. R. Demon Paji Dosinaeng |
| Role | `hr_manager` |
| Departemen | Manajemen Perusahaan (id=1) |
| Password | `untukdevajaya` |
| Total Cuti | 12 |
| Sisa Cuti | 12 |

## Endpoint Utama

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/auth/register` | Registrasi karyawan |
| POST | `/auth/login` | Login & dapatkan JWT |
| GET | `/auth/me` | Data user yang login |
| PUT | `/auth/change-password` | Ganti password |
| POST | `/karyawan/cuti` | Ajukan cuti |
| GET | `/karyawan/cuti` | Riwayat cuti |
| GET | `/pm/dashboard` | Dashboard PM |
| GET | `/hr/dashboard` | Dashboard HR |
| GET | `/approval/approval-queue` | Queue approval |
| POST | `/approval/approval{log_cuti_id}` | Approve/Decline cuti |
| GET | `/holidays/sync` | Sync holiday dari Kemendesa |
| GET | `/health` | Health check |

## Tips

- Jika ada perubahan model, jalankan: `alembic revision --autogenerate -m "deskripsi"` lalu `alembic upgrade head`
- Untuk reset database sepenuhnya: drop database → migrate → seeder
- Gunakan `python seeder.py --force` jika sudah ada data dan ingin mulai dari awal
