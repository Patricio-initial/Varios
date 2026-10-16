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

Armado a partir del plano "RODRIGUEZ - Ampliación vivienda 18-9-2024 - implantación" (ESC 1/200):

| Archivo | Qué tiene |
| --- | --- |
| `mi-casa.json` | Casa principal: cocina, estar-comedor, guardado, entrada, 2 baños, pasillo, 2 dormitorios, estudio, dormitorio principal con vestidor y baño, lavadero |
| `quincho-taller.json` | Quincho (con baño y parrilla), taller y la pileta con el solárium |

Son dos archivos porque la vista 3D de la app está pensada para una casa: con todo
el lote junto (~41 m) el modelo no entra en la pantalla. Se usa uno a la vez.

1. Bajar `mi-casa.json` (y si se quiere `quincho-taller.json`) a la Mac.
2. Clic derecho en el icono de la barra de menú → **Load Floor Plan…** → elegir el archivo.
3. Para retocarlo: clic derecho → **Edit Home…** (arrastrar habitaciones, mover luces,
   aires y muebles) → **Save & apply**. Se guarda en
   `~/Library/Application Support/HouseControl/plan.json`.

**Dispositivos en el plano** (se vinculan en **Edit Home… → seleccionar la luz o el aire → Real device**):

| En el plano | Dónde | Plataforma |
| --- | --- | --- |
| Mesada 1 y 2 | Cocina | Philips Hue (grupo "mesada") |
| Mesa 1 y 2 | Comedor | Philips Hue (grupo "mesa") |
| Ikea | Living (lámpara Symfonisk) | Philips Hue |
| Puerta, Avestruz, Pasillo | Entrada | Smart Life |
| Dispenser agua | Guardado / despensa | Smart Life (interruptor) |
| Luz garage | Garage | Smart Life |
| Aire living | Estar-comedor | "dining room air conditioner" |
| Aire cocina | Cocina | Broadlink → necesita Home Assistant |
| Extractor | Quincho (`quincho-taller.json`) | Broadlink → necesita Home Assistant |

House Control solo maneja luces, enchufes y aires: las cerraduras, el alimentador del gato,
el sensor de temperatura del quincho y el enchufe del estanque no aparecen.
Las posiciones de las luces dentro de cada ambiente son aproximadas: se arrastran en el editor.

## Ver qué hay conectado en la red

Para saber qué luces, enchufes, aires y demás hay en casa y ubicarlos en el plano:

```bash
python3 escanear-red.py
```

Con la Mac en el Wi-Fi de casa, tarda alrededor de un minuto. Solo mira la red local
(ping, ARP, Bonjour, UPnP y unos pocos puertos conocidos) y no cambia nada. Deja
`red-casa.csv` (para abrir en Excel o Numbers) y `red-casa.json` (para pasarle a Claude),
cada uno con una categoría sugerida por dispositivo. Esos archivos no se suben al repo.

## Conectar los dispositivos reales

Clic derecho → **Edit Home… → Connections** y conectar Smart Life (QR con la app),
Home Assistant, Hue o Apple Home. Luego seleccionar cada luz/aire del plano y elegir
su **Real device**. Hasta entonces todo está simulado, así que se puede probar sin miedo.
