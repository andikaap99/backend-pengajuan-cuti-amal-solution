from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user, hash_password, verify_password, require_role
from app.db import get_db
from app.models.user import User
from app.schemas.user import Token, UserOut, UserRegister, UserMeOut, UserRegisterAdmin, ChangePassword, ChangePasswordMessage, ExecutiveOut

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
        id_pm=data.id_pm,
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
    current_user: Annotated[User, Depends(require_role("hr", "direktur"))],
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
        id_pm=data.id_pm,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
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
        select(User).options(selectinload(User.manager)).where(User.id_user == current_user.id_user)
    )
    user = result.scalar_one()
    return user


## route get all users
@router.get("/users", response_model=list[ExecutiveOut])
async def get_all_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User))
    return result.scalars().all()
