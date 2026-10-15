#!/usr/bin/env python3
"""Genera mi-casa.json y quincho-taller.json (planos para House Control) a partir de las medidas tomadas del
plano "RODRIGUEZ - AMPLIACION VIVIENDA 18-9-2024 - implantación" (ESC 1/200).

Coordenadas en metros, vistas desde arriba como en el plano: x hacia la derecha
(hacia el fondo del lote), z hacia abajo. El origen es la esquina superior izquierda
de la cocina. Para corregir una medida, cambiarla acá y volver a correr:
    python3 generar-plano.py
"""
import json
from pathlib import Path

# x0, z0, x1, z1 medidos sobre el plano. Cada archivo mueve el origen a su esquina.
ROOMS = [
    # Casa principal
    ("cocina",     "Cocina",          2.70,  1.15,  5.55,  7.20, "tile"),
    ("estar",      "Estar-comedor",   5.55,  1.15, 10.85, 10.20, "oak"),
    ("guardado",   "Guardado",        2.70,  7.20,  5.55, 10.20, "tile"),
    ("hall",       "Entrada",         2.70, 10.20,  8.15, 13.10, "stone"),
    ("bano1",      "Baño 1",          2.70, 13.10,  5.10, 16.25, "tile"),
    ("bano2",      "Baño 2",          2.70, 16.25,  5.10, 19.80, "tile"),
    ("pasillo",    "Pasillo",         5.10, 13.10,  6.40, 23.30, "oak"),
    ("dorm1",      "Dormitorio 1",    6.40, 13.10, 10.85, 16.25, "walnut"),
    ("dorm2",      "Dormitorio 2",    6.40, 16.25, 10.85, 19.80, "walnut"),
    ("estudio",    "Estudio",         2.70, 19.80,  5.10, 23.30, "oak"),
    ("principal",  "Dormitorio ppal", 6.40, 19.80, 12.25, 23.30, "walnut"),
    ("lavadero",   "Lavadero",        2.70, 23.30,  6.40, 25.10, "tile"),
    ("vestidor",   "Vestidor",        6.40, 23.30,  8.50, 25.10, "walnut"),
    ("banoppal",   "Baño ppal",       8.50, 23.30, 12.25, 25.10, "tile"),
    # Quincho (Ampliación etapa 2)
    ("quincho",    "Quincho",        21.80, 20.80, 30.55, 25.25, "stone"),
    ("banoq",      "Baño quincho",   30.55, 20.80, 33.75, 23.60, "tile"),
    ("cocinaq",    "Parrilla",       30.55, 23.60, 33.75, 25.25, "tile"),
    # Taller
    ("taller",     "Taller",         38.85, 21.20, 43.35, 25.25, "stone"),
]

# (tipo, desde, hasta, extras) — siempre sobre el borde de una habitación.
OPENINGS = [
    ("open",   (5.55, 1.40), (5.55, 7.00)),                 # cocina abierta al estar
    ("door",   (4.40, 7.20), (5.20, 7.20)),                 # cocina → guardado
    ("open",   (5.70, 10.20), (8.00, 10.20)),               # estar → entrada
    ("door",   (2.70, 10.60), (2.70, 11.60)),               # puerta de entrada
    ("window", (8.15, 10.40), (8.15, 12.90), {"sill": 0.05, "head": 2.3}),  # entrada → patio
    ("open",   (5.10, 13.10), (6.40, 13.10)),               # entrada → pasillo
    ("door",   (5.10, 13.50), (5.10, 14.20)),               # baño 1
    ("door",   (5.10, 18.90), (5.10, 19.60)),               # baño 2
    ("door",   (6.40, 15.30), (6.40, 16.10)),               # dormitorio 1
    ("door",   (6.40, 16.40), (6.40, 17.20)),               # dormitorio 2
    ("door",   (5.10, 20.30), (5.10, 21.10)),               # estudio
    ("door",   (6.40, 20.50), (6.40, 21.30)),               # dormitorio principal
    ("door",   (5.30, 23.30), (6.20, 23.30)),               # lavadero
    ("open",   (6.60, 23.30), (8.30, 23.30)),               # vestidor
    ("door",   (8.70, 23.30), (9.50, 23.30)),               # baño principal
    # Ventanales
    ("window", (10.85, 1.40), (10.85, 10.00), {"sill": 0.05, "head": 2.4}),  # estar → deck
    ("window", (6.00, 1.15), (10.60, 1.15), {"sill": 0.05, "head": 2.4}),   # estar frente
    ("window", (2.70, 1.40), (2.70, 7.00), {"sill": 0.9, "head": 2.1}),     # cocina
    ("window", (10.85, 13.50), (10.85, 15.90), {"sill": 0.05, "head": 2.2}),
    ("window", (10.85, 16.60), (10.85, 19.40), {"sill": 0.05, "head": 2.2}),
    ("window", (12.25, 20.30), (12.25, 22.90), {"sill": 0.05, "head": 2.2}),
    ("window", (2.70, 20.10), (2.70, 21.40)),                                # estudio
    ("window", (2.70, 23.60), (2.70, 24.80)),                                # lavadero
    ("window", (10.00, 25.10), (11.60, 25.10), {"sill": 1.5, "head": 2.0}),  # baño ppal
    # Quincho
    ("window", (22.10, 20.80), (30.30, 20.80), {"sill": 0.05, "head": 2.3}), # paños corredizos
    ("window", (21.80, 21.10), (21.80, 25.00), {"sill": 0.05, "head": 2.3}), # corredizas apiladas
    ("door",   (31.00, 23.60), (31.80, 23.60)),                              # baño quincho
    ("open",   (30.55, 23.90), (30.55, 25.00)),                              # quincho → parrilla
    ("door",   (32.40, 25.25), (33.30, 25.25)),                              # salida parrilla
    # Taller
    ("door",   (38.85, 23.50), (38.85, 24.40)),
    ("window", (39.40, 21.20), (42.80, 21.20), {"sill": 1.0, "head": 2.1}),
]

