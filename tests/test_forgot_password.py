from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.password_reset_token import PasswordResetToken
from app.routers.auth import forgot_password
from app.schemas.user import ForgotPasswordRequest, ForgotPasswordMessage
from conftest import make_user, seed_departemen


async def _count_tokens(db: AsyncSession, id_user: int) -> int:
    rows = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.id_user == id_user)
    )
    return len(rows.all())


async def test_forgot_password_username_ada(db):
    await seed_departemen(db)
    user = await make_user(db, "karyawan1", "karyawan", email="karyawan1@mail.com")
    await db.commit()

    from fastapi import BackgroundTasks
    tasks = BackgroundTasks()
    result = await forgot_password(
        ForgotPasswordRequest(username="karyawan1"), tasks, db
    )

    assert isinstance(result, ForgotPasswordMessage)
    assert "username terdaftar" in result.detail
    assert await _count_tokens(db, user.id_user) == 1
    ## email di-queue sebagai background task (tidak dikirim saat test)
    assert len(tasks.tasks) == 1


async def test_forgot_password_username_tidak_ada(db):
    await seed_departemen(db)
    from fastapi import BackgroundTasks
    tasks = BackgroundTasks()
    result = await forgot_password(
        ForgotPasswordRequest(username="tidakada"), tasks, db
    )

    ## response identik (anti-enumerasi), tidak ada token dibuat
    assert result.detail == "Jika username terdaftar, link reset password telah dikirim"
    rows = await db.execute(select(PasswordResetToken))
    assert len(rows.all()) == 0
    assert len(tasks.tasks) == 0


async def test_forgot_password_tanpa_email(db):
    ## username ada tapi email kosong -> tidak kirim, response tetap sama
    await seed_departemen(db)
    user = await make_user(db, "karyawan1", "karyawan", email=None)
    await db.commit()

    from fastapi import BackgroundTasks
    tasks = BackgroundTasks()
    result = await forgot_password(
        ForgotPasswordRequest(username="karyawan1"), tasks, db
    )

    assert result.detail == "Jika username terdaftar, link reset password telah dikirim"
    assert await _count_tokens(db, user.id_user) == 0
    assert len(tasks.tasks) == 0
