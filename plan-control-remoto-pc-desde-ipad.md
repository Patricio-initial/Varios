# Plan: controlar mi PC de casa desde el iPad

Objetivo: ver y manejar el escritorio de la PC (teclado, mouse, apps, archivos) desde el iPad,
primero dentro de la red de casa y, opcionalmente, desde cualquier lugar de forma segura.

---

## 0. Decisiones previas (5 minutos)

| Pregunta | Cómo averiguarlo | Qué cambia |
|---|---|---|
| ¿Qué sistema tiene la PC? | Windows: `Win + Pause` → "Edición". Mac / Linux: obvio. | Define la herramienta (ver Fase 2). |
| ¿Windows **Pro** o **Home**? | Misma pantalla de arriba. | Home **no** puede recibir Escritorio Remoto (RDP). |
| ¿Solo en casa o también fuera? | Tu necesidad. | Fuera de casa → Fase 4 (Tailscale). |
| ¿Quiero encender la PC a distancia? | Tu necesidad. | Sí → Fase 5 (Wake-on-LAN). |
| ¿Juegos / video fluido? | Tu necesidad. | Sí → Parsec o Moonlight/Sunshine en vez de RDP. |

### Recomendación según el caso

| Caso | Herramienta en la PC | App en el iPad |
|---|---|---|
| Windows Pro/Enterprise, uso general | Escritorio Remoto (RDP), integrado | **Windows App** (Microsoft, gratis) |
| Windows Home, o quieres algo que "solo funcione" | **RustDesk** (gratis, código abierto) o Chrome Remote Desktop | RustDesk / Chrome Remote Desktop |
| Juegos o video con baja latencia | **Parsec** o **Sunshine** | Parsec / **Moonlight** |
| Mac | Compartir pantalla (VNC) integrado | Screens 5, RealVNC Viewer, o RustDesk |
| Linux | GNOME Remote Desktop (RDP) o xrdp | Windows App |

> El resto del plan usa la ruta principal **Windows Pro + RDP + Tailscale**. Las alternativas
> están en la Fase 2B.

---

## Fase 1. Preparar la red de casa

1. **IP fija para la PC**: en el router, sección *DHCP → Reserva de direcciones* (o "IP estática"),
   asocia la MAC de la PC a una IP, p. ej. `192.168.1.50`.
   - Ver MAC e IP en Windows: `ipconfig /all` → "Dirección física" e "IPv4".
2. **Preferir cable Ethernet** en la PC (más estable y necesario para Wake-on-LAN fiable).
3. **Evitar que la PC se duerma** mientras quieras usarla a distancia:
   *Configuración → Sistema → Inicio/apagado y suspensión → Suspender: Nunca* (conectada a corriente).
4. Anotar: nombre de la PC (`hostname`), IP fija, usuario de Windows.

**Listo cuando:** la PC siempre tiene la misma IP tras reiniciar.

---

## Fase 2A. Escritorio Remoto (Windows Pro)

En la PC:

1. *Configuración → Sistema → Escritorio remoto → Activar*.
2. Dejar marcada **"Requerir autenticación a nivel de red (NLA)"**.
3. Asegurar que tu cuenta tiene **contraseña** (RDP no acepta cuentas sin contraseña).
   Si inicias con PIN/Hello y cuenta Microsoft, usa el correo + contraseña de la cuenta Microsoft.
4. Equivalente en PowerShell (como administrador), por si prefieres un script:

   ```powershell
   Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name fDenyTSConnections -Value 0
   Set-ItemProperty 'HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' -Name UserAuthentication -Value 1
   Enable-NetFirewallRule -DisplayGroup 'Escritorio remoto'   # en inglés: 'Remote Desktop'
   ```

En el iPad:

1. Instalar **Windows App** (antes "Microsoft Remote Desktop") desde la App Store.
2. **+ → Agregar PC** → Nombre de host: `192.168.1.50` (tu IP fija).
3. Cuenta de usuario: tu usuario de Windows (o correo de cuenta Microsoft) y contraseña.
4. Opcional: en la PC, *Configuración de pantalla* → resolución "Coincidir con el dispositivo"
   para que se vea nítido en el iPad.

**Listo cuando:** desde el iPad, conectado al Wi-Fi de casa, ves el escritorio de la PC.

## Fase 2B. Alternativas (Windows Home, Mac, juegos)

- **RustDesk**: instalar en PC e iPad, en la PC anotar ID + definir *contraseña permanente*,
  conectar desde el iPad con ese ID. Funciona también fuera de casa sin configurar el router.
- **Chrome Remote Desktop**: `remotedesktop.google.com/access` en la PC → configurar acceso con PIN;
  en el iPad usar la app o Safari con la misma cuenta de Google.
- **Parsec / Sunshine + Moonlight**: para juegos; requiere GPU razonable en la PC.
- **Mac**: *Ajustes del Sistema → General → Compartir → Compartir pantalla*; conectar con
  `vnc://IP-del-Mac` desde una app VNC.

---

## Fase 3. Comodidad en el iPad

- **Mouse y teclado Bluetooth** (o Magic Keyboard): Windows App soporta puntero real;
  la experiencia pasa de "aceptable" a "como estar frente a la PC".
- En Windows App: activar *modo mouse* en vez de *toque directo* si no tienes mouse.
- Gestos útiles: dos dedos = clic derecho, pellizco = zoom, tres dedos = mostrar teclado.
- Redirigir portapapeles (activado por defecto) para copiar/pegar entre iPad y PC.

---

## Fase 4. Acceso desde fuera de casa (seguro)

