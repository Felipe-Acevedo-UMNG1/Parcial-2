# Parcial 2 — Mesa de Ayuda

Trabajo del examen aplicado de Seguridad Informática (UMNG, 2026-II).

- [ACTUALIZACION_SI26_G02.txt](ACTUALIZACION_SI26_G02.txt): parámetros confirmados, cambios y pendientes al 29/09/2026.
- [INSTRUCCIONES_PARCIAL_2.txt](INSTRUCCIONES_PARCIAL_2.txt): pasos, cambios y pendientes.
- [docs/REVISION.md](docs/REVISION.md): comparación con el HTML y límites de la validación.
- [infra/OPERACION.md](infra/OPERACION.md): comandos por nodo, restauración y análisis.
- [ORIGEN_BASE.txt](ORIGEN_BASE.txt): origen de las bases y excepciones por secretos.
- `backend/`: API FastAPI corregida y pruebas de regresión.
- `frontend/`: cliente Angular, Nginx mediante `infra/nginx.conf`.
- `infra/`: plantillas para ACL, base de datos, respaldo y Wazuh.
- `docs/`: guía de informes y hallazgos preliminares; las evidencias reales
  deben añadirse después de desplegar los nodos.

**Grupo 2:** Felipe Ricardo Acevedo Torres, Dustyn Fabian Pérez Rodríguez y
Laura Sofia Velandia Sarmiento. Código **SI26-G02**, API **8102**, MySQL
**33062**, subred del bono WireGuard **10.77.2.0/24**. Datos confirmados en el
PDF del docente; detalle en [infra/parametros-grupo.json](infra/parametros-grupo.json).

**Estado:** código y plantillas preparados con los parámetros asignados. Faltan
las IPs Tailscale, credenciales privadas y el despliegue con evidencias reales.
Nunca subir `.env`, certificados privados, tokens, claves ni capturas con contraseñas.

La rama `v-base` conserva la importación de los dos proyectos sin las
credenciales expuestas en la base. La rama de trabajo es
`acevedo_perez_velandia`; `acevedo` se conserva como referencia anterior.
Falta crear una *etiqueta Git* `v-base` sobre la importación documentada y
explicar al docente las excepciones de origen; el tag no cambia esas excepciones.
