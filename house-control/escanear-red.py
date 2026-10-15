#!/usr/bin/env python3
"""Escanea la red de casa y lista los dispositivos conectados, con una categoría sugerida
(luz, aire, enchufe, cámara, TV, parlante, etc.) para ubicarlos en House Control.

Uso en la Mac (con la Mac conectada al Wi-Fi de casa):
    python3 escanear-red.py

Solo mira la red local: no manda nada a internet ni cambia nada en los dispositivos.
Usa ping, la tabla ARP, nombres DNS/Bonjour (mDNS), UPnP (SSDP) y prueba unos pocos
puertos conocidos. Deja el resultado en red-casa.csv y red-casa.json, en esta carpeta.
"""
import concurrent.futures as cf
import csv
import ipaddress
import json
import platform
import re
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

MAC_OS = platform.system() == "Darwin"

# Fabricantes comunes en casas, por prefijo de MAC (OUI). Lista corta, no exhaustiva.
VENDORS = {
    "Espressif (chip Wi-Fi de enchufes/luces Tuya, Shelly, etc.)": [
        "24:0a:c4", "24:62:ab", "24:6f:28", "24:a1:60", "24:b2:de", "2c:3a:e8", "2c:f4:32", "30:ae:a4",
        "3c:61:05", "3c:71:bf", "40:f5:20", "48:3f:da", "48:55:19", "4c:11:ae", "4c:75:25", "50:02:91",
        "54:5a:a6", "5c:cf:7f", "60:01:94", "68:c6:3a", "70:03:9f", "7c:9e:bd", "80:7d:3a", "84:0d:8e",
        "84:cc:a8", "84:f3:eb", "8c:aa:b5", "8c:ce:4e", "98:cd:ac", "98:f4:ab", "a0:20:a6", "a4:7b:9d",
        "a4:cf:12", "a4:e5:7c", "ac:67:b2", "b4:e6:2d", "bc:dd:c2", "bc:ff:4d", "c4:4f:33", "c4:5b:be",
        "c8:2b:96", "c8:c9:a3", "cc:50:e3", "d8:a0:1d", "d8:bf:c0", "d8:f1:5b", "dc:4f:22", "e0:98:06",
        "e8:db:84", "ec:fa:bc", "f0:08:d1", "f4:cf:a2", "fc:f5:c4", "08:3a:f2", "10:52:1c", "18:fe:34",
        "1c:9d:c2", "30:83:98", "44:17:93", "70:b8:f6", "94:b9:7e", "e8:31:cd", "ec:94:cb", "a8:42:e3",
        "b0:a7:32", "34:85:18", "64:e8:33", "e4:65:b8", "f4:12:fa"],
    "Tuya / Smart Life": ["10:d5:61", "1c:90:ff", "38:1f:8d", "50:8a:06", "68:57:2d", "7c:f6:66", "84:e3:42",
                          "a0:92:08", "c4:82:e1", "d4:a6:51", "fc:67:1f", "18:de:50", "cc:8c:bf", "70:89:76"],
    "Philips Hue (Signify)": ["00:17:88", "ec:b5:fa"],
    "Shelly": ["34:94:54", "e8:68:e7", "c8:f0:9e"],
    "Xiaomi / Yeelight": ["04:cf:8c", "28:6c:07", "34:ce:00", "50:ec:50", "64:09:80", "78:11:dc", "7c:49:eb",
                          "f0:b4:29", "54:48:e6", "b0:41:1d"],
    "Sonoff (ITEAD)": ["d0:27:00"],
    "TP-Link (Kasa/Tapo)": ["50:c7:bf", "60:32:b1", "98:da:c4", "b0:95:75", "1c:3b:f3", "54:af:97", "ac:84:c6",
                            "c0:06:c3", "5c:62:8b", "30:de:4b", "b0:a7:b9", "e8:48:b8", "3c:52:a1"],
    "Apple": ["00:1c:b3", "28:cf:e9", "3c:15:c2", "40:cb:c0", "60:fb:42", "7c:d1:c3", "88:66:a5", "a4:83:e7",
              "ac:bc:32", "b8:e8:56", "d0:03:4b", "f0:18:98", "f4:5c:89", "14:98:77", "90:dd:5d", "bc:d0:74"],
    "Google / Nest / Chromecast": ["1c:f2:9a", "20:df:b9", "30:fd:38", "3c:5a:b4", "44:07:0b", "54:60:09",
                                   "6c:ad:f8", "a4:77:33", "d8:6c:63", "f4:f5:d8", "f4:f5:e8", "f8:0f:f9"],
    "Amazon (Echo/Fire TV)": ["00:fc:8b", "0c:47:c9", "18:74:2e", "34:d2:70", "40:b4:cd", "44:65:0d", "68:37:e9",
                              "74:c2:46", "84:d6:d0", "a0:02:dc", "f0:27:2d", "fc:65:de", "08:84:9d"],
    "Samsung": ["00:12:fb", "00:16:32", "08:d4:2b", "5c:49:7d", "8c:79:f5", "a8:7c:01", "bc:14:85", "f4:7b:09"],
    "LG": ["00:1e:75", "10:68:3f", "64:99:5d", "a8:23:fe", "c8:08:e9", "cc:2d:8c"],
    "Sonos": ["00:0e:58", "34:7e:5c", "48:a6:b8", "5c:aa:fd", "78:28:ca", "94:9f:3e", "b8:e9:37"],
    "Hikvision / EZVIZ (cámaras)": ["28:57:be", "44:19:b6", "4c:bd:8f", "bc:ad:28", "c0:56:e3", "e0:ca:3c"],
    "Dahua / Imou (cámaras)": ["3c:ef:8c", "4c:11:bf", "90:02:a9", "a0:bd:1d", "e0:50:8b"],
    "Raspberry Pi (¿Home Assistant?)": ["28:cd:c1", "2c:cf:67", "b8:27:eb", "d8:3a:dd", "dc:a6:32", "e4:5f:01"],
    "Broadlink (control IR)": ["34:ea:34", "78:0f:77", "c8:f7:42", "e8:16:56"],
    "Midea (aires)": ["50:2c:c6", "6c:4a:85"],
}
OUI = {p: v for v, prefixes in VENDORS.items() for p in prefixes}

