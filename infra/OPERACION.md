# Operación de las plantillas

Anexo técnico de `INSTRUCCIONES_PARCIAL_2.txt`. Ejecutar únicamente en las VMs
del grupo, desde la raíz de este repositorio, salvo que se indique otra carpeta.
Los textos `<...>` se reemplazan con valores auténticos; no son comandos listos
para pegar. Usar Ubuntu 24.04 y MySQL 8 para estas plantillas. No se han aplicado
en VMs durante esta revisión.

## Red, arranque y firewall

1. Completar `infra/network.example.json` en una copia `red.private.json` con
   las IPv4 de `tailscale ip -4`, PCs y puertos. Completar/aplicar la ACL en el
   panel de Tailscale. Todos los PCs administradores deben estar en el grupo ACL.
2. En **cada VM**, generar el firewall cambiando `backend` por su rol:

   ```sh
   python3 infra/firewall.py backend red.private.json > firewall.generated.nft
   sudo nft -c -f firewall.generated.nft
   sudo install -m 600 firewall.generated.nft /etc/examen-firewall.nft
   sudo install -m 644 infra/systemd/examen-firewall.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now examen-firewall.service
   sudo nft list table inet examen
   ```

   Aplicar desde la consola de la VM y mantenerla abierta hasta comprobar una
   segunda conexión SSH por Tailscale. Se usa **nftables**, permitido por el HTML;
   no activar además UFW ni un servicio que ejecute `flush ruleset`. Solo se
   renueva la tabla `examen`. INPUT deniega por defecto; permite loopback,
   respuestas, ICMP de diagnóstico y los servicios autorizados en `tailscale0`.
   FORWARD también filtra puertos Docker después de DNAT (443 se convierte en
   5601 en Wazuh). No habilitar exit node ni subnet routing en estas VMs.
   Validar de nuevo después de reiniciar Docker/Tailscale y la VM. La ACL y el
   firewall deben probarse por separado; un rechazo de ACL no demuestra nftables.
   Para recuperación desde consola: `sudo nft delete table inet examen`, corregir
   el archivo y reiniciar el servicio antes de continuar la exposición.
3. Evitar que MySQL o Docker intenten enlazarse antes de tener IP Tailscale:

   ```sh
   sudo install -m 755 infra/wait-tailscale-ip.sh /usr/local/sbin/wait-tailscale-ip
   sudoedit /etc/examen-node.env
   ```

   Escribir `TAILSCALE_NODE_IP=<IP de esta VM>` sin espacios. En db usar
   `SERVICIO=mysql`; en backend, frontend y security usar `SERVICIO=docker`:

   ```sh
   sudo install -d /etc/systemd/system/$SERVICIO.service.d
   sudo install -m 644 infra/systemd/tailscale-wait.conf /etc/systemd/system/$SERVICIO.service.d/tailscale.conf
   sudo systemctl daemon-reload
   ```

   El script espera hasta 120 s; si falla, revisar `tailscale status`, la IP
   configurada y `journalctl -u "$SERVICIO"`. El reinicio se hace al completar la
   configuración del servicio, no mientras se prepara MySQL.

## MySQL y certificados — sg-db

1. Instalar `mysql-server age openssl`. Ejecutar `sudo mysql_secure_installation`.
   Conservar root únicamente local y eliminar cuentas anónimas. Crear TLS:

   ```sh
   sudo bash infra/db/create-tls.sh <IP_DB>
   sudo cp infra/db/mysqld.cnf.template /etc/mysql/mysql.conf.d/mesa-ayuda.cnf
   sudoedit /etc/mysql/mysql.conf.d/mesa-ayuda.cnf
   sudo mysqld --validate-config
   sudo systemctl restart mysql
   sudo mysql < infra/db/mesa_ayuda.sql
   ```

   Certificado válido 90 días, SAN igual a IP_DB: usar esa misma IP en DB_HOST.
   Copiar **solo** `ca.pem` por canal autenticado al backend y verificar huella
   SHA-256 en origen/destino. La clave de la CA queda en `/root/mesa-ca`, la clave
   de servidor solo en db. El script no sobrescribe certificados existentes.
   Respaldar CA y programar renovación si el laboratorio dura más de 90 días.
