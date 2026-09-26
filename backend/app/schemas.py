from pydantic import BaseModel, Field


class RegistroIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    email: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=12, max_length=128)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str


class TicketIn(BaseModel):
    titulo: str = Field(min_length=1, max_length=150)
    descripcion: str = Field(min_length=1, max_length=10000)
    prioridad: str = Field(default="media", pattern=r"^(baja|media|alta)$")


class EstadoIn(BaseModel):
    estado: str = Field(pattern=r"^(abierto|en_progreso|cerrado)$")
