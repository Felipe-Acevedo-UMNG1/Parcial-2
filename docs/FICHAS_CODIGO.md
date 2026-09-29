# Fichas de revisión de código

Base fija: `b757385b7f38da91c0bad9d4e69e56e074a6a806`. Solución: rama `acevedo_perez_velandia`.
Las líneas indicadas corresponden a esa base, no a la rama corregida.
Detección realizada: revisión manual del código y las pruebas locales citadas.
SonarQube, Bearer y ZAP **no se ejecutaron** en esta revisión; agregar su
resultado real a cada ficha, incluso si no detectan el problema.

Para obtener el diff verificable de cada archivo:

```sh
git diff b757385b7f38da91c0bad9d4e69e56e074a6a806 acevedo_perez_velandia -- RUTA_DEL_ARCHIVO
```

Las PoC siguientes son pasos pendientes para el laboratorio **propio** con
usuarios, tickets y contraseñas de prueba. No son resultados ya obtenidos.
Completar en cada ficha: fecha, grupo/nodo, captura antes/después, commit final,
herramienta/regla y explicación de por qué detectó o no detectó el caso.

## 1. SQLi en login — obligatoria

- **Clasificación:** OWASP A03:2021; CWE-89.
- **Ubicación/snippet:** `backend/app/main.py`, 74–78:
  `f"WHERE username = '{datos.username}'"`.
- **Causa e impacto:** un dato se interpreta como SQL. Puede seleccionar o
  construir una fila con identidad/hash controlados. Un simple `OR 1=1` no
  garantiza omitir la posterior comprobación de contraseña; no afirmar lo contrario.
- **Detección:** lectura manual encuentra la interpolación. La prueba local
  `test_login_uses_parameters_and_does_not_log_password` comprueba que la
  entrada con comilla viaja como parámetro y el login inválido devuelve 401.
- **PoC controlada:** en la base de laboratorio, enviar un username con UNION
  que produzca las cuatro columnas esperadas (`id, username, rol, password_hash`)
  para una cuenta de prueba y MD5 de una clave de prueba conocida. Comparar el
  token obtenido en la versión base con el rechazo 401 en la versión final.
- **Corrección/diff:** en ese archivo, consulta con `%s` y tupla de parámetros.
  Pendiente: evidencia contra MySQL real; el test no ejecuta SQL en un servidor.

## 2. Firma JWT desactivada — obligatoria

- **Clasificación:** A07:2021; CWE-347.
- **Ubicación/snippet:** `backend/app/security.py`, 33–44:
  `options={"verify_signature": False}` y rol tomado de las claims.
- **Causa e impacto:** el servidor acepta identidad y rol de un token no
  autenticado y sin vencimiento obligatorio; permite suplantación.
- **Detección:** revisión manual y `test_jwt_forged_and_expired_are_rejected`.
- **PoC controlada:** firmar un JWT de la cuenta de prueba con una clave distinta;
  invocar una ruta protegida. Comparar aceptación base/rechazo 401 final; repetir
  con token vencido y conservar un token válido como control positivo.
- **Corrección/diff:** HS256 con firma, `sub`, `iat`, `exp` obligatorios,
  vencimiento 30 minutos y rol obtenido de DB. Test local aprobado; API real pendiente.

## 3. IDOR de tickets — obligatoria

- **Clasificación:** A01:2021; CWE-639.
- **Ubicación/snippet:** `backend/app/main.py`, 103–108 y 121–127:
  `SELECT * FROM tickets WHERE id = %s` sin propietario; UPDATE también solo por ID.
- **Causa e impacto:** conocer el número permite leer o cambiar tickets ajenos.
- **Detección:** revisión manual; pruebas de rechazo de lectura/actualización
  ajenas y control positivo de actualización propia.
- **PoC controlada:** A crea un ticket; B intenta GET y PATCH sobre ese ID.
  Esperar 404 en ambos casos finales y estado intacto al consultar como A.
- **Corrección/diff:** `id = %s AND usuario_id = %s` en lectura y modificación.
  Tests locales aprobados; pendiente prueba con dos cuentas reales y capturas.

## 4. XSS en descripción — obligatoria

- **Clasificación:** A03:2021; CWE-79.
- **Ubicación/snippet:** `frontend/src/app/app.ts`, 140:
  `this.sanitizer.bypassSecurityTrustHtml(t.descripcion)`;
  `frontend/src/app/app.html`, 95: `[innerHTML]="descripcionHtml"`.
- **Causa e impacto:** se desactiva el saneamiento y se interpreta HTML no confiable;
  un ticket almacenado puede ejecutar código al abrirse.
- **Detección:** revisión manual de origen/salida y compilación de Angular.
- **PoC controlada:** crear un ticket con `<img src=x onerror="alert('prueba-XSS')">`.
  En la versión final se debe mostrar texto literal, sin elemento img ni alerta;
  verificar DOM además de CSP, porque CSP sola podría ocultar el fallo de código.