FURNITURE = [
    # Estar-comedor
    {"type": "diningSet",   "pos": (8.30, 3.25), "width": 3.0, "chairs": 8},
    {"type": "sofa",        "pos": (8.60, 5.65), "width": 2.4, "color": "#8b93a7"},
    {"type": "rug",         "pos": (8.30, 7.30), "size": (3.4, 2.4), "color": "#6f6a5e"},
    {"type": "coffeeTable", "pos": (8.90, 7.50), "width": 1.4},
    {"type": "armchair",    "pos": (6.80, 7.15), "rot": 90, "color": "#a07a5e"},
    {"type": "armchair",    "pos": (6.80, 8.25), "rot": 90, "color": "#a07a5e"},
    {"type": "sideboard",   "pos": (8.40, 9.90), "rot": 180, "width": 4.0},
    {"type": "tv",          "pos": (8.90, 9.85), "rot": 180, "width": 1.8},
    {"type": "plant",       "pos": (10.50, 1.50), "height": 1.4},
    # Cocina
    {"type": "kitchen",     "pos": (3.05, 4.20), "rot": 90, "width": 5.2},
    {"type": "island",      "pos": (5.10, 4.50), "rot": 90, "width": 3.4, "stools": 0},
    {"type": "fridge",      "pos": (5.15, 6.75), "rot": -90},
    # Baños
    {"type": "vanity",      "pos": (3.05, 14.20), "rot": 90, "width": 0.8},
    {"type": "toilet",      "pos": (4.70, 14.80), "rot": -90},
    {"type": "vanity",      "pos": (3.05, 18.70), "rot": 90, "width": 0.8},
    {"type": "toilet",      "pos": (4.70, 17.60), "rot": -90},
    # Dormitorios
    {"type": "bed",         "pos": (9.40, 14.70), "rot": -90, "width": 1.4, "color": "#7f9bb5"},
    {"type": "wardrobe",    "pos": (6.75, 14.30), "rot": 90, "width": 1.9},
    {"type": "bed",         "pos": (9.40, 18.00), "rot": -90, "width": 1.4, "color": "#b98a7a"},
    {"type": "wardrobe",    "pos": (6.75, 18.50), "rot": 90, "width": 1.6},
    {"type": "desk",        "pos": (3.90, 20.30), "width": 1.4},
    {"type": "wardrobe",    "pos": (3.90, 22.90), "rot": 180, "width": 2.2},
    {"type": "bed",         "pos": (10.70, 22.15), "rot": 180, "width": 1.8, "color": "#9c8fb3"},
    {"type": "nightstand",  "pos": (9.45, 22.95), "rot": 180},
    {"type": "nightstand",  "pos": (11.90, 22.95), "rot": 180},
    {"type": "wardrobe",    "pos": (6.75, 21.70), "rot": 90, "width": 2.5},
    {"type": "wardrobe",    "pos": (7.45, 24.75), "rot": 180, "width": 1.9},
    {"type": "bathtub",     "pos": (11.30, 24.65), "rot": 180},
    {"type": "toilet",      "pos": (9.80, 24.70), "rot": 180},
    {"type": "vanity",      "pos": (8.90, 24.80), "rot": 180, "width": 0.7},
    # Lavadero
    {"type": "kitchen",     "pos": (4.30, 24.75), "rot": 180, "width": 3.0, "upper": False},
    # Quincho
    {"type": "diningSet",   "pos": (26.10, 23.05), "width": 3.0, "chairs": 8},
    {"type": "sofa",        "pos": (22.90, 24.75), "rot": 180, "width": 2.0, "color": "#6f8f86"},
    {"type": "island",      "pos": (29.20, 22.40), "rot": 90, "width": 2.2, "stools": 3},
    {"type": "kitchen",     "pos": (29.40, 24.90), "rot": 180, "width": 2.0, "upper": False},
    {"type": "kitchen",     "pos": (32.10, 24.90), "rot": 180, "width": 3.0, "upper": False},
    {"type": "toilet",      "pos": (32.40, 21.30)},
    {"type": "vanity",      "pos": (33.40, 22.60), "rot": -90, "width": 0.7},
    # Taller
    {"type": "desk",        "pos": (39.45, 23.75), "rot": 90, "width": 1.5},
    {"type": "bookshelf",   "pos": (41.70, 24.95), "rot": 180, "width": 4.0, "height": 1.9},
    {"type": "desk",        "pos": (42.90, 21.90), "rot": -90, "width": 0.9},
    # Exterior: solárium, pileta y árboles
    {"type": "rug",         "pos": (25.75, 14.60), "size": (4.0, 3.0), "color": "#c8b89a"},
    {"type": "rug",         "pos": (32.75, 14.60), "size": (10.0, 3.0), "color": "#4fb6d6"},
    {"type": "plant",       "pos": (36.0, 26.5), "height": 1.6},   # durazno
]

