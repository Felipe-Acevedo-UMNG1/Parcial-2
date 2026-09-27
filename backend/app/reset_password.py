"""Restablecimiento local: python -m app.reset_password USUARIO.

Ejecutar en el contenedor con una terminal. No recibe claves como argumentos
ni convierte un MD5 en Argon2: pide una contraseña NUEVA al administrador.
"""
import argparse
from getpass import getpass

from app.database import execute, fetch_one
from app.security import hash_password


def main():
    parser = argparse.ArgumentParser(description="Restablecer clave con Argon2")
    parser.add_argument("username")
    args = parser.parse_args()
    user = fetch_one("SELECT id FROM usuarios WHERE username = %s", (args.username,))
    if not user:
        parser.exit(1, "Usuario inexistente. No se modificó la base.\n")
    password = getpass("Nueva contraseña (12–128 caracteres): ")
    confirm = getpass("Repítala: ")
    if not 12 <= len(password) <= 128 or password != confirm:
        parser.exit(1, "Longitud inválida o contraseñas diferentes. Sin cambios.\n")
    execute("UPDATE usuarios SET password_hash = %s WHERE id = %s",
            (hash_password(password), user["id"]))
    print("Contraseña restablecida; usuario, rol y tickets conservados.")


if __name__ == "__main__":
    main()