- **Corrección/diff:** eliminar SafeHtml/DomSanitizer e interpolar
  `{{ ticket.descripcion }}`. Además, desactivar `inlineCritical` en el build
  para evitar el `onload` inline incompatible con CSP. Build verificado;
  interacción del navegador y PoC completa pendientes.

## 5. SQLi en búsqueda

- **Clasificación:** A03:2021; CWE-89.
- **Ubicación/snippet:** `backend/app/main.py`, 96–100:
  `f"AND titulo LIKE '%{q}%' ORDER BY id DESC"`.
- **Causa e impacto:** un término puede alterar SQL y el filtro de propietario.
- **Detección:** lectura manual; test `test_search_scopes_owner_and_parameterizes_input`.
- **PoC controlada:** con dos cuentas y tickets desechables, buscar una cadena con
  comilla y `OR 1=1`; registrar que la versión final no devuelve tickets de otra cuenta.
- **Corrección/diff:** SQL constante, ID de sesión y `f"%{q}%"` enviados por separado.
  Test local aprobado; resultados MySQL reales pendientes.

## 6. Contraseñas MD5

- **Clasificación:** A02:2021; CWE-327 (también pertinente CWE-916).
- **Ubicación/snippet:** `backend/app/security.py`, 10–15:
  `hashlib.md5(password.encode()).hexdigest()`.
- **Causa e impacto:** hash rápido y sin sal; dos claves iguales dejan igual hash
  y facilitan ataques offline si alguien obtiene la tabla.
- **Detección:** revisión manual y test de Argon2 con sal y verificación.
- **PoC controlada:** crear dos cuentas con la misma clave de prueba; comparar
  igualdad de los hashes base y desigualdad final, sin publicar hashes reales.
- **Corrección/diff:** Argon2; columna de 255 caracteres y restablecimiento
  interactivo en `backend/app/reset_password.py`. MD5 antiguo se rechaza; no
  se convierte ciegamente un hash en otro. Test de conservación de ID aprobado;
  migración/registro en MySQL pendientes.

## 7. Contraseñas en logs

- **Clasificación:** A09:2021; CWE-532.
- **Ubicación/snippet:** `backend/app/main.py`, 59 y 80:
  `logger.warning(f"Login fallido para {datos.username} con clave {datos.password}")`.
- **Causa e impacto:** secretos se propagan a archivos, consola y SIEM.
- **Detección:** revisión manual y captura local de logs al fallar el login.
- **PoC controlada:** usar una contraseña marcador solo de laboratorio y buscarla
  en el log base/final. Debe desaparecer del final; sí deben existir IP y evento.
- **Corrección/diff:** evento `AUTH_FAILED`, usuario saneado, IP validada solo
  desde el proxy autorizado; rotación de logs. Tests de secreto y spoof de IP
  aprobados. Pendiente trazabilidad Cloudflare → Nginx → backend → Wazuh.

## 8. Exposición de configuración

- **Clasificación:** A05:2021; CWE-200.
- **Ubicación/snippet:** `backend/app/main.py`, 43–52:
  `"db_password": config.DB_PASSWORD`, `"env": dict(os.environ)`.
- **Causa e impacto:** endpoint público sin autorización entrega variables y claves.
- **Detección:** revisión manual del endpoint y test final de respuesta 404.
- **PoC controlada:** consultar `/debug/config` en base con secretos desechables;
  conservar una captura censurada. Después comprobar 404 en la misma ruta final.
- **Corrección/diff:** eliminar endpoint. Test local aprobado; ruta real pendiente.

## 9. Persistencia y registro de JWT

- **Clasificación:** A07:2021; CWE-922; el log también corresponde a CWE-532.
- **Ubicación/snippet:** `frontend/src/app/services/api.service.ts`, 40–44:
  `localStorage.setItem('token', res.access_token)` y `console.log(...res.access_token)`.
- **Causa e impacto:** el token permanece tras cerrar pestañas y es accesible a
  cualquier script del origen; la consola añade otra exposición.
- **Detección:** revisión manual. El riesgo aumenta con XSS; memoria no elimina
  todos los riesgos de un script malicioso, por eso se corrige también la salida HTML.
- **PoC controlada:** revisar Application/Local Storage y Console antes/después;
  salir y recargar. En la final no debe persistir un token ni imprimirse.
- **Corrección/diff:** token solo en memoria, borrado de las tres claves antiguas
  al iniciar y limpieza al cerrar sesión. Build aprobado; DevTools pendiente.

## Otros hallazgos

CORS comodín en `backend/app/main.py` 21–27 (A05/CWE-942) fue retirado usando
proxy del mismo origen. El listado admin en 137 incluía `password_hash` y ahora
lo omite. Los secretos de la base se documentan en `ORIGEN_BASE.txt`; no se
reproducen para fabricar una evidencia. No afirmar que el repositorio demuestra
un antes/después de esas claves: fueron excluidas durante la importación.

Taxonomía de referencia: https://top10.owasp.org/2021/ . La asignación a cada
categoría/CWE es el análisis del código del proyecto, no un resultado de escáner.
