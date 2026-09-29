<#
.SYNOPSIS
    Prepara la PC de escritorio para controlarla desde el iPad via Tailscale + Escritorio Remoto.

.DESCRIPTION
    1. Verifica que Windows sea Pro/Enterprise/Education (Home no puede recibir RDP).
    2. Instala Tailscale con winget (si no esta instalado).
    3. Inicia sesion en Tailscale en modo desatendido (funciona sin sesion de Windows abierta).
    4. Activa Escritorio Remoto con NLA.
    5. Limita el firewall de RDP a la subred local y a Tailscale (100.64.0.0/10).
    6. Evita que la PC se suspenda mientras esta conectada a corriente.

    Ejecutar en PowerShell como administrador:
        powershell -ExecutionPolicy Bypass -File .\configurar-pc-tailscale-rdp.ps1

.PARAMETER SoloTailscale
    Permite RDP solo desde Tailscale (bloquea la subred local). Recomendado si en casa
    hay dos redes y quieres que todo entre por Tailscale.

.PARAMETER SinCambiosDeEnergia
    No modifica la configuracion de suspension.
#>
[CmdletBinding()]
param(
    [switch]$SoloTailscale,
    [switch]$SinCambiosDeEnergia
)

$ErrorActionPreference = 'Stop'

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Ok($texto)   { Write-Host "    OK: $texto" -ForegroundColor Green }
function Aviso($texto){ Write-Host "    AVISO: $texto" -ForegroundColor Yellow }

# --- 0. Administrador -------------------------------------------------------
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Ejecuta este script en PowerShell como administrador (clic derecho > Ejecutar como administrador).'
}

# --- 1. Edicion de Windows --------------------------------------------------
Paso 'Comprobando edicion de Windows'
$edicion = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion').EditionID
if ($edicion -like 'Core*') {
    Aviso "Windows Home ($edicion) no puede recibir Escritorio Remoto."
    Aviso 'Tailscale se instalara igual; para el control remoto usa RustDesk (ver Fase 2B del plan).'
    $puedeRdp = $false
} else {
    Ok "Edicion $edicion admite Escritorio Remoto."
    $puedeRdp = $true
}

# --- 2. Instalar Tailscale --------------------------------------------------
Paso 'Instalando Tailscale'
$tailscaleExe = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
if (Test-Path $tailscaleExe) {
    Ok 'Tailscale ya esta instalado.'
} else {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'winget no esta disponible. Instala Tailscale desde https://tailscale.com/download/windows y vuelve a ejecutar el script.'
    }
    winget install --id Tailscale.Tailscale --exact --silent --accept-package-agreements --accept-source-agreements
    if (-not (Test-Path $tailscaleExe)) {
        throw "No se encontro $tailscaleExe tras la instalacion."
    }
    Ok 'Tailscale instalado.'
}

# --- 3. Iniciar sesion en modo desatendido ----------------------------------
Paso 'Conectando Tailscale (se abrira el navegador para iniciar sesion si hace falta)'
& $tailscaleExe up --unattended
if ($LASTEXITCODE -ne 0) { throw 'tailscale up fallo. Revisa el mensaje de arriba.' }
$ipTailscale = (& $tailscaleExe ip -4 | Select-Object -First 1)
Ok "IP de Tailscale de esta PC: $ipTailscale"

# --- 4. Escritorio Remoto con NLA -------------------------------------------
if ($puedeRdp) {
    Paso 'Activando Escritorio Remoto con NLA'
    $ts = 'HKLM:\System\CurrentControlSet\Control\Terminal Server'
    Set-ItemProperty $ts -Name fDenyTSConnections -Value 0
    Set-ItemProperty "$ts\WinStations\RDP-Tcp" -Name UserAuthentication -Value 1
    Ok 'Escritorio Remoto activado.'

    # --- 5. Firewall -------------------------------------------------------
    Paso 'Configurando firewall de Escritorio Remoto'
    # Grupo "Escritorio remoto" / "Remote Desktop", independiente del idioma de Windows.
    $grupoRdp = '@FirewallAPI.dll,-28752'
    $origen = if ($SoloTailscale) { @('100.64.0.0/10') } else { @('LocalSubnet', '100.64.0.0/10') }
    Get-NetFirewallRule -Group $grupoRdp |
        Set-NetFirewallRule -Enabled True -Profile Any -RemoteAddress $origen
    Ok ("RDP permitido solo desde: " + ($origen -join ', '))
}

# --- 6. Energia -------------------------------------------------------------
if (-not $SinCambiosDeEnergia) {
    Paso 'Desactivando suspension con corriente'
    powercfg /change standby-timeout-ac 0
    powercfg /change hibernate-timeout-ac 0
    Ok 'La PC no se suspendera mientras este enchufada.'
}

# --- Resumen ----------------------------------------------------------------
$nombre = $env:COMPUTERNAME.ToLower()
Write-Host "`n================ LISTO ================" -ForegroundColor Green
Write-Host "Nombre en Tailscale (MagicDNS): $nombre"
Write-Host "IP de Tailscale:                $ipTailscale"
Write-Host "Usuario para conectar:          $env:USERNAME (o el correo de tu cuenta Microsoft)"
Write-Host ''
Write-Host 'Pendiente:'
Write-Host '  1. En https://login.tailscale.com/admin/machines: en esta PC > ... > Disable key expiry.'
Write-Host '  2. En el iPad: instalar Tailscale, iniciar sesion con la MISMA cuenta y activar la VPN.'
if ($puedeRdp) {
    Write-Host "  3. En Windows App (iPad): Agregar PC > nombre de host '$nombre' (o $ipTailscale)."
} else {
    Write-Host '  3. Instalar RustDesk en PC e iPad (Windows Home no admite RDP).'
}
