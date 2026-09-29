# Bono WireGuard — grupo 2

Subred asignada por el docente: **10.77.2.0/24**. Se registra también en
`../parametros-grupo.json`. Usarla únicamente si el equipo opta por el bono.

Esta actualización registra el parámetro; no instala ni activa un túnel.
La red Tailscale obligatoria conserva sus IPs reales `100.x`, obtenidas con
`tailscale ip -4`. La subred del bono no reemplaza esas IPs en `.env`, MySQL,
ACL o `network.example.json`.

Para completar el bono faltan elegir el hub público separado de security local,
definir IPs de peers dentro de la subred sin duplicados, crear claves privadas
en cada equipo, configurar sus claves públicas/endpoint/AllowedIPs, ajustar
firewall y registrar handshake y conectividad reales. No guardar claves
privadas en Git. Seguir los requisitos del bono de `Parcial 2.html`.