# Puertos conocidos: si responden, dicen bastante de qué es el aparato.
PORTS = {
    80: "web", 443: "https", 554: "rtsp (cámara)", 1883: "mqtt", 6668: "tuya local",
    8009: "chromecast", 8123: "home assistant", 8080: "web alt", 9999: "tp-link kasa",
    62078: "iphone/ipad", 548: "mac (afp)", 445: "compartir archivos", 9100: "impresora", 1400: "sonos",
    55443: "yeelight", 8008: "google cast",
}

# Servicios Bonjour (mDNS) que se preguntan directamente, además de los que anuncie cada equipo.
MDNS_TYPES = [
    "_hue._tcp.local", "_hap._tcp.local", "_home-assistant._tcp.local", "_googlecast._tcp.local",
    "_airplay._tcp.local", "_raop._tcp.local", "_shelly._tcp.local", "_esphomelib._tcp.local",
    "_sonos._tcp.local", "_ipp._tcp.local", "_printer._tcp.local", "_companion-link._tcp.local",
    "_amzn-wplay._tcp.local", "_spotify-connect._tcp.local", "_miio._udp.local", "_matter._tcp.local",
    "_meshcop._udp.local", "_smb._tcp.local", "_ssh._tcp.local", "_rfb._tcp.local",
]