LIGHTS = [
    ("estar.comedor", "Comedor",       "estar",     "pendant", (8.30, 3.25), {"y": 1.9, "capabilities": ["brightness", "temp"]}),
    ("estar.living",  "Living",        "estar",     "spots",   (8.60, 7.20), {"capabilities": ["brightness", "temp"]}),
    ("estar.tv",      "Tira TV",       "estar",     "strip",   (8.90, 10.05), {"y": 0.4, "length": 2.0, "capabilities": ["brightness", "color"], "color": "#7b5cff"}),
    ("cocina.techo",  "Cocina",        "cocina",    "spots",   (4.10, 4.20), {"capabilities": ["brightness"]}),
    ("cocina.isla",   "Isla",          "cocina",    "pendant", (5.10, 4.50), {"y": 1.8}),
    ("hall.techo",    "Entrada",       "hall",      "ceiling", (5.40, 11.65), {}),
    ("pasillo.techo", "Pasillo",       "pasillo",   "spots",   (5.75, 18.20), {}),
    ("bano1.techo",   "Baño 1",        "bano1",     "ceiling", (3.90, 14.70), {}),
    ("bano2.techo",   "Baño 2",        "bano2",     "ceiling", (3.90, 18.00), {}),
    ("dorm1.techo",   "Dormitorio 1",  "dorm1",     "ceiling", (8.60, 14.70), {"capabilities": ["brightness", "temp"]}),
    ("dorm2.techo",   "Dormitorio 2",  "dorm2",     "ceiling", (8.60, 18.00), {"capabilities": ["brightness", "temp"]}),
    ("estudio.techo", "Estudio",       "estudio",   "ceiling", (3.90, 21.50), {"capabilities": ["brightness", "temp"]}),
    ("ppal.techo",    "Dormitorio",    "principal", "ceiling", (9.30, 21.50), {"capabilities": ["brightness", "temp"]}),
    ("ppal.mesa",     "Velador",       "principal", "table",   (9.45, 22.95), {"y": 0.55}),
    ("banoppal.techo","Baño ppal",     "banoppal",  "spots",   (10.40, 24.20), {}),
    ("lavadero.techo","Lavadero",      "lavadero",  "ceiling", (4.50, 24.20), {}),
    ("quincho.mesa",  "Mesa quincho",  "quincho",   "pendant", (26.10, 23.05), {"y": 1.9, "capabilities": ["brightness", "temp"]}),
    ("quincho.techo", "Quincho",       "quincho",   "spots",   (24.00, 23.00), {"capabilities": ["brightness"]}),
    ("cocinaq.techo", "Parrilla",      "cocinaq",   "ceiling", (32.10, 24.40), {}),
    ("taller.techo",  "Taller",        "taller",    "ceiling", (41.10, 23.20), {}),
]

# (id, nombre, habitación, pared, posición sobre la pared)
ACS = [
    ("estar.ac",   "Aire estar",      "estar",     "south", (6.60, 10.20)),
    ("dorm1.ac",   "Aire dorm. 1",    "dorm1",     "north", (8.60, 13.10)),
    ("dorm2.ac",   "Aire dorm. 2",    "dorm2",     "south", (8.60, 19.80)),
    ("ppal.ac",    "Aire dorm. ppal", "principal", "north", (9.30, 19.80)),
    ("quincho.ac", "Aire quincho",    "quincho",   "south", (25.50, 25.25)),
]

