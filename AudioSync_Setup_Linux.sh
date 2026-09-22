#!/usr/bin/env bash
# ==============================================================================
# 🎧 AudioSync - Assistente de Instalação para Linux (Setup Wizard)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.1"

clear
echo "======================================================"
echo "   🎧 AudioSync v$VERSION - Assistente de Instalação"
echo "   Desenvolvido por Rafael Paroni"
echo "   https://rafaelparoni.vercel.app/audio-sync"
echo "======================================================"
echo ""
echo "Bem-vindo ao instalador do AudioSync para Linux."
echo "Este assistente instalará o AudioSync e todas as dependências no seu computador."
echo ""

# Determina destino padrão
if [ "$EUID" -eq 0 ]; then
    DEFAULT_INSTALL_DIR="/opt/AudioSync"
    DEFAULT_BIN_DIR="/usr/local/bin"
    DEFAULT_DESKTOP_DIR="/usr/share/applications"
    DEFAULT_ICON_DIR="/usr/share/icons/hicolor/128x128/apps"
else
    DEFAULT_INSTALL_DIR="$HOME/.local/share/AudioSync"
    DEFAULT_BIN_DIR="$HOME/.local/bin"
    DEFAULT_DESKTOP_DIR="$HOME/.local/share/applications"
    DEFAULT_ICON_DIR="$HOME/.local/share/icons/hicolor/128x128/apps"
fi

read -p "Pasta de instalação [$DEFAULT_INSTALL_DIR]: " USER_DIR
INSTALL_DIR="${USER_DIR:-$DEFAULT_INSTALL_DIR}"

echo ""
echo "[1/4] Verificando e instalando pacotes do sistema..."

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
fi

echo ""
echo "[2/4] Copiando arquivos para $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DEFAULT_BIN_DIR"
mkdir -p "$DEFAULT_DESKTOP_DIR"
mkdir -p "$DEFAULT_ICON_DIR"

# Copia arquivos do aplicativo
cp -r app.py client.py server.py config.json requirements.txt AudioSyncNoText.png "$INSTALL_DIR/"

# Configura ambiente virtual
echo ""
echo "[3/4] Configurando ambiente Python isolado..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Cria lançador executável
LAUNCHER="$INSTALL_DIR/audiosync"
cat << EOF > "$LAUNCHER"
#!/usr/bin/env bash
cd "$INSTALL_DIR"
source "$INSTALL_DIR/venv/bin/activate"
exec python3 app.py "\$@"
EOF
chmod +x "$LAUNCHER"

# Cria symlink global ou no PATH do usuário
ln -sf "$LAUNCHER" "$DEFAULT_BIN_DIR/audiosync"

# Copia ícone do sistema
cp "$INSTALL_DIR/AudioSyncNoText.png" "$DEFAULT_ICON_DIR/audiosync.png"

# Cria atalho no Menu de Aplicativos
echo ""
echo "[4/4] Criando atalhos e integração com o sistema..."
DESKTOP_FILE="$DEFAULT_DESKTOP_DIR/audiosync.desktop"
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronização de Áudio via Rede Local (UDP)
Exec=$LAUNCHER
Icon=$INSTALL_DIR/AudioSyncNoText.png
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

# Pergunta sobre Área de Trabalho
read -p "Deseja criar um atalho na sua Área de Trabalho (Desktop)? [S/n]: " DESKTOP_SHORTCUT
DESKTOP_SHORTCUT="${DESKTOP_SHORTCUT:-S}"
if [[ "$DESKTOP_SHORTCUT" =~ ^[Ss]$ ]]; then
    USER_DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    if [ -d "$USER_DESKTOP_DIR" ]; then
        cp "$DESKTOP_FILE" "$USER_DESKTOP_DIR/audiosync.desktop"
        chmod +x "$USER_DESKTOP_DIR/audiosync.desktop"
        if command -v gio &>/dev/null; then
            gio set "$USER_DESKTOP_DIR/audiosync.desktop" metadata::trusted true 2>/dev/null || true
        fi
        echo "Atalho criado na Área de Trabalho com sucesso!"
    fi
fi

# Cria desinstalador
UNINSTALL_SCRIPT="$INSTALL_DIR/uninstall.sh"
cat << EOF > "$UNINSTALL_SCRIPT"
#!/usr/bin/env bash
echo "Desinstalando AudioSync..."
rm -rf "$INSTALL_DIR"
rm -f "$DEFAULT_DESKTOP_DIR/audiosync.desktop"
rm -f "$DEFAULT_BIN_DIR/audiosync"
rm -f "$HOME/Desktop/audiosync.desktop"
rm -f "$DEFAULT_ICON_DIR/audiosync.png"
echo "AudioSync foi removido com sucesso!"
EOF
chmod +x "$UNINSTALL_SCRIPT"

echo ""
echo "======================================================"
echo "🎉 Instalação concluída com sucesso!"
echo "Você pode abrir o AudioSync de 3 formas:"
echo " 1. Pelo Menu de Aplicativos do sistema (AudioSync)"
echo " 2. Pelo atalho na Área de Trabalho"
echo " 3. Digitando no terminal: audiosync"
echo ""
echo "Desinstalador disponível em: $UNINSTALL_SCRIPT"
echo "======================================================"
echo ""

read -p "Deseja abrir o AudioSync agora? [S/n]: " RUN_NOW
RUN_NOW="${RUN_NOW:-S}"
if [[ "$RUN_NOW" =~ ^[Ss]$ ]]; then
    nohup "$LAUNCHER" >/dev/null 2>&1 &
fi

exit 0
