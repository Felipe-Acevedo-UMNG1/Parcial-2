"""Genera reglas; NO las aplica. Uso: python3 infra/firewall.py ROL red.private.json.

Ubuntu 24.04, nftables, Tailscale IPv4, sin rutas de subred/exit node.
Tabla independiente: no vacía las reglas de Docker, Tailscale o Wazuh.
"""
import argparse
import ipaddress
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("role", choices=["db", "backend", "frontend", "security"])
parser.add_argument("config", type=Path)
args = parser.parse_args()
data = json.loads(args.config.read_text())


def ip(value):
    address = ipaddress.IPv4Address(value)
    if address not in ipaddress.IPv4Network("100.64.0.0/10"):
        raise ValueError("Use la IPv4 real de Tailscale (100.64.0.0/10)")
    return str(address)


nodes = {role: ip(data[role + "_ip"]) for role in ("db", "backend", "frontend", "security")}
pcs = [ip(value) for value in data["pc_ips"]]
if not pcs or len(set(nodes.values())) != 4 or set(pcs) & set(nodes.values()):
    parser.error("Debe haber cuatro IPs de servidor distintas y al menos un PC independiente")
api, db = int(data["app_port"]), int(data["db_port"])
if not all(1 <= port <= 65535 for port in (api, db)) or db == 3306:
    parser.error("Use puertos asignados entre 1 y 65535; DB no puede ser 3306")


def allowed(sources, ports, forwarded=False):
    # En FORWARD, Docker ya tradujo 443 a 5601. INPUT ve el puerto del host.
    origins = ", ".join(sorted(set(sources)))
    targets = ", ".join(str(p) for p in ports)
    dnat = "ct status dnat " if forwarded else ""
    return f'    iifname "tailscale0" ip saddr {{ {origins} }} {dnat}tcp dport {{ {targets} }} accept'


incoming = [allowed(pcs, [22])]
forward = []
if args.role == "db":
    incoming.append(allowed([nodes["backend"]], [db]))
elif args.role == "backend":
    sources = pcs + [nodes["frontend"]]
    incoming.append(allowed(sources, [api]))
    forward.append(allowed(sources, [api], True))
elif args.role == "security":
    sources = pcs + [nodes[r] for r in ("db", "backend", "frontend")]
    incoming += [allowed(sources, [1514, 1515]), allowed(pcs, [443, 9000])]
    forward += [allowed(sources, [1514, 1515], True), allowed(pcs, [5601, 9000], True)]

print('''# Generado para este nodo. Aplicar desde consola de VM tras verificar SSH por Tailscale.
# La prioridad 10 filtra después de las cadenas habituales de iptables (0).
add table inet examen
flush table inet examen
table inet examen {
  chain input {
    type filter hook input priority 10; policy drop;
    iifname "lo" accept
    ct state invalid drop
    ct state established,related accept
    ip protocol icmp accept
    meta l4proto ipv6-icmp accept''')
print("\n".join(incoming))
print('''  }
  chain forward {
    type filter hook forward priority 10; policy accept;
    ct state invalid drop
    ct state established,related accept''')
print("\n".join(forward))
print('''    # Rechaza nuevas conexiones a puertos publicados no autorizados arriba.
    ct status dnat drop
  }
}''')
