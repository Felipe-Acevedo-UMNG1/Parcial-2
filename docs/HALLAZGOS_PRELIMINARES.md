# Hallazgos preliminares sobre las bases del examen

Base: rama `v-base`. Solución: rama `acevedo`. OWASP Top 10:2021. Estas fichas
registran revisión del código y pruebas locales; el impacto controlado sobre el
sistema desplegado y los informes de herramientas siguen pendientes.

| # | Ubicación en base | Riesgo y causa raíz | Corrección | Verificación actual / pendiente |
|---|---|---|---|---|
| 1 ⭐ A03 / CWE-89 | `backend/app/main.py`, login | Usuario concatenado en SQL; comilla altera la consulta y puede eludir controles o leer registros. | Parámetros `%s`. | Prueba local de entrada `\' OR 1=1 --`; faltan prueba en VM y SAST. |
| 2 A03 / CWE-89 | `backend/app/main.py`, buscar | `q` se concatena en `LIKE`; puede modificar filtro de propietario. | SQL parametrizado y valor `%q%` aparte. | Revisión del diff; falta prueba con base real. |
| 3 ⭐ A07 / CWE-347 | `backend/app/security.py`, `usuario_actual` | `verify_signature=False` admite rol y sub falsificados. | Firma HS256, `exp`, campos obligatorios y usuario consultado en DB. | Prueba local de token falsificado y expirado; falta prueba por API real. |
| 4 A02 / CWE-327 | `backend/app/security.py`, contraseña | MD5 rápido sin sal permite ataques offline sobre hashes. | Argon2 para registros nuevos; ampliar columna a 255. | Prueba local de dos hashes distintos; restablecer claves MD5 existentes. |
| 5 ⭐ A01 / CWE-639 | `backend/app/main.py`, GET/PATCH ticket | La selección por ID ignora `usuario_id`; permite leer/cambiar ticket ajeno. | Exigir ID y propietario en lectura y actualización. | Dos pruebas locales con respuesta 404; falta dos usuarios reales. |
| 6 A09 / CWE-532 | `backend/app/main.py`, logs | Registro y login fallido escriben contraseña; filtración a operadores y Wazuh. | Solo evento, IP y usuario validado, sin clave. | Prueba local verifica que la clave no aparece; falta alerta D2. |
| 7 A05 / CWE-200 | `backend/app/main.py`, `/debug/config` | Endpoint sin autenticación filtra contraseña, JWT y todo el entorno. | Ruta eliminada. | Revisar 404 en despliegue y ZAP. |
| 8 A05 / CWE-942 | `backend/app/main.py`, CORS | Origen y método `*` sin necesidad; aumenta superficie del navegador. | CORS retirado; proxy mismo origen `/api`. | Build y Network del navegador pendientes. |
| 9 ⭐ A03 / CWE-79 | `frontend/src/app/app.ts` y `app.html` | `bypassSecurityTrustHtml` desactiva saneamiento de descripción. | Interpolación de texto con `white-space: pre-wrap`. | Build; pendiente ticket con texto HTML inocuo en navegador. |
| 10 A07 / CWE-922 | `frontend/src/app/services/api.service.ts` | JWT en `localStorage` persiste y es accesible a scripts; además se imprime en consola. | Token en memoria, salida de sesión lo descarta. | Revisión del código; pendiente DevTools: no token persistido. |
| 11 A05 / CWE-798 | `backend/env_del_examen.txt` y `config.py` | Base trae contraseña root y clave JWT fija, recuperables desde Git. | No importar archivo; requerir secreto desde entorno; `.gitignore`. | Revisar historial propio; rotar si esas claves se usaron realmente. |

Adicionales: el endpoint admin entregaba `password_hash`; la corrección omite
esa columna. El contenedor base corría como root, con `--reload` y `ports` en
todas las interfaces; la corrección elimina esas exposiciones.

Para el informe IEEE, ampliar **cada** ficha con línea del commit base, diff,
causa, PoC controlada en la infraestructura del equipo, herramienta que detecta
o no detecta el caso (SonarQube/Bearer/ZAP o revisión manual) y resultado real
posterior. No atribuir a una herramienta hallazgos que no produjo.
