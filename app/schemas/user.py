from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    nama: str
    password: str
    id_departemen: int
    id_pm: int | None = None


class UserOut(BaseModel):
    id_user: int
    username: str
    nama: str
    role: str
    id_departemen: int

    model_config = {"from_attributes": True}


class PMOut(BaseModel):
    id_user: int
    username: str
    nama: str

    model_config = {"from_attributes": True}


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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
