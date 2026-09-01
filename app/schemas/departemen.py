from pydantic import BaseModel


class DepartemenBase(BaseModel):
    nama_departemen: str


class DepartemenCreate(DepartemenBase):
    pass


class DepartemenUpdate(BaseModel):
    nama_departemen: str


class DepartemenOut(DepartemenBase):
    id_departemen: int

    model_config = {"from_attributes": True}
