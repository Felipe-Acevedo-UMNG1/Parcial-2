import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "33062"))
DB_NAME = os.getenv("DB_NAME", "mesa_ayuda")
DB_USER = os.getenv("DB_USER", "app_mesa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSL_CA = os.getenv("DB_SSL_CA", "")

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
if len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET debe tener al menos 32 caracteres aleatorios")

# Parámetros del grupo 2, confirmados en el PDF del docente el 29/09/2026.
GRUPO_CODIGO = os.getenv("GRUPO_CODIGO", "SI26-G02")
APP_PORT = int(os.getenv("APP_PORT", "8102"))
TRUSTED_PROXY_IP = os.getenv("TRUSTED_PROXY_IP", "")
