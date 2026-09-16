from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import async_session_factory
from app.routers.auth import router as auth_router
from app.routers.department import router as department_router
from app.routers.karyawan import router as karyawan_router
from app.routers.pm import router as pm_router
from app.routers.hr import router as hr_router
from app.routers.direktur import router as direktur_router
from app.routers.holiday import router as holiday_router
from app.routers.approval import router as approval_router
from app.routers.role import router as role_router
from app.services.holiday_quota_service import proses_cuti_hari_libur
from app.services.auto_aktifkan_user_service import aktifkan_user_selesai_cuti
from app.services.holiday_service import sync_holidays

scheduler = AsyncIOScheduler()


async def job_holiday_quota():
    async with async_session_factory() as db:
        await proses_cuti_hari_libur(db)


async def job_aktifkan_user():
    async with async_session_factory() as db:
        await aktifkan_user_selesai_cuti(db)


async def job_sync_holidays():
    from datetime import date
    year = date.today().year
    async with async_session_factory() as db:
        await sync_holidays(year, db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ## run sekali saat startup (handle holiday yang kelewat)
    async with async_session_factory() as db:
        await proses_cuti_hari_libur(db)

    ## run sekali saat startup (aktifkan user yang cutinya sudah selesai)
    async with async_session_factory() as db:
        await aktifkan_user_selesai_cuti(db)

    ## run sekali saat startup (sync holiday jika belum ada data tahun ini)
    from datetime import date
    current_year = date.today().year
    async with async_session_factory() as db:
        from sqlalchemy import select
        from app.models.holiday import Holiday
        result = await db.execute(select(Holiday).where(Holiday.tahun == current_year).limit(1))
        if not result.scalar_one_or_none():
            await sync_holidays(current_year, db)

    ## schedule tiap jam 00:00
    scheduler.add_job(job_holiday_quota, CronTrigger(hour=0, minute=0), timezone=timezone("Asia/Jakarta"))
    scheduler.add_job(job_aktifkan_user, CronTrigger(hour=0, minute=0), timezone=timezone("Asia/Jakarta"))
    ## sync holiday otomatis tanggal 1 Januari tiap tahun jam 00:01
    scheduler.add_job(job_sync_holidays, CronTrigger(month=1, day=1, hour=0, minute=1), timezone=timezone("Asia/Jakarta"))
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Management Cuti Karyawan API", lifespan=lifespan)

origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(department_router)
app.include_router(karyawan_router)
app.include_router(pm_router)
app.include_router(hr_router)
app.include_router(direktur_router)
app.include_router(holiday_router)
app.include_router(approval_router)
app.include_router(role_router)


@app.get("/health")
async def health_check():
    
    return {"status": "ok"}