2. Copiar `grants.mysql.template.sql` a un archivo fuera de Git con permisos
   600. Editar IP_BACKEND exacta y una contraseña nueva. Aplicar con `sudo mysql`.
   Si el usuario ya existe, revisar `SHOW GRANTS` y usar `ALTER USER` para cambiar
   clave/autenticación/TLS; retirar privilegios antiguos antes del GRANT mínimo.
   Nunca crear `app_mesa@'%'`. La app no recibe CREATE, ALTER, DROP ni GRANT.
3. Comprobar en db:

   ```sql
   SELECT user,host,plugin FROM mysql.user;
   SHOW VARIABLES WHERE Variable_name IN ('port','bind_address','require_secure_transport','general_log','log_error_verbosity');
   SHOW GRANTS FOR 'app_mesa'@'<IP_BACKEND>';
   ```

   Desde backend, usar cliente MySQL con `--host=<IP_DB> --port=<DB_PORT>
   --user=app_mesa --password --ssl-mode=VERIFY_IDENTITY --ssl-ca=<CA pública>`.
   Ejecutar `SHOW STATUS LIKE 'Ssl_cipher';`: debe tener cifrado. La misma
   conexión con `--ssl-mode=DISABLED` debe fallar; `CREATE TABLE` debe denegarse.
   Un login fallido debe aparecer en `/var/log/mysql/error.log`; `general_log`
   permanece OFF. `ss -lntp` no debe mostrar MySQL en 0.0.0.0, 3306 ni 33060.
