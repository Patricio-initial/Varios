# Home Assistant en la Mac (M1) como central de la casa

Home Assistant (HA) corre en una máquina virtual dentro de la Mac, con **UTM**, y queda en la red
de casa como un equipo más (con su propia IP). House Control y el iPhone le hablan por la red.

Lo que resuelve: el **aire del living** (Boldr Klima, por Matter), el **aire de la cocina** y el
**extractor del quincho** (Broadlink).

> Mientras la Mac esté apagada, dormida o fuera de casa, HA no funciona. Más adelante se puede
> pasar todo a un Home Assistant Green con una copia de seguridad, sin rehacer nada.

## 1. Instalar UTM y bajar Home Assistant OS

En la Terminal:

```bash
brew install --cask utm
brew install xz
mkdir -p ~/HomeAssistant && cd ~/HomeAssistant
curl -LO https://github.com/home-assistant/operating-system/releases/download/18.3/haos_generic-aarch64-18.3.qcow2.xz
xz -d haos_generic-aarch64-18.3.qcow2.xz
```

(Si no tenés Homebrew: UTM se baja de https://mac.getutm.app y el archivo `.xz` se abre con
The Unarchiver. Si salió una versión más nueva, cambiar `18.3` por esa; la lista está en
https://github.com/home-assistant/operating-system/releases)

## 2. Crear la máquina virtual en UTM

1. Abrir UTM → **+** → **Virtualize** → **Other**.
2. Marcar **Skip ISO boot** → Continue.
3. Memoria **4096 MB**, CPU **2** núcleos → Continue.
4. Disco: dejar lo que propone (se borra después) → Continue → Shared Directory: Continue.
5. Nombre: **Home Assistant**, marcar **Open VM Settings** → Save.
6. En la configuración:
   - **Network** → Network Mode: **Bridged (Advanced)** → Bridged Interface: **en0** (Wi-Fi).
     Sin esto HA no ve los dispositivos de la casa.
   - **Drives**: borrar el disco VirtIO que se creó (y el USB/CD si hay) → **New…** →
     **Import…** → elegir `~/HomeAssistant/haos_generic-aarch64-18.3.qcow2`.
   - En ese disco nuevo: **Resize…** → **64 GB**.
   - **QEMU**: dejar **UEFI Boot** activado.
7. Save → ▶︎ (Play).

Arranca en una consola negra. La primera vez tarda entre 5 y 20 minutos en prepararse.

## 3. Primer ingreso

1. En el navegador: **http://homeassistant.local:8123**
   (si no abre, la IP aparece en la consola de UTM: `http://<esa IP>:8123`).
2. Crear el usuario y poner la ubicación de la casa.
3. En la **app Deco** (TP-Link): Más → Avanzado → **Reserva de direcciones** → reservar la IP
   del equipo "homeassistant", para que no cambie.

## 4. Que esté siempre encendido

```bash
# La Mac no se duerme estando enchufada (la pantalla sí se apaga)
sudo pmset -c sleep 0
# Opcional, si se cierra la tapa: no dormir nunca (para volver atrás: disablesleep 0)
sudo pmset -a disablesleep 1
```

Y para que HA arranque solo cada vez que iniciás sesión en la Mac:

```bash
bash ~/varios/house-control/ha-autostart.sh
```

(`~/varios` es donde está clonado este repo.) Con FileVault activado, la Mac no inicia sesión
sola después de un corte de luz: hay que poner la contraseña una vez y ahí arranca HA.

## 5. Conectar los dispositivos en Home Assistant

En HA: **Ajustes → Dispositivos y servicios**.

- **Broadlink**: aparece solo como "Descubierto" → Configurar. Quedan el control IR de la
  cocina y los enchufes ("extractor" y "estanque") como `switch.*`.
- **Aire de la cocina** (por el Broadlink): instalar **HACS** (https://hacs.xyz) y desde ahí
  **SmartIR**, con el código de la marca del aire. Eso crea un `climate.*` que se maneja como
  un aire normal. Hace falta saber la marca y el modelo del aire de la cocina.
- **Aire del living (Boldr Klima)**: Añadir integración → **Matter** (instala solo el servidor
  Matter). Después, en la app **Google Home** → el aire → engranaje → **Apps y servicios Matter
  vinculados** → **Vincular app o servicio** → copia el código → en HA: Añadir dispositivo →
  **Matter** → pegar el código. Si Google Home no ofrece esa opción, el código Matter tiene que
  salir de la app de Boldr.

## 6. Conectar Home Assistant con House Control

1. En HA: tu usuario (abajo a la izquierda) → **Seguridad** → **Tokens de acceso de larga
   duración** → Crear token → nombre "House Control" → copiarlo.
2. En House Control: clic derecho en la casita → **Edit Home… → Connections → Home Assistant**
   → aparece solo → **Use** → pegar el token → **Connect**.
3. En el plano, elegir **Real device** para:
   - **Aire living** → el `climate.*` del Klima
   - **Aire cocina** → el `climate.*` de SmartIR
   - **Extractor** (en `quincho-taller.json`) → el `switch.*` del Broadlink
4. **Save & apply**.

## Pasarlo a un equipo dedicado más adelante

HA: Ajustes → Sistema → **Copias de seguridad** → crear y descargar. En el equipo nuevo
(Home Assistant Green o Raspberry Pi), al primer ingreso elegir **Restaurar desde copia de
seguridad**. En House Control solo hay que volver a conectar Home Assistant si cambia la IP.
