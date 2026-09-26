import logging
import os
import re
from ipaddress import ip_address

from fastapi import Depends, FastAPI, HTTPException, Request

from app import config
from app.database import execute, fetch_all, fetch_one
from app.schemas import EstadoIn, LoginIn, RegistroIn, TicketIn
from app.security import crear_token, hash_password, usuario_actual, verify_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("mesa_ayuda")
if os.getenv("APP_LOG_FILE"):
    logger.addHandler(logging.FileHandler(os.environ["APP_LOG_FILE"]))

app = FastAPI(
    title="Mesa de Ayuda API",
    description="API de la Mesa de Ayuda — Seguridad Informática UMNG 2026-II",
    version="2.0.0",
)

# ---------------------------------------------------------------- General

@app.get("/health", tags=["General"])
def health():
    return {"estado": "ok", "grupo": config.GRUPO_CODIGO, "version": app.version}


# ---------------------------------------------------------------- Autenticación

@app.post("/auth/registro", tags=["Autenticación"])
def registro(datos: RegistroIn):
    logger.info("Registro de usuario: %s", datos.username)
    existe = fetch_one("SELECT id FROM usuarios WHERE username = %s", (datos.username,))
    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    nuevo_id = execute(
        "INSERT INTO usuarios (username, email, password_hash) VALUES (%s, %s, %s)",
        (datos.username, datos.email, hash_password(datos.password)),
    )
    return fetch_one(
        "SELECT id, username, email, rol FROM usuarios WHERE id = %s", (nuevo_id,)
    )


@app.post("/auth/login", tags=["Autenticación"])
def login(datos: LoginIn, request: Request):
    usuario = fetch_one(
        "SELECT id, username, rol, password_hash FROM usuarios WHERE username = %s",
        (datos.username,),
    )
    if not usuario or not verify_password(datos.password, usuario["password_hash"]):
        source = request.client.host if request.client else "unknown"
        if source == config.TRUSTED_PROXY_IP:
            forwarded = request.headers.get("x-real-ip", "")
            try:
                source = str(ip_address(forwarded))
            except ValueError:
                pass
        safe_user = re.sub(r"[^A-Za-z0-9_.-]", "_", datos.username)[:50]
        logger.warning("AUTH_FAILED source_ip=%s username=%s", source, safe_user)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return {"access_token": crear_token(usuario), "token_type": "bearer", "rol": usuario["rol"]}


# ---------------------------------------------------------------- Tickets

@app.get("/tickets", tags=["Tickets"])
def mis_tickets(usuario: dict = Depends(usuario_actual)):
    return fetch_all(
        "SELECT * FROM tickets WHERE usuario_id = %s ORDER BY id DESC", (usuario["id"],)
    )


@app.get("/tickets/buscar", tags=["Tickets"])
def buscar_tickets(q: str, usuario: dict = Depends(usuario_actual)):
    return fetch_all(
        "SELECT * FROM tickets WHERE usuario_id = %s AND titulo LIKE %s ORDER BY id DESC",
        (usuario["id"], f"%{q}%"),
    )


@app.get("/tickets/{ticket_id}", tags=["Tickets"])
def ver_ticket(ticket_id: int, usuario: dict = Depends(usuario_actual)):
    ticket = fetch_one(
        "SELECT * FROM tickets WHERE id = %s AND usuario_id = %s",
        (ticket_id, usuario["id"]),
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@app.post("/tickets", tags=["Tickets"])
def crear_ticket(datos: TicketIn, usuario: dict = Depends(usuario_actual)):
    nuevo_id = execute(
        "INSERT INTO tickets (titulo, descripcion, prioridad, usuario_id) "
        "VALUES (%s, %s, %s, %s)",
        (datos.titulo, datos.descripcion, datos.prioridad, usuario["id"]),
    )
    return fetch_one("SELECT * FROM tickets WHERE id = %s", (nuevo_id,))


@app.patch("/tickets/{ticket_id}/estado", tags=["Tickets"])
def cambiar_estado(ticket_id: int, datos: EstadoIn, usuario: dict = Depends(usuario_actual)):
    ticket = fetch_one(
        "SELECT * FROM tickets WHERE id = %s AND usuario_id = %s",
        (ticket_id, usuario["id"]),
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    execute(
        "UPDATE tickets SET estado = %s WHERE id = %s AND usuario_id = %s",
        (datos.estado, ticket_id, usuario["id"]),
    )
    return fetch_one(
        "SELECT * FROM tickets WHERE id = %s AND usuario_id = %s",
        (ticket_id, usuario["id"]),
    )


# ---------------------------------------------------------------- Administración

@app.get("/admin/usuarios", tags=["Administración"])
def listar_usuarios(usuario: dict = Depends(usuario_actual)):
    if usuario["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return fetch_all(
        "SELECT id, username, email, rol, creado_en FROM usuarios"
    )
