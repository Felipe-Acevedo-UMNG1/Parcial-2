"""Cinco peticiones al login PROPIO. No sigue redirecciones ni reintenta."""
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


base = os.environ["OWN_LOGIN_URL"].rstrip("/")
parsed = urllib.parse.urlsplit(base)
if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
    sys.exit("OWN_LOGIN_URL debe ser solo el origen propio, por ejemplo https://su-tunel.example")
opener = urllib.request.build_opener(NoRedirect)
failures = 0
for i in range(5):
    request = urllib.request.Request(
        base + "/api/auth/login",
        data=b'{"username":"cuenta_demo_inexistente","password":"intento_invalido"}',
        headers={"Content-Type": "application/json"},
    )
    try:
        with opener.open(request, timeout=10) as response:
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
    except urllib.error.URLError as exc:
        sys.exit(f"No se pudo conectar: {exc.reason}")
    print(f"Intento {i + 1}: HTTP {status}")
    failures += status == 401
if failures != 5:
    sys.exit("Prueba incompleta: se necesitan cinco 401. Un 429 es Nginx, no un fallo registrado por la API. Espere 60 s antes de repetir.")
print("Cinco fallos registrados por la API. Verifique srcip y regla 100121, nivel 10, en Wazuh.")