4. Si ya había usuarios MD5: hacer respaldo y ejecutar
   `sudo mysql < infra/db/migrate-passwords.sql`. Por cada usuario listado,
   ejecutar en **backend/**: `docker compose exec backend python -m
   app.reset_password USUARIO`. Pide dos veces una contraseña nueva sin mostrarla;
   preserva ID, rol y tickets. No se puede recuperar una contraseña a partir de MD5.

## Respaldo y restauración — sg-db

1. En un PC confiable: `age-keygen -o mesa-backup.key`. Guardar la clave privada
   fuera del repositorio y copiar únicamente su clave pública `age1...` a
   `/etc/mesa-backup.env` como `AGE_RECIPIENT=age1...` (archivo root, modo 600).
2. Como administrador MySQL local, crear `backup_mesa@localhost` con
   `caching_sha2_password`, contraseña nueva y únicamente SELECT, SHOW VIEW,
   TRIGGER y EVENT sobre `mesa_ayuda.*`. Guardar fuera de Git `/root/.my.cnf`
   (modo 600) con `[client]`, `user=backup_mesa`, `password=<clave>` y
   `protocol=SOCKET`, cada elemento en su propia línea.
3. Programar y comprobar:

   ```sh
   sudo install -m 750 infra/db/backup.sh /usr/local/sbin/mesa-backup
   sudo install -m 644 infra/systemd/mesa-backup.service infra/systemd/mesa-backup.timer /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now mesa-backup.timer
   sudo systemctl start mesa-backup.service
   sudo systemctl list-timers mesa-backup.timer
   sudo journalctl -u mesa-backup.service --no-pager -n 15
   ```

   Archivo esperado: `/var/backups/mesa_ayuda/FECHA.sql.age`. Copiarlo al PC por
   SSH y conservarlo cifrado en otra máquina. Revisar espacio y retención.
4. Restaurar en una **base temporal vacía**, nunca sobre la de la aplicación.
   En una máquina con MySQL de prueba, age y la clave privada, crear
   `mesa_ayuda_restore`; después:

   ```sh
   set -o pipefail
   age -d -i /ruta/mesa-backup.key /ruta/FECHA.sql.age | sudo mysql mesa_ayuda_restore
   sudo mysql -e 'SELECT COUNT(*) FROM mesa_ayuda_restore.usuarios; SELECT COUNT(*) FROM mesa_ayuda_restore.tickets;'
   ```

   El volcado no incluye `CREATE DATABASE` ni `USE mesa_ayuda`; se restaura en la
   base elegida. Comparar cantidades y un ticket de prueba con el origen del
   respaldo. Guardar fecha, salida y evidencia del contenido; no publicar datos
   reales de usuarios ni la clave de descifrado.

## Wazuh — sg-security LOCAL

1. Usar la versión 4.14.x del enunciado. La guía oficial consultada el 26/09/2026
   usa 4.14.8. En una carpeta fuera de Parcial-2:

   Instalar Docker/Compose y `python3-yaml` previamente. Configurar de forma
   persistente `vm.max_map_count=524288` con sysctl (sirve también para Sonar).
   Crear `/opt/examen/grupo.txt` en este host antes de levantar el manager.

   ```sh
   git clone --branch v4.14.8 --depth 1 https://github.com/wazuh/wazuh-docker.git
   cd wazuh-docker/single-node
   python3 /ruta/Parcial-2/infra/wazuh/restrict-compose.py docker-compose.yml <IP_SECURITY>
   docker compose -f generate-indexer-certs.yml run --rm generator
   docker compose config --quiet
   ```

   **Antes de iniciar**, reemplazar credenciales por defecto en todos los
   componentes según la guía oficial de cambio de contraseñas enlazada abajo;
   el script solo ajusta puertos y volumen FIM. Para una instalación ya iniciada,
   seguir el procedimiento de actualización, no basta editar variables.
   Revisar `docker compose config` localmente, sin publicar su salida (contiene
   claves); no deben publicarse 514, 55000 ni 9200. Después `docker compose up -d`.
2. Desde https://IP_SECURITY instalar un agente en las otras 3 VMs y cada PC
   usando el asistente de despliegue, IP_SECURITY y el nombre real del equipo.
   Enrolamiento 1515/TCP y eventos 1514/TCP. Cambiar contraseña inicial del panel.
   El manager vigila el directorio del nodo security mediante el montaje
   `/opt/examen:/opt/examen:ro`; no hace falta un agente duplicado en el contenedor.
3. Integrar `infra/wazuh/agent-snippets.txt` en los agentes sin duplicar bloques.
   En el manager agregar también `/opt/examen` dentro de su `syscheck` en
   `config/wazuh_cluster/wazuh_manager.conf`. Mantenerlo en el archivo montado,
   no únicamente dentro del contenedor. En Windows vigilar un directorio real,
   por ejemplo `C:\examen`; el requisito `/opt/examen` corresponde a los 4 Linux.
4. Copiar/integrar los archivos locales del repo en
   `/var/ossec/etc/decoders/local_decoder.xml` y `/var/ossec/etc/rules/local_rules.xml`
   del manager (volumen persistente). No sobrescribir reglas locales ajenas.
   Reiniciar `wazuh.manager`; reiniciar agentes tras editar `ossec.conf`.
5. D1: modificar una nota de prueba en `/opt/examen` de cada nodo y confirmar
   nombre del agente/manager y ruta. Incluir configuraciones críticas; no activar
   `report_changes` en `.env`, claves o archivos que contengan secretos.
6. D2: abrir `docker compose exec wazuh.manager /var/ossec/bin/wazuh-logtest`.
   En **la misma sesión**, introducir cinco veces en menos de 60 s:

   ```text
   AUTH_FAILED source_ip=203.0.113.9 username=cuenta_demo
   ```

   Esperar decoder `mesa-ayuda-auth`, campo `srcip` y regla 100121 nivel 10 en el
   quinto evento. Es una prueba sintética, no reemplaza la alerta del sistema.
   Repetir con 4 eventos (sin alerta 100121) e IPs distintas (sin mezclar conteos).
   Luego esperar 60 s sin login/registro y ejecutar `scripts/demo-login-failures.py`
   contra el túnel propio. Debe imprimir cinco 401; 429 significa que Nginx
   limitó antes de la API y esa ejecución no prueba D2. Verificar IP pública real
   del visitante, no la del proxy. No ampliar la confianza del backend a `*`.
7. D3: integrar `active-response.xml` en el manager; confirmar con logtest qué
   regla nativa (5763/5712) dispara el SSH de este sistema. Instalar `rsyslog` e
   `iptables` en la VM agente y comprobar lectura de `/var/log/auth.log` sin
   duplicarla si el agente ya usa journald. Usar una segunda PC autorizada y
   una clave SSH de prueba incorrecta para unos pocos intentos contra esa VM;
   no habilitar contraseñas SSH. Mantener consola abierta. Comprobar alerta,
   `/var/ossec/logs/active-responses.log`, rechazo temporal y recuperación tras
   60 s. Ajustar las reglas al evento nativo observado, no inventar una alerta.

## SonarQube, Bearer y ZAP

En security, configurar persistentemente `vm.max_map_count=524288` y
`fs.file-max=131072` en `/etc/sysctl.d/90-sonarqube.conf`, luego `sudo sysctl
--system`. Copiar `infra/sonarqube/.env.example` a `.env` en esa carpeta, completar
IP y contraseña, y ejecutar allí `docker compose up -d`. Acceso de PCs por
http://IP_SECURITY:9000; cambiar admin inicial. PostgreSQL no publica puertos.
Reservar RAM adicional para Sonar o ejecutarlo en un PC, como admite el HTML;
en ese caso ajustar bind/ACL únicamente para ese PC. No ejecutar dos stacks
pesados con memoria insuficiente. Registrar las versiones/digests descargados y
usar las mismas imágenes antes/después; no usar `down -v` al conservar análisis.

Instalar SonarScanner CLI y Bearer CLI desde sus guías oficiales. Crear dos
proyectos (grupo-backend, grupo-frontend), generar token local temporal, y hacer
primero el análisis base y luego el final dentro de **los mismos proyectos**.
Community no requiere análisis de ramas para esta comparación: identificar cada
ejecución con `sonar.projectVersion=base` o `final` y conservar el historial.

```sh
git worktree add ../Parcial-2-base b757385b7f38da91c0bad9d4e69e56e074a6a806
export SONAR_HOST_URL=http://<IP_SECURITY>:9000
read -rsp 'Token Sonar: ' SONAR_TOKEN; export SONAR_TOKEN
sonar-scanner -Dsonar.projectKey=<grupo>-backend -Dsonar.projectVersion=base -Dsonar.projectBaseDir=../Parcial-2-base/backend -Dsonar.sources=app -Dsonar.python.version=3.12
sonar-scanner -Dsonar.projectKey=<grupo>-frontend -Dsonar.projectVersion=base -Dsonar.projectBaseDir=../Parcial-2-base/frontend -Dsonar.sources=src
```

Repetir cambiando `base` por `final` y los directorios por `backend` y `frontend`
de la rama corregida. Guardar las cuatro capturas/resultados fechados; revisar
Security Hotspots y explicar falsos positivos. Después `unset SONAR_TOKEN`.

```sh
bearer scan ../Parcial-2-base/backend --format html --output docs/bearer-base-FECHA.html
bearer scan backend --format html --output docs/bearer-final-FECHA.html
docker run --rm -v "$PWD/docs:/zap/wrk:rw" ghcr.io/zaproxy/zaproxy:stable zap-baseline.py -t "$URL_PROPIA" -r zap-final-FECHA.html
```

ZAP debe poder escribir en `docs` con su usuario del contenedor; ajustar la
propiedad de esa carpeta si lo requiere, no usar permisos 777 en todo el repo.
Para el informe base, escanear primero el estado base desplegado con **datos y
claves desechables**, en una ventana controlada; guardar `zap-base-FECHA.html`
antes del cambio. Un escaneo actual no puede reconstruir evidencia pasada.
Cerrar el túnel al terminar la demostración vulnerable. Baseline es pasivo:
no prueba por sí solo SQLi, JWT, IDOR o XSS autenticado. Usar PoC manuales propias.
Un resultado sin hallazgos de Bearer/Sonar tampoco demuestra ausencia de fallas.

## Fuentes oficiales consultadas

- https://angular.dev/tools/cli/serve
- https://docs.docker.com/engine/network/firewall-iptables/
- https://wiki.nftables.org/wiki-nftables/index.php/Configuring_chains
- https://dev.mysql.com/doc/refman/8.0/en/error-log-priority-based-filtering.html
- https://documentation.wazuh.com/current/deployment-options/docker/wazuh-container.html
- https://documentation.wazuh.com/current/deployment-options/docker/changing-default-password.html
- https://documentation.wazuh.com/current/user-manual/ruleset/ruleset-xml-syntax/rules.html
- https://documentation.wazuh.com/current/user-manual/capabilities/active-response/ar-use-cases/blocking-ssh-brute-force.html
- https://docs.sonarsource.com/sonarqube-community-build/server-installation/pre-installation/linux
- https://docs.sonarsource.com/sonarqube-community-build/server-installation/from-docker-image/set-up-and-start-container
- https://docs.sonarsource.com/sonarqube-community-build/server-installation/installing-the-database
- https://docs.bearer.com/guides/configure-scan/
- https://www.zaproxy.org/docs/docker/baseline-scan/
