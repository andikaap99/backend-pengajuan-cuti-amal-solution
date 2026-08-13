from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.department import router as department_router
from app.routers.karyawan import router as karyawan_router

app = FastAPI(title="Management Cuti Karyawan API")

app.include_router(auth_router)
app.include_router(department_router)
app.include_router(karyawan_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
