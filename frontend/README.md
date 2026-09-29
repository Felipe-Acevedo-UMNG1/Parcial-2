# Cliente Angular y proxy Nginx

La base se conserva en `v-base`; las correcciones están en `acevedo_perez_velandia`.
Guía completa: [../INSTRUCCIONES_PARCIAL_2.txt](../INSTRUCCIONES_PARCIAL_2.txt).

El backend del grupo SI26-G02 escucha en 8102; `.env.example` y el proxy local
ya usan ese puerto. Si existe `.env`, actualizar APP_PORT=8102 conservando la IP.

1. Copiar `.env.example` a `.env` con la IP Tailscale del backend y el puerto
   API real del grupo.
2. En `frontend/`, ejecutar `docker compose up -d --build`. La imagen usa
   [../infra/nginx.conf](../infra/nginx.conf), que recibe esos valores como
   plantilla de Nginx al arrancar.
3. En `sg-frontend`, apuntar cloudflared a `http://127.0.0.1:8080`. El
   puerto solo escucha en loopback del host, sin entrada pública directa.
4. Verificar URL HTTPS, peticiones `/api/...`, headers, limitación de login,
   CSP y la consola del navegador con casos de uso reales.

Para desarrollo local con API en `127.0.0.1:8102`: `npm ci`, `npm start`.
`proxy.conf.json` reenvía `/api` sin CORS. Para comprobar compilación:
`npm run build -- --configuration production`.

El patrón de desarrollo es `/api/**`. Producción desactiva CSS crítico inline
para no generar manejadores `onload` incompatibles con `script-src 'self'`.
El proxy público bloquea Swagger; consultar `/docs` directamente por Tailscale.

El token permanece en memoria y se pierde al recargar la página; el usuario
inicia sesión nuevamente. Las descripciones se muestran como texto seguro.
