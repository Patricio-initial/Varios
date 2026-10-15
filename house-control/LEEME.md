# House Control en mi Mac

App de barra de menú que muestra la casa en 3D y controla luces y aires
(Smart Life/Tuya, Home Assistant, Philips Hue, Apple Home).
Repo original: https://github.com/0xProbabillity/house-control

## Opción A — Descargar la app ya hecha (más fácil)

1. Bajar `HouseControl-<versión>.dmg` de https://github.com/0xProbabillity/house-control/releases
2. Abrir el .dmg y arrastrar **House Control** a **Aplicaciones**.
3. Primera vez macOS la bloquea (no está notarizada):
   - macOS 15+: **Ajustes del Sistema → Privacidad y seguridad → "Abrir igualmente"**.
   - macOS 13–14: clic derecho sobre la app → **Abrir** → **Abrir**.
   - O en Terminal: `xattr -dr com.apple.quarantine "/Applications/House Control.app"`
4. Buscar el icono de la casa en la barra de menú (no tiene ventana ni icono en el Dock).

## Opción B — Compilarla uno mismo

Requisitos: macOS 13+, Xcode Command Line Tools, Node.js 20.19+ / 22.12+.

```bash
curl -fsSL https://raw.githubusercontent.com/patricio-initial/varios/claude/house-control-mac-setup-uetb68/house-control/instalar-mac.sh -o instalar-mac.sh
bash instalar-mac.sh
```

(o clonar este repo y correr `bash house-control/instalar-mac.sh`)

## Cargar el plano de mi casa

El plano es un JSON (`mi-casa.json` en esta carpeta, cuando esté listo).

- Clic derecho en el icono de la barra de menú → **Load Floor Plan…** → elegir `mi-casa.json`.
- Para retocarlo: clic derecho → **Edit Home…** (arrastrar habitaciones, agregar puertas,
  muebles, luces, aires) → **Save & apply**.
- Se guarda en `~/Library/Application Support/HouseControl/plan.json`.

## Conectar los dispositivos reales

Clic derecho → **Edit Home… → Connections** y conectar Smart Life (QR con la app),
Home Assistant, Hue o Apple Home. Luego seleccionar cada luz/aire del plano y elegir
su **Real device**. Hasta entonces todo está simulado, así que se puede probar sin miedo.
