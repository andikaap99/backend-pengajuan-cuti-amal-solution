from typing import Annotated
import secrets
from datetime import datetime, timedelta, UTC
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user, hash_password, verify_password, require_role
from app.db import get_db
from app.models.user import User
from app.models.user_pm import UserPM
from app.models.password_reset_token import PasswordResetToken
from app.schemas.user import Token, UserOut, UserRegister, UserMeOut, UserRegisterAdmin, ChangePassword, ChangePasswordMessage, ExecutiveOut, UpdateProfile, UpdateProfileMessage, ForgotPasswordRequest, ForgotPasswordMessage, ResetPasswordRequest, ResetPasswordRequestById, ResetPasswordMessage
from app.services.cuti_service import hitung_cuti_terpakai
from app.services.email_service import send_forgot_password_email, send_password_changed_notification

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

router = APIRouter(prefix="/auth", tags=["Auth"])


## route login
@router.post("/login", response_model=Token)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"id_user": user.id_user, "role": user.role})
    
    return Token(access_token=access_token)


## route register
@router.post("/register", response_model=UserOut)
async def register(
    data: UserRegister,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar",
        )

    user = User(
        username=data.username,
        nama=data.nama,
        password=hash_password(data.password),
        role="karyawan",
        id_departemen=data.id_departemen,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user

## route register
@router.post("/register-admin", response_model=UserOut)
async def register(
    data: UserRegisterAdmin,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role("hr_manager", "staff_hr", "direktur"))],
):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar",
        )

    user = User(
        username=data.username,
        nama=data.nama,
        password=hash_password(data.password),
        role=data.role.lower(),
        id_departemen=data.id_departemen,
        email=data.email,
        no_telp=data.no_telp,
        tanggal_bergabung=data.tanggal_bergabung,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    ## handle PM assignment untuk role karyawan
    if data.role.lower() == "karyawan" and data.id_pm_list:
        for pm_id in data.id_pm_list:
            result_pm = await db.execute(select(User).where(User.id_user == pm_id, User.role == "pm"))
            pm_user = result_pm.scalar_one_or_none()
            if not pm_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User dengan ID {pm_id} tidak ditemukan atau bukan role PM!",
                )
            new_pm = UserPM(id_karyawan=user.id_user, id_pm=pm_id)
            db.add(new_pm)
        await db.commit()

    return user

@router.put("/change-password", response_model=ChangePasswordMessage)
async def change_password(
    data: ChangePassword,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    if not verify_password(data.password_lama, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password lama salah",
        )
    if data.password_baru != data.konfirmasi_password_baru:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konfirmasi password baru tidak cocok",
        )

    if verify_password(data.password_baru, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password baru tidak boleh sama dengan password lama",
        )

    current_user.password = hash_password(data.password_baru)
    db.add(current_user)
    await db.commit()

    return ChangePasswordMessage(detail="Password berhasil diubah")

## route get about me
@router.get("/me", response_model=UserMeOut)
async def get_me(current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(User).where(User.id_user == current_user.id_user)
    )
    user = result.scalar_one()

    cuti_terpakai = await hitung_cuti_terpakai(user.id_user, db)

    return UserMeOut(
        id_user=user.id_user,
        username=user.username,
        nama=user.nama,
        role=user.role,
        id_departemen=user.id_departemen,
        total_cuti=user.total_cuti,
        cuti_terpakai=cuti_terpakai,
        sisa_cuti=user.sisa_cuti,
        email=user.email,
        no_telp=user.no_telp,
        tanggal_bergabung=user.tanggal_bergabung,
    )


## route get all users
@router.get("/users", response_model=list[ExecutiveOut])
async def get_all_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User))
    return result.scalars().all()


## route update profile
@router.put("/profile", response_model=UpdateProfileMessage)
async def update_profile(
    data: UpdateProfile,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if data.no_telp is not None:
        current_user.no_telp = data.no_telp

    db.add(current_user)
    await db.commit()

    return UpdateProfileMessage(detail="Profile berhasil diupdate")


## route forgot password
@router.post("/forgot-password", response_model=ForgotPasswordMessage)
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if user and user.email:
        token = secrets.token_urlsafe(32)
        expired_at = datetime.now(UTC) + timedelta(minutes=30)

        reset_token = PasswordResetToken(
            id_user=user.id_user,
            token=token,
            expired_at=expired_at,
        )
        db.add(reset_token)
        await db.commit()

        background_tasks.add_task(send_forgot_password_email, user, token)

    return ForgotPasswordMessage(detail="Jika username terdaftar, link reset password telah dikirim")


## validasi token reset password
async def _get_valid_reset_token(token: str, db: AsyncSession) -> PasswordResetToken:
    result = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token tidak valid",
        )

    if reset_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sudah digunakan",
        )

    expired_at = reset_token.expired_at
    if expired_at.tzinfo is None:
        expired_at = expired_at.replace(tzinfo=UTC)
    if datetime.now(UTC) > expired_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token sudah expired",
        )

    return reset_token


## route konfirmasi reset password via forgot password (password baru pilihan user)
@router.post("/confirm-reset-password", response_model=ResetPasswordMessage)
async def confirm_reset_password(
    data: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reset_token = await _get_valid_reset_token(data.token, db)

    result_user = await db.execute(
        select(User).where(User.id_user == reset_token.id_user)
    )
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User tidak ditemukan",
        )

    user.password = hash_password(data.password_baru)
    db.add(user)

    reset_token.used = True
    db.add(reset_token)

    await db.commit()

    if user.email:
        background_tasks.add_task(send_password_changed_notification, user, data.password_baru)

    return ResetPasswordMessage(detail="Password berhasil diubah")


## route reset password ke default (untukdevajaya) tanpa input user - khusus HR/Direktur
@router.post("/reset-password", response_model=ResetPasswordMessage)
async def reset_password(
    data: ResetPasswordRequestById,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(require_role("hr_manager", "staff_hr", "direktur"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result_user = await db.execute(
        select(User).where(User.id_user == data.id_user)
    )
    user = result_user.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User tidak ditemukan",
        )

    password_default = "untukdevajaya"
    user.password = hash_password(password_default)
    db.add(user)

    await db.commit()

    if user.email:
        background_tasks.add_task(send_password_changed_notification, user, password_default)

    return ResetPasswordMessage(detail="Password berhasil direset ke default")


## route halaman reset password (HTML)
@router.get("/reset-password-page", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(request, "reset_password.html", {"token": token})