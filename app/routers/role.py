from fastapi import APIRouter

from app.schemas.user import ExecutiveOut

router = APIRouter(prefix="/roles", tags=["Roles"])

ROLES = [
    {"id": 1, "nama": "karyawan"},
    {"id": 2, "nama": "pm"},
    {"id": 3, "nama": "hr"},
    {"id": 4, "nama": "direktur"},
]


@router.get("")
async def get_all_roles():
    return ROLES
