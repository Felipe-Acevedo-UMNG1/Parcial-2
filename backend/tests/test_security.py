"""Regresiones de las fallas obligatorias del examen, sin infraestructura externa."""
import importlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SECRET", "pruebas-una-clave-aleatoria-de-32-caracteres")
main = importlib.import_module("app.main")
security = importlib.import_module("app.security")


def test_jwt_forged_and_expired_are_rejected(monkeypatch):
    monkeypatch.setattr(security, "fetch_one", lambda *args: {"id": 1, "username": "ana", "rol": "usuario"})
    now = datetime.now(timezone.utc)
    claims = {"sub": "1", "iat": now, "exp": now + timedelta(minutes=10)}
    forged = jwt.encode(claims, "attacker-key-that-is-more-than-32-bytes", algorithm="HS256")
    expired = jwt.encode({**claims, "exp": now - timedelta(seconds=5)}, security.config.JWT_SECRET, algorithm="HS256")
    for token in (forged, expired):
        try:
            security.usuario_actual("Bearer " + token)
            assert False, "El token inseguro fue aceptado"
        except Exception as exc:
            assert exc.status_code == 401
    assert security.usuario_actual("Bearer " + security.crear_token({"id": 1}))["id"] == 1


def test_login_uses_parameters_and_does_not_log_password(monkeypatch, caplog):
    captured = []
    def fake_fetch(sql, params):
        captured.append((sql, params))
        return None
    monkeypatch.setattr(main, "fetch_one", fake_fetch)
    with TestClient(main.app) as client:
        response = client.post("/auth/login", json={"username": "' OR 1=1 --", "password": "NO_LOG_THIS_SECRET"})
    assert response.status_code == 401
    assert captured[0][1] == ("' OR 1=1 --",)
    assert "OR 1=1" not in captured[0][0]
    assert "NO_LOG_THIS_SECRET" not in caplog.text


def test_ticket_ownership_applies_to_read_and_update(monkeypatch):
    calls = []
    def fake_fetch(sql, params):
        calls.append((sql, params))
        return None  # Ticket de otro usuario: no debe revelarse ni modificarse.
    monkeypatch.setattr(main, "fetch_one", fake_fetch)
    monkeypatch.setattr(main, "execute", lambda *args: (_ for _ in ()).throw(AssertionError("modificación ajena")))
    main.app.dependency_overrides[security.usuario_actual] = lambda: {"id": 7, "rol": "usuario"}
    try:
        with TestClient(main.app) as client:
            assert client.get("/tickets/99").status_code == 404
            assert client.patch("/tickets/99/estado", json={"estado": "cerrado"}).status_code == 404
    finally:
        main.app.dependency_overrides.clear()
    assert all(params == (99, 7) and "usuario_id = %s" in sql for sql, params in calls)


def test_password_hash_is_salted_and_verified():
    a = security.hash_password("una-clave-fuerte-de-prueba")
    b = security.hash_password("una-clave-fuerte-de-prueba")
    assert a != b and a.startswith("$argon2")
    assert security.verify_password("una-clave-fuerte-de-prueba", a)
    assert not security.verify_password("otra-clave", a)
