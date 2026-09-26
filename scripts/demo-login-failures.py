"""Cinco logins fallidos controlados contra el sistema propio; usar solo en laboratorio."""
import os
import urllib.error
import urllib.request

url = os.environ["OWN_LOGIN_URL"].rstrip("/") + "/api/auth/login"
for i in range(5):
    payload = b'{"username":"cuenta_demo","password":"intento_invalido"}'
    request = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(request, timeout=10)
    except urllib.error.HTTPError as exc:
        print(f"Intento {i + 1}: HTTP {exc.code}")
