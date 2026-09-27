"""Regresiones de las fallas obligatorias del examen, sin infraestructura externa."""
import importlib
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
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
    assert not security.verify_password("una-clave", "5f4dcc3b5aa765d61d8327deb882cf99")


@pytest.mark.parametrize("peer,trusted,forwarded,expected", [
    ("100.64.0.30", "100.64.0.30", "203.0.113.5", "203.0.113.5"),
    ("100.64.0.99", "100.64.0.30", "203.0.113.5", "100.64.0.99"),
    ("100.64.0.30", "100.64.0.30", "invalid, forged", "100.64.0.30"),
])
def test_failed_login_trusts_only_frontend_peer(monkeypatch, caplog, peer, trusted, forwarded, expected):
    monkeypatch.setattr(main.config, "TRUSTED_PROXY_IP", trusted)
    monkeypatch.setattr(main, "fetch_one", lambda *args: None)
    with TestClient(main.app, client=(peer, 12345)) as client:
        response = client.post("/auth/login", headers={"X-Real-IP": forwarded},
                               json={"username": "demo\nINJECT", "password": "not-logged"})
    assert response.status_code == 401
    assert f"source_ip={expected} username=demo_INJECT" in caplog.text
    assert "not-logged" not in caplog.text


def test_ready_reports_database_outage_without_secrets(monkeypatch, caplog):
    def unavailable(*args):
        raise RuntimeError("password=PRIVATE_DB_SECRET")
    monkeypatch.setattr(main, "fetch_one", unavailable)
    with TestClient(main.app) as client:
        assert client.get("/health").status_code == 200
        response = client.get("/ready")
    assert response.status_code == 503
    assert "PRIVATE_DB_SECRET" not in response.text + caplog.text
    monkeypatch.setattr(main, "fetch_one", lambda *args: {"disponible": 1})
    with TestClient(main.app) as client:
        assert client.get("/ready").json()["database"] == "ok"


def test_search_scopes_owner_and_parameterizes_input(monkeypatch):
    queries = []
    def search(sql, params):
        queries.append((sql, params))
        return []
    monkeypatch.setattr(main, "fetch_all", search)
    main.app.dependency_overrides[security.usuario_actual] = lambda: {"id": 7, "rol": "usuario"}
    try:
        with TestClient(main.app) as client:
            assert client.get("/tickets/buscar", params={"q": "' OR 1=1 --"}).status_code == 200
            assert client.get("/admin/usuarios").status_code == 403
            assert client.get("/debug/config").status_code == 404
    finally:
        main.app.dependency_overrides.clear()
    assert queries[0][1] == (7, "%' OR 1=1 --%")
    assert "OR 1=1" not in queries[0][0]


def test_owner_can_update_own_ticket(monkeypatch):
    ticket = {"id": 99, "usuario_id": 7, "estado": "abierto"}
    monkeypatch.setattr(main, "fetch_one", lambda *args: dict(ticket))
    def update(sql, params):
        assert params == ("cerrado", 99, 7)
        ticket["estado"] = params[0]
    monkeypatch.setattr(main, "execute", update)
    main.app.dependency_overrides[security.usuario_actual] = lambda: {"id": 7, "rol": "usuario"}
    try:
        with TestClient(main.app) as client:
            assert client.get("/tickets/99").status_code == 200
            assert client.patch("/tickets/99/estado", json={"estado": "cerrado"}).json()["estado"] == "cerrado"
    finally:
        main.app.dependency_overrides.clear()


def test_reset_password_preserves_user_and_uses_argon2(monkeypatch):
    reset = importlib.import_module("app.reset_password")
    monkeypatch.setattr("sys.argv", ["reset_password", "ana"])
    monkeypatch.setattr(reset, "fetch_one", lambda *args: {"id": 7})
    monkeypatch.setattr(reset, "getpass", lambda *args: "nueva-clave-segura-de-prueba")
    changes = []
    monkeypatch.setattr(reset, "execute", lambda sql, params: changes.append((sql, params)))
    reset.main()
    assert changes[0][0] == "UPDATE usuarios SET password_hash = %s WHERE id = %s"
    hashed, user_id = changes[0][1]
    assert user_id == 7 and security.verify_password("nueva-clave-segura-de-prueba", hashed)
