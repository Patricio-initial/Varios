#!/usr/bin/env bash
# Hace que la máquina virtual "Home Assistant" de UTM arranque sola al iniciar sesión en la Mac.
# Uso:    bash ha-autostart.sh            (instala)
#         bash ha-autostart.sh --quitar   (desinstala)
set -euo pipefail

VM="${HA_VM_NAME:-Home Assistant}"
LABEL="local.homeassistant.utm"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UTMCTL="/Applications/UTM.app/Contents/MacOS/utmctl"

if [ "${1:-}" = "--quitar" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Listo: Home Assistant ya no arranca solo."
  exit 0
fi

[ -x "$UTMCTL" ] || { echo "No encuentro UTM en /Applications. Instalalo primero (brew install --cask utm)."; exit 1; }

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string>
    <string>-c</string>
    <string>sleep 20; open -g -a UTM; sleep 10; "$UTMCTL" start "$VM"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>/tmp/homeassistant-utm.log</string>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Listo: la VM \"$VM\" va a arrancar sola cada vez que inicies sesión."
echo "(La primera vez macOS puede pedir permiso para que la Terminal/launchd controle UTM: aceptalo.)"
