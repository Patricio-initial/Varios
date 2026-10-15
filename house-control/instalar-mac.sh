#!/usr/bin/env bash
# Instala y compila House Control (github.com/0xProbabillity/house-control) en macOS.
# Uso: bash instalar-mac.sh [carpeta-destino]   (por defecto ~/house-control)
set -euo pipefail

DEST="${1:-$HOME/house-control}"

echo "==> Comprobando requisitos"
if ! xcode-select -p >/dev/null 2>&1; then
  echo "Faltan las Xcode Command Line Tools. Se abrirá el instalador; cuando termine, vuelve a ejecutar este script."
  xcode-select --install || true
  exit 1
fi
swift --version | head -1

if ! command -v node >/dev/null 2>&1; then
  if command -v brew >/dev/null 2>&1; then
    echo "==> Instalando Node.js con Homebrew"
    brew install node
  else
    echo "Falta Node.js (20.19+ o 22.12+). Instálalo desde https://nodejs.org o instala Homebrew (https://brew.sh) y vuelve a ejecutar."
    exit 1
  fi
fi
echo "Node $(node --version)"

echo "==> Descargando el código en $DEST"
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --ff-only
else
  git clone https://github.com/0xProbabillity/house-control.git "$DEST"
fi

echo "==> Compilando (la primera vez tarda unos minutos)"
cd "$DEST"
./scripts/build-app.sh

echo "==> Abriendo la app: busca el icono de la casa en la barra de menú (arriba a la derecha)"
open build/HouseControl.app
