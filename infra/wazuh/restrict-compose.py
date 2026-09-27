"""Ajusta SOLO puertos y FIM del compose oficial 4.14.x; ejecutar antes de up.

Uso: python3 restrict-compose.py docker-compose.yml IP_SECURITY
Requiere python3-yaml. Reemplaza las listas de puertos: un override normal
las acumularía y dejaría los puertos originales abiertos.
"""
import ipaddress
from pathlib import Path
import sys
import yaml

if len(sys.argv) != 3:
    sys.exit(__doc__)
path = Path(sys.argv[1])
host = str(ipaddress.IPv4Address(sys.argv[2]))
data = yaml.safe_load(path.read_text())
services = data["services"]
manager = services["wazuh.manager"]
manager["ports"] = [f"{host}:1514:1514", f"{host}:1515:1515"]
services["wazuh.indexer"].pop("ports", None)
services["wazuh.dashboard"]["ports"] = [f"{host}:443:5601"]
volumes = manager.setdefault("volumes", [])
mount = "/opt/examen:/opt/examen:ro"
if mount not in volumes:
    volumes.append(mount)
path.write_text(yaml.safe_dump(data, sort_keys=False))
print("Puertos: 1514/1515/443 solo por Tailscale. Indexer y API: red interna Docker.")
print("FIM: /opt/examen del HOST montado. Añada ese directorio a syscheck del manager.")
