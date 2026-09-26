# Parcial 2 — Mesa de Ayuda

Trabajo del examen aplicado de Seguridad Informática (UMNG, 2026-II).

- [INSTRUCCIONES_PARCIAL_2.txt](INSTRUCCIONES_PARCIAL_2.txt): pasos, cambios y pendientes.
- [ORIGEN_BASE.txt](ORIGEN_BASE.txt): origen de las bases y excepciones por secretos.
- `backend/`: API FastAPI corregida y pruebas de regresión.
- `frontend/`: cliente Angular, Nginx mediante `infra/nginx.conf`.
- `infra/`: plantillas para ACL, base de datos, respaldo y Wazuh.
- `docs/`: guía de informes y hallazgos preliminares; las evidencias reales
  deben añadirse después de desplegar los nodos.

**Estado:** código y plantillas preparados; no hay infraestructura del grupo
ni parámetros del docente disponibles en este repositorio. Nunca subir `.env`,
certificados privados, tokens, claves ni capturas con contraseñas.

La rama `v-base` conserva la importación de los dos proyectos sin las
credenciales expuestas en la base. La rama `acevedo` contiene las correcciones.
Para cumplir literalmente el enunciado falta crear una *etiqueta Git* `v-base`
sobre el commit de esa rama y renombrar la rama de trabajo cuando se confirmen
los apellidos paternos de todos los integrantes.
