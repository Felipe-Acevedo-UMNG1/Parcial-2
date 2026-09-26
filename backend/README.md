# API FastAPI

La base se conserva en la rama `v-base`; las correcciones están en `acevedo`.
Guía completa: [../INSTRUCCIONES_PARCIAL_2.txt](../INSTRUCCIONES_PARCIAL_2.txt).

1. Ejecutar `infra/db/mesa_ayuda.sql` con administrador local. El usuario
   `app_mesa` recibe solo SELECT, INSERT, UPDATE y DELETE sobre esa base.
2. Crear un certificado MySQL de servidor con CA propia y SAN que coincida
   con `DB_HOST`; copiar la CA pública a `secrets/db-ca.pem` en este directorio.
3. Copiar `.env.example` a `.env` y rellenar los datos reales del grupo.
   `JWT_SECRET` se puede generar con `openssl rand -hex 32`.
4. En el host del backend: `sudo install -d -o 10001 -g 10001 -m 0750
   /var/log/mesa_ayuda`. Después ejecutar `docker compose up -d --build`.
5. Verificar `/health`, una conexión permitida y otra bloqueada desde la
   tailnet. El puerto Docker se enlaza a la IP Tailscale; proteger también
   DOCKER-USER de acuerdo con el firewall del host.

El contenedor no crea tablas: iniciar `app_mesa` con privilegios DML es
incompatible con crear esquemas en cada arranque. Los usuarios antiguos cuyo
hash sea MD5 deberán cambiar su contraseña para poder acceder.

Pruebas locales: `pip install -r requirements.txt httpx pytest` y
`pytest -q` (sin MySQL ni VMs). El token se emite por 30 minutos y requiere
JWT_SECRET de al menos 32 caracteres. La API no habilita CORS: el frontend
usa el mismo origen mediante `/api`.