**Nunca abrir el puerto 3389 (RDP) del router a Internet.** Es de lo más escaneado y atacado.
En su lugar, usar una VPN privada:

### Opción recomendada: Tailscale (gratis para uso personal)

1. Crear cuenta en Tailscale (idealmente con una cuenta que tenga **2FA** activado).
2. Instalar Tailscale en la **PC** e iniciar sesión.
   - En la PC: *Preferencias → Run unattended* para que funcione sin sesión abierta.
3. Instalar Tailscale en el **iPad** con la misma cuenta y activar la VPN.
4. En la consola de Tailscale, desactivar la expiración de clave para la PC
   (*Machines → … → Disable key expiry*), así no pierde acceso a los 180 días.
5. En Windows App, crear una segunda conexión usando la IP `100.x.y.z` de Tailscale
   o el nombre MagicDNS (p. ej. `mi-pc`) en vez de `192.168.1.50`.
6. Opcional (endurecer): limitar la regla de firewall de RDP a la red de Tailscale:

   ```powershell
   Get-NetFirewallRule -DisplayGroup 'Escritorio remoto' |
     Set-NetFirewallRule -RemoteAddress 192.168.1.0/24,100.64.0.0/10
   ```

**Alternativas:** WireGuard en el router (si lo soporta), ZeroTier, o RustDesk (ya funciona
fuera de casa por sí solo).

**Listo cuando:** con el iPad en datos móviles (Wi-Fi apagado) y Tailscale activo, conectas a la PC.

---

## Fase 5. Encender la PC a distancia (Wake-on-LAN) — opcional

1. **BIOS/UEFI**: activar *Wake on LAN* / *Power On by PCI-E* / *Resume by LAN*.
   Desactivar *ErP / EuP* si existe (corta la corriente a la tarjeta de red).
2. **Windows → Administrador de dispositivos → Adaptador de red → Propiedades**:
   - *Administración de energía*: marcar "Permitir que este dispositivo reactive el equipo"
     y "Solo permitir un paquete mágico".
   - *Opciones avanzadas*: "Wake on Magic Packet" = Habilitado.
3. **Desactivar inicio rápido**: *Panel de control → Opciones de energía → Elegir el
   comportamiento de los botones → desmarcar "Activar inicio rápido"*.
4. En el iPad, app de WoL (p. ej. **Mocha WOL** o **Wolow**) con la MAC y la IP de broadcast
   (`192.168.1.255`). Probar dentro de casa.
5. **Desde fuera**: el paquete mágico no cruza Internet por sí solo. Opciones:
   - Un dispositivo siempre encendido en casa con Tailscale (Raspberry Pi, NAS, router con
     Tailscale/WireGuard) que envíe el paquete: `wakeonlan AA:BB:CC:DD:EE:FF`.
   - Router que ofrezca WoL desde su app (FRITZ!Box, ASUS, algunos TP-Link).
   - Alternativa simple: dejar la PC en **suspensión** en vez de apagada, o configurar en la
     BIOS "Encender tras corte de energía" + enchufe inteligente.

**Listo cuando:** apagas la PC, envías el paquete desde el iPad y la PC arranca.

---

## Fase 6. Seguridad (lista de control)

- [ ] Contraseña larga y única en la cuenta de Windows.
- [ ] NLA activado en RDP.
- [ ] Puerto 3389 **cerrado** en el router (verificar que no haya reenvío de puertos ni UPnP que lo abra).
- [ ] 2FA en la cuenta de Tailscale / RustDesk / Google.
- [ ] Windows Update y la app remota al día.
- [ ] Bloqueo de pantalla en el iPad (contiene acceso a tu PC).
- [ ] Opcional: política de bloqueo de cuenta tras intentos fallidos
      (`secpol.msc → Directivas de cuenta → Bloqueo de cuenta`).

---

## Fase 7. Pruebas finales

1. En casa, Wi-Fi: conectar por IP local → OK.
2. Fuera, datos móviles + Tailscale: conectar por IP/nombre de Tailscale → OK.
3. Reiniciar la PC sin iniciar sesión → conectar de nuevo (valida Tailscale desatendido) → OK.
4. Apagar la PC → despertar con WoL → conectar → OK (si hiciste la Fase 5).
5. Probar copiar/pegar, audio y teclado físico.

---

## Solución de problemas rápida

| Síntoma | Causa probable | Solución |
|---|---|---|
| "No se pudo encontrar el equipo" | IP cambió o PC dormida | Revisar reserva DHCP; desactivar suspensión. |
| Credenciales rechazadas | Usas PIN en vez de contraseña | Usar contraseña o correo de cuenta Microsoft. |
| Funciona en casa, no fuera | Tailscale apagado en iPad o PC | Activar VPN en el iPad; "Run unattended" en la PC. |
| Lento o entrecortado | Wi-Fi débil / resolución alta | Cable en la PC; bajar resolución o calidad en la app. |
| WoL no enciende | Inicio rápido / ErP / Wi-Fi | Fase 5 pasos 1–3; WoL fiable solo por cable. |
| Pantalla negra al conectar | Controlador de video / sesión | Actualizar driver; en RDP cerrar y volver a conectar. |

---

## Resumen del orden de trabajo

1. IP fija en el router (Fase 1).
2. Activar Escritorio Remoto o instalar RustDesk (Fase 2).
3. Instalar Windows App en el iPad y probar en casa.
4. Añadir mouse/teclado (Fase 3).
5. Tailscale en PC e iPad para acceso externo (Fase 4).
6. Wake-on-LAN si quieres encenderla a distancia (Fase 5).
7. Revisar la lista de seguridad y hacer las pruebas (Fases 6–7).