def run(cmd, timeout=5):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def local_network():
    """Devuelve (ip propia, red) de la interfaz con salida a la red."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 80))  # no manda nada: solo elige la interfaz
        ip = s.getsockname()[0]
    finally:
        s.close()
    mask = None
    if MAC_OS:
        for iface in ("en0", "en1", "en2", "en3", "en4", "en5"):
            out = run(["ifconfig", iface])
            if f"inet {ip} " in out:
                m = re.search(r"netmask (0x[0-9a-f]+)", out)
                if m:
                    mask = str(ipaddress.IPv4Address(int(m.group(1), 16)))
                break
    else:
        m = re.search(rf"inet {re.escape(ip)}/(\d+)", run(["ip", "-4", "addr"]))
        if m:
            mask = m.group(1)
    net = ipaddress.ip_network(f"{ip}/{mask or 24}", strict=False)
    if net.num_addresses > 1024:  # redes grandes: solo el /24 propio
        net = ipaddress.ip_network(f"{ip}/24", strict=False)
    return ip, net


def ping(ip):
    cmd = ["ping", "-c", "1", "-W", "800" if MAC_OS else "1", ip]
    return subprocess.run(cmd, capture_output=True).returncode == 0


def arp_table():
    table = {}
    for line in run(["arp", "-an"]).splitlines():
        m = re.search(r"\((\d+\.\d+\.\d+\.\d+)\) at ([0-9a-fA-F:]+)", line)
        if m and m.group(2) != "ff:ff:ff:ff:ff:ff":
            table[m.group(1)] = ":".join(p.zfill(2) for p in m.group(2).lower().split(":"))
    return table


def vendor(mac):
    if not mac:
        return ""
    if int(mac[:2], 16) & 0x02:
        return "MAC privada (celular/compu con dirección aleatoria)"
    return OUI.get(mac[:8], "")


def open_ports(ip):
    found = []
    for port, label in PORTS.items():
        with socket.socket() as s:
            s.settimeout(0.35)
            if s.connect_ex((ip, port)) == 0:
                found.append(f"{port} {label}")
    return found


# ---------- mDNS (Bonjour), sin dependencias ----------

def _name(data, off):
    labels, end = [], None
    for _ in range(128):
        n = data[off]
        if n == 0:
            off += 1
            break
        if n & 0xC0 == 0xC0:
            if end is None:
                end = off + 2
            off = ((n & 0x3F) << 8) | data[off + 1]
            continue
        labels.append(data[off + 1:off + 1 + n].decode("utf-8", "replace"))
        off += 1 + n
    return ".".join(labels), (end if end is not None else off)


def _query(names):
    pkt = struct.pack(">HHHHHH", 0, 0, len(names), 0, 0, 0)
    for n in names:
        pkt += b"".join(bytes([len(p)]) + p.encode() for p in n.split(".")) + b"\0"
        pkt += struct.pack(">HH", 12, 0x8001)  # PTR, clase IN pidiendo respuesta unicast
    return pkt


def _parse(data, rec):
    try:
        _, _, qd, an, ns, ar = struct.unpack(">HHHHHH", data[:12])
        off = 12
        for _ in range(qd):
            _, off = _name(data, off)
            off += 4
        for _ in range(an + ns + ar):
            name, off = _name(data, off)
            rtype, _, _, rdlen = struct.unpack(">HHIH", data[off:off + 10])
            off += 10
            rd = data[off:off + rdlen]
            if rtype == 12:
                rec["ptr"].setdefault(name, set()).add(_name(data, off)[0])
            elif rtype == 33:
                rec["srv"][name] = _name(data, off + 6)[0]
            elif rtype == 1 and rdlen == 4:
                rec["a"][name] = socket.inet_ntoa(rd)
            elif rtype == 16:
                txt, i = [], 0
                while i < len(rd):
                    txt.append(rd[i + 1:i + 1 + rd[i]].decode("utf-8", "replace"))
                    i += 1 + rd[i]
                rec["txt"][name] = txt
            off += rdlen
    except Exception:
        pass


def mdns(seconds=5.0):
    rec = {"ptr": {}, "srv": {}, "a": {}, "txt": {}}
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
    s.settimeout(0.3)
    target = ("224.0.0.251", 5353)
    asked = set(MDNS_TYPES)
    try:
        s.sendto(_query(["_services._dns-sd._udp.local"]), target)
        s.sendto(_query(MDNS_TYPES), target)
        start = time.time()
        while time.time() - start < seconds:
            try:
                data, _ = s.recvfrom(9000)
                _parse(data, rec)
            except socket.timeout:
                pass
            new = rec["ptr"].get("_services._dns-sd._udp.local", set()) - asked
            if new:
                asked |= new
                s.sendto(_query(sorted(new)), target)
    except OSError:
        pass
    finally:
        s.close()

    by_ip = {}
    for stype, instances in rec["ptr"].items():
        if stype.startswith("_services."):
            continue
        short = stype.replace(".local", "")
        for inst in instances:
            ip = rec["a"].get(rec["srv"].get(inst, ""))
            if not ip:
                continue
            e = by_ip.setdefault(ip, {"services": set(), "names": set(), "txt": []})
            e["services"].add(short)
            e["names"].add(inst.split("." + short)[0])
            e["txt"] += [t for t in rec["txt"].get(inst, [])
                         if re.match(r"(md|model|fn|ty|manufacturer|product)=", t)]
    for host, ip in rec["a"].items():
        by_ip.setdefault(ip, {"services": set(), "names": set(), "txt": []})["names"].add(
            host.replace(".local", ""))
    return by_ip


# ---------- UPnP (SSDP) ----------

def ssdp(seconds=3.0):
    msg = ("M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\n"
           "MX: 2\r\nST: ssdp:all\r\n\r\n").encode()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0.3)
    found = {}
    try:
        s.sendto(msg, ("239.255.255.250", 1900))
        start = time.time()
        while time.time() - start < seconds:
            try:
                data, addr = s.recvfrom(4096)
            except socket.timeout:
                continue
            m = re.search(rb"(?im)^server:\s*(.+?)\r?$", data)
            if m:
                found.setdefault(addr[0], set()).add(m.group(1).decode("utf-8", "replace").strip())
    except OSError:
        pass
    finally:
        s.close()
    return found


def categorize(d, gateway):
    text = " ".join([d["nombre"], d["fabricante"], " ".join(d["servicios_bonjour"]),
                     " ".join(d["upnp"]), " ".join(d["puertos"]), d["detalles"]]).lower()
    has = lambda *words: any(w in text for w in words)  # noqa: E731
    rules = [
        ("router / módem", lambda: d["ip"] == gateway),
        ("puente Hue (luces)", lambda: has("_hue._tcp", "signify", "philips hue")),
        ("Home Assistant", lambda: has("home-assistant", "8123 ")),
        ("cámara", lambda: has("rtsp", "hikvision", "dahua", "ezviz", "imou", "camera", "camara")),
        ("aire acondicionado", lambda: has("midea", "aire", "climat", "split", "hvac", "daikin", "carrier")),
        ("control IR (puede manejar aires)", lambda: has("broadlink")),
        ("TV / streaming", lambda: has("googlecast", "chromecast", "_airplay", "fire tv", "amzn-wplay", "roku",
                                       "webos", "tizen", "bravia", "tv", "8009 ")),
        ("parlante", lambda: has("sonos", "_raop", "spotify", "echo", "homepod", "nest audio", "speaker")),
        ("impresora", lambda: has("_ipp", "_printer", "9100 ", "epson", "brother", "laserjet", "deskjet")),
        ("accesorio Apple Home", lambda: has("_hap._tcp")),
        ("luz o enchufe inteligente (Tuya/Smart Life)", lambda: has("tuya", "6668 ")),
        ("luz o enchufe inteligente", lambda: has("espressif", "shelly", "sonoff", "kasa", "tapo", "yeelight",
                                                  "esphome", "xiaomi", "9999 ", "55443 ")),
        ("celular / tablet", lambda: has("62078 ", "iphone", "ipad", "android", "galaxy")),
        ("computadora", lambda: has("macbook", "imac", "mac-mini", "_ssh", "_smb", "_rfb", "445 ", "548 ",
                                    "desktop", "laptop", "pc")),
        ("celular / compu (MAC privada)", lambda: has("mac privada")),
    ]
    for label, test in rules:
        if test():
            return label
    return "desconocido"


def default_gateway():
    if MAC_OS:
        m = re.search(r"gateway: (\S+)", run(["route", "-n", "get", "default"]))
    else:
        m = re.search(r"default via (\S+)", run(["ip", "route"]))
    return m.group(1) if m else None


def main():
    my_ip, net = local_network()
    print(f"Red: {net}  (esta Mac es {my_ip})")
    hosts = [str(h) for h in net.hosts()]

    print(f"1/4 Buscando equipos ({len(hosts)} direcciones, ~30 s)…")
    with cf.ThreadPoolExecutor(64) as ex:
        alive = {ip for ip, ok in zip(hosts, ex.map(ping, hosts)) if ok}

    print("2/4 Preguntando nombres por Bonjour y UPnP…")
    with cf.ThreadPoolExecutor(2) as ex:
        f_mdns, f_ssdp = ex.submit(mdns), ex.submit(ssdp)
        bonjour, upnp = f_mdns.result(), f_ssdp.result()

    arp = arp_table()
    ips = {ip for ip in alive | set(arp) | set(bonjour) | set(upnp)
           if ip != my_ip and ipaddress.ip_address(ip) in net}
    ips = sorted(ips, key=ipaddress.ip_address)
    gateway = default_gateway()

    print(f"3/4 Probando puertos conocidos en {len(ips)} equipos…")
    with cf.ThreadPoolExecutor(32) as ex:
        ports = dict(zip(ips, ex.map(open_ports, ips)))

    print("4/4 Armando la lista…")
    devices = []
    for ip in ips:
        try:
            dns = socket.gethostbyaddr(ip)[0]
        except OSError:
            dns = ""
        b = bonjour.get(ip, {"services": set(), "names": set(), "txt": []})
        mac = arp.get(ip, "")
        d = {
            "ip": ip,
            "mac": mac,
            "fabricante": vendor(mac),
            "nombre": " / ".join(sorted({n for n in [dns, *b["names"]] if n})),
            "servicios_bonjour": sorted(b["services"]),
            "upnp": sorted(upnp.get(ip, [])),
            "puertos": [p + " " for p in ports.get(ip, [])],
            "detalles": " ".join(sorted(set(b["txt"]))),
        }
        d["categoria_sugerida"] = categorize(d, gateway)
        d["puertos"] = [p.strip() for p in d["puertos"]]
        devices.append(d)

    here = Path(__file__).resolve().parent
    (here / "red-casa.json").write_text(json.dumps(
        {"red": str(net), "fecha": time.strftime("%Y-%m-%d %H:%M"), "dispositivos": devices},
        ensure_ascii=False, indent=2), encoding="utf-8")
    with open(here / "red-casa.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ip", "mac", "fabricante", "nombre", "categoria_sugerida", "bonjour", "upnp", "puertos",
                    "detalles"])
        for d in devices:
            w.writerow([d["ip"], d["mac"], d["fabricante"], d["nombre"], d["categoria_sugerida"],
                        "; ".join(d["servicios_bonjour"]), "; ".join(d["upnp"]), "; ".join(d["puertos"]),
                        d["detalles"]])

    print(f"\n{len(devices)} dispositivos encontrados:\n")
    for d in devices:
        print(f"  {d['ip']:<15} {d['categoria_sugerida']:<44} {d['nombre'] or d['fabricante'] or d['mac']}")
    print(f"\nGuardado en {here / 'red-casa.csv'} y {here / 'red-casa.json'}")
    print("Mandale red-casa.json a Claude para que ubique cada dispositivo en el plano.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
