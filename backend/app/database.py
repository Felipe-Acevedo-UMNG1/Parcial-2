import ssl

import pymysql
from pymysql.cursors import DictCursor

from app import config


def get_connection():
    if not config.DB_SSL_CA:
        raise RuntimeError("Configure DB_SSL_CA para verificar TLS con MySQL")
    tls = ssl.create_default_context(cafile=config.DB_SSL_CA)
    return pymysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        db=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        ssl=tls,
        ssl_verify_identity=True,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )


def fetch_one(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute(sql, params=None):
    """Ejecuta un INSERT/UPDATE y devuelve el id afectado."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid
