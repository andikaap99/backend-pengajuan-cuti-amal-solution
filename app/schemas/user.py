from pydantic import BaseModel


## apa aja yang dikirim waktu register
class UserRegister(BaseModel):
    username: str
    nama: str
    password: str
    id_departemen: int
    id_pm: int | None = None

class UserRegisterAdmin(BaseModel):
    username: str
    nama: str
    password: str
    role: str
    id_departemen: int
    id_pm: int | None = None

## apa aja yang ditampilin waktu register berhasil
class UserOut(BaseModel):
    id_user: int
    username: str
    nama: str
    role: str
    id_departemen: int

    model_config = {"from_attributes": True}

## data pm apa aja yang ditampilin (usermeout)
class PMOut(BaseModel):
    id_user: int
    username: str
    nama: str

    model_config = {"from_attributes": True}

## data apa aja yang ditampilin about me
class UserMeOut(BaseModel):
    id_user: int
    username: str
    nama: str
    role: str
    id_departemen: int
    id_pm: int | None = None
    total_cuti: int
    sisa_cuti: int
    pm: PMOut | None = None

    model_config = {"from_attributes": True}

## data akses token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

## message change password
class ChangePasswordMessage(BaseModel):
    detail: str

## data ganti password
class ChangePassword(BaseModel):
    password_lama: str
    password_baru: str
    konfirmasi_password_baru: str
