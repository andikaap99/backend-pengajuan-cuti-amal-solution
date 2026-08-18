from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.department import router as department_router
from app.routers.karyawan import router as karyawan_router
from app.routers.pm import router as pm_router
from app.routers.hr import router as hr_router
from app.routers.direktur import router as direktur_router
from app.routers.holiday import router as holiday_router

app = FastAPI(title="Management Cuti Karyawan API")

app.include_router(auth_router)
app.include_router(department_router)
app.include_router(karyawan_router)
app.include_router(pm_router)
app.include_router(hr_router)
app.include_router(direktur_router)
app.include_router(holiday_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