SCENES = [
    {"id": "llegar", "name": "Llegar", "icon": "home",
     "lights": {"*": {"on": False}, "hall.techo": {"on": True}, "estar.living": {"on": True, "brightness": 0.8}}},
    {"id": "cena", "name": "Cena", "icon": "sofa",
     "lights": {"*": {"on": False}, "estar.comedor": {"on": True, "brightness": 0.7},
                "cocina.isla": {"on": True}, "estar.living": {"on": True, "brightness": 0.3}}},
    {"id": "pelicula", "name": "Película", "icon": "film",
     "lights": {"*": {"on": False}, "estar.tv": {"on": True, "brightness": 0.9, "color": "#6a4cff"}},
     "acs": {"estar.ac": {"target": 23}}},
    {"id": "quincho", "name": "Quincho", "icon": "heat",
     "lights": {"quincho.mesa": {"on": True}, "quincho.techo": {"on": True}, "cocinaq.techo": {"on": True}}},
    {"id": "noche", "name": "Noche", "icon": "moon",
     "lights": {"*": {"on": False}, "pasillo.techo": {"on": True, "brightness": 0.1}},
     "acs": {"*": {"on": False}, "ppal.ac": {"on": True, "target": 24}}},
    {"id": "apagar", "name": "Todo apagado", "icon": "power",
     "lights": {"*": {"on": False}}, "acs": {"*": {"on": False}}},
]


def r(v):
    return round(v, 2)


# La cámara de House Control está pensada para una casa, no para un lote de 40 m: con
# todo junto el modelo no entra en la vista. Por eso se generan dos planos (se carga
# uno a la vez con "Load Floor Plan…"):
#   mi-casa.json         la casa principal
#   quincho-taller.json  el quincho y el taller, con la pileta delante
VARIANTS = {
    "mi-casa.json":        ("Casa La Esperanza", lambda x: x < 13.0),
    "quincho-taller.json": ("Quincho y taller", lambda x: x >= 21.0),
}


def build(name, keep):
    ox = min(x0 for _, _, x0, _, _, _, _ in ROOMS if keep(x0))
    oz = min(z0 for _, _, x0, z0, _, _, _ in ROOMS if keep(x0))
    # La pileta queda delante del quincho: el origen se corre para incluirla.
    if keep(25.0):
        oz = 13.0

    def p(pt):
        return [r(pt[0] - ox), r(pt[1] - oz)]

    plan = {
        "version": 1,
        "name": name,
        "wallHeight": 2.7,
        "interiorWallHeight": 1.25,
        "outdoorTemp": 28,
        "camera": {"azimuth": 34, "elevation": 52},
        "rooms": [{"id": i, "name": n, "rect": [r(x0 - ox), r(z0 - oz), r(x1 - x0), r(z1 - z0)], "floor": f}
                  for i, n, x0, z0, x1, z1, f in ROOMS if keep(x0)],
        "openings": [],
        "furniture": [],
        "lights": [],
        "acs": [],
        "scenes": [],
    }
    for o in OPENINGS:
        t, a, b = o[:3]
        if not keep(a[0]):
            continue
        plan["openings"].append({"type": t, "from": p(a), "to": p(b), **(o[3] if len(o) > 3 else {})})
    for f in FURNITURE:
        if not keep(f["pos"][0]):
            continue
        item = {k: (list(v) if isinstance(v, tuple) else v) for k, v in f.items()}
        item["pos"] = p(f["pos"])
        plan["furniture"].append(item)
    rooms = {room["id"] for room in plan["rooms"]}
    for i, n, room, t, pos, extra in LIGHTS:
        if room not in rooms:
            continue
        plan["lights"].append({"id": i, "name": n, "room": room, "type": t, "pos": p(pos), **extra})
    for i, n, room, wall, pos in ACS:
        if room not in rooms:
            continue
        plan["acs"].append({"id": i, "name": n, "room": room, "wall": wall, "pos": p(pos)})
    ids = {x["id"] for x in plan["lights"]} | {x["id"] for x in plan["acs"]}
    for scene in SCENES:
        sc = {"id": scene["id"], "name": scene["name"], "icon": scene["icon"]}
        for kind in ("lights", "acs"):
            targets = {k: v for k, v in scene.get(kind, {}).items() if k == "*" or k in ids}
            if targets:
                sc[kind] = targets
        if any(k != "*" for kind in ("lights", "acs") for k in sc.get(kind, {})) or scene["id"] == "apagar":
            plan["scenes"].append(sc)
    return plan


if __name__ == "__main__":
    for file, (name, keep) in VARIANTS.items():
        out = Path(__file__).with_name(file)
        out.write_text(json.dumps(build(name, keep), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Escrito {out}")
