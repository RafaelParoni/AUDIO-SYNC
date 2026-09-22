#!/usr/bin/env bash
# ==============================================================================
# AudioSync - Script de Instalação Automatizada para Linux
# Suporte: Ubuntu, Debian, Linux Mint, Pop!_OS, Fedora, Arch Linux, Manjaro
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "--------------------------------------------------------"
echo "🎧 Instalador do AudioSync para Linux"
echo "--------------------------------------------------------"

# 1. Identifica e instala pacotes do sistema
echo "[1/4] Verificando e instalando dependências do sistema..."

if command -v apt-get &> /dev/null; then
    echo "Distro baseada em Debian/Ubuntu detectada."
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-tk python3-venv \
        portaudio19-dev pulseaudio-utils libappindicator3-1 gir1.2-appindicator3-0.1 \
        build-essential || true
elif command -v dnf &> /dev/null; then
    echo "Distro baseada em Fedora/RHEL detectada."
    sudo dnf install -y python3 python3-pip python3-tkinter \
        portaudio-devel pulseaudio-utils libappindicator-gtk3 \
        gcc python3-devel || true
elif command -v pacman &> /dev/null; then
    echo "Distro baseada em Arch Linux detectada."
    sudo pacman -Syu --noconfirm python python-pip tk portaudio \
        pulseaudio libappindicator-gtk3 base-devel || true
else
    echo "Aviso: Gerenciador de pacotes não identificado automaticamente."
    echo "Certifique-se de ter instalado: python3, python3-tk, portaudio-dev e pulseaudio-utils."
fi

# 2. Configura ambiente virtual Python (venv)
echo "[2/4] Criando e configurando ambiente virtual Python (venv)..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Instala dependências Python
echo "[3/4] Instalando bibliotecas Python (requirements.txt)..."
pip install --upgrade pip
pip install -r requirements.txt

chmod +x run_linux.sh

# 4. Cria atalho no menu de aplicativos (Desktop Entry)
echo "[4/4] Configurando atalho no menu de aplicativos..."
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

DESKTOP_FILE="$APPS_DIR/audiosync.desktop"
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronização de Áudio via Rede Local (UDP)
Exec=$SCRIPT_DIR/run_linux.sh
Icon=$SCRIPT_DIR/AudioSyncNoText.png
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

echo "--------------------------------------------------------"
echo "✅ Instalação concluída com sucesso!"
echo "Você pode iniciar o AudioSync de três formas:"
echo " 1. Pelo Menu de Aplicativos do seu sistema (AudioSync)"
echo " 2. Pelo terminal executando: ./run_linux.sh"
echo " 3. Ativando o venv: source venv/bin/activate && python3 app.py"
echo "--------------------------------------------------------"
