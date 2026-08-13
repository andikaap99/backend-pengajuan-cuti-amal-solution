from fastapi import FastAPI

from app.routers.auth import router as auth_router

app = FastAPI(title="Management Cuti Karyawan API")

app.include_router(auth_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
