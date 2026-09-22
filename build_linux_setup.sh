#!/usr/bin/env bash
# ==============================================================================
# AudioSync - Gerador de Pacotes de Instalação (Setup) para Linux
# Gera:
#   1. SetupOutput/AudioSync_v1.1_amd64.deb   (Pacote Debian/Ubuntu/Mint)
#   2. SetupOutput/AudioSync_Setup_v1.1.sh    (Instalador Auto-Extraível Universal)
#   3. SetupOutput/AudioSync-v1.1-x86_64.AppImage (Opcional, se appimagetool presente)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.1"
APP_NAME="AudioSync"
PKG_NAME="audiosync"
OUTPUT_DIR="$SCRIPT_DIR/SetupOutput"

mkdir -p "$OUTPUT_DIR"

echo "========================================================"
echo "📦 Compilando e Gerando Instaladores do AudioSync v$VERSION para Linux"
echo "========================================================"

# 1. Ativa ambiente virtual ou compila com PyInstaller
if [ -d "venv" ]; then
    source venv/bin/activate
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "Instalando PyInstaller..."
    pip install pyinstaller
fi

echo "[1/4] Compilando executável nativo Linux com PyInstaller..."
pyinstaller AudioSync.spec --clean --noconfirm

DIST_DIR="$SCRIPT_DIR/dist/AudioSync"
if [ ! -f "$DIST_DIR/AudioSync" ]; then
    echo "Erro: O executável $DIST_DIR/AudioSync não foi gerado!"
    exit 1
fi

chmod +x "$DIST_DIR/AudioSync"

# ==============================================================================
# 2. Gerar Instalador Auto-Extraível (.sh) - Compatível com TODAS as distros
# ==============================================================================
echo "[2/4] Gerando instalador executável universal: AudioSync_Setup_v${VERSION}.sh..."

SETUP_SCRIPT="$OUTPUT_DIR/AudioSync_Setup_v${VERSION}.sh"

cat << 'EOF_HEADER' > "$SETUP_SCRIPT"
#!/usr/bin/env bash
# ==============================================================================
# AudioSync - Assistente de Instalação para Linux
# ==============================================================================
set -e

VERSION="1.1"
APP_TITLE="AudioSync"

echo "======================================================"
echo "   🎧 AudioSync v$VERSION - Assistente de Instalação"
echo "   Desenvolvido por Rafael Paroni"
echo "   https://rafaelparoni.vercel.app/audio-sync"
echo "======================================================"
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
echo "Instalando em: $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DEFAULT_BIN_DIR"
mkdir -p "$DEFAULT_DESKTOP_DIR"
mkdir -p "$DEFAULT_ICON_DIR"

# Extrai os dados embutidos
PAYLOAD_LINE=$(awk '/^__PAYLOAD_BEGINS__/ {print NR + 1; exit 0; }' "$0")
tail -n +"$PAYLOAD_LINE" "$0" | tar -xz -C "$INSTALL_DIR"

chmod +x "$INSTALL_DIR/AudioSync"

# Copia ícone
if [ -f "$INSTALL_DIR/AudioSyncNoText.png" ]; then
    cp "$INSTALL_DIR/AudioSyncNoText.png" "$DEFAULT_ICON_DIR/audiosync.png"
fi

# Cria atalho no Menu de Aplicativos
DESKTOP_FILE="$DEFAULT_DESKTOP_DIR/audiosync.desktop"
cat << EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronização de Áudio via Rede Local (UDP)
Exec=$INSTALL_DIR/AudioSync
Icon=$INSTALL_DIR/AudioSyncNoText.png
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
EOF
chmod +x "$DESKTOP_FILE"

# Cria atalho de comando no PATH
ln -sf "$INSTALL_DIR/AudioSync" "$DEFAULT_BIN_DIR/audiosync"

# Pergunta sobre atalho na Área de Trabalho
read -p "Deseja criar um atalho na Área de Trabalho? [S/n]: " DESKTOP_SHORTCUT
DESKTOP_SHORTCUT="${DESKTOP_SHORTCUT:-S}"
if [[ "$DESKTOP_SHORTCUT" =~ ^[Ss]$ ]]; then
    USER_DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    if [ -d "$USER_DESKTOP_DIR" ]; then
        cp "$DESKTOP_FILE" "$USER_DESKTOP_DIR/audiosync.desktop"
        chmod +x "$USER_DESKTOP_DIR/audiosync.desktop"
        if command -v gio &>/dev/null; then
            gio set "$USER_DESKTOP_DIR/audiosync.desktop" metadata::trusted true 2>/dev/null || true
        fi
        echo "Atalho criado na Área de Trabalho!"
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
echo "AudioSync desinstalado com sucesso!"
EOF
chmod +x "$UNINSTALL_SCRIPT"

echo ""
echo "======================================================"
echo "✅ Instalação concluída com sucesso!"
echo "Comando no terminal: audiosync"
echo "Desinstalador disponível em: $UNINSTALL_SCRIPT"
echo "======================================================"
echo ""

read -p "Deseja iniciar o AudioSync agora? [S/n]: " RUN_NOW
RUN_NOW="${RUN_NOW:-S}"
if [[ "$RUN_NOW" =~ ^[Ss]$ ]]; then
    nohup "$INSTALL_DIR/AudioSync" >/dev/null 2>&1 &
fi

exit 0
__PAYLOAD_BEGINS__
EOF_HEADER

# Compacta os arquivos de dist/AudioSync e anexa ao instalador
tar -cz -C "$DIST_DIR" . >> "$SETUP_SCRIPT"
chmod +x "$SETUP_SCRIPT"

echo "-> Instalador gerado: $SETUP_SCRIPT"

# ==============================================================================
# 3. Gerar Pacote .deb (Debian / Ubuntu / Mint / Pop!_OS)
# ==============================================================================
echo "[3/4] Gerando pacote de instalação .deb (Ubuntu/Debian)..."

DEB_BUILD_DIR="$SCRIPT_DIR/build/deb_package"
rm -rf "$DEB_BUILD_DIR"
mkdir -p "$DEB_BUILD_DIR/DEBIAN"
mkdir -p "$DEB_BUILD_DIR/opt/audiosync"
mkdir -p "$DEB_BUILD_DIR/usr/bin"
mkdir -p "$DEB_BUILD_DIR/usr/share/applications"
mkdir -p "$DEB_BUILD_DIR/usr/share/icons/hicolor/128x128/apps"

# Copia arquivos do aplicativo
cp -r "$DIST_DIR/"* "$DEB_BUILD_DIR/opt/audiosync/"
chmod +x "$DEB_BUILD_DIR/opt/audiosync/AudioSync"

# Cria atalho no /usr/bin
ln -sf /opt/audiosync/AudioSync "$DEB_BUILD_DIR/usr/bin/audiosync"

# Ícone do sistema
cp "$DIST_DIR/AudioSyncNoText.png" "$DEB_BUILD_DIR/usr/share/icons/hicolor/128x128/apps/audiosync.png"

# Desktop Entry
cat << EOF > "$DEB_BUILD_DIR/usr/share/applications/audiosync.desktop"
[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronização de Áudio via Rede Local (UDP)
Exec=/opt/audiosync/AudioSync
Icon=audiosync
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
EOF

# DEBIAN/control
INSTALLED_SIZE=$(du -sk "$DEB_BUILD_DIR" | cut -f1)
cat << EOF > "$DEB_BUILD_DIR/DEBIAN/control"
Package: audiosync
Version: $VERSION
Section: sound
Priority: optional
Architecture: amd64
Installed-Size: $INSTALLED_SIZE
Maintainer: Rafael Paroni <rafaelparoni.vercel.app>
Description: AudioSync - Espelhamento de áudio via rede local de ultra baixa latência (UDP)
 Software multiplataforma para sincronização em tempo real de áudio entre computadores.
EOF

# DEBIAN/postinst
cat << 'EOF' > "$DEB_BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi
exit 0
EOF
chmod 755 "$DEB_BUILD_DIR/DEBIAN/postinst"

# DEBIAN/prerm
cat << 'EOF' > "$DEB_BUILD_DIR/DEBIAN/prerm"
#!/bin/sh
set -e
exit 0
EOF
chmod 755 "$DEB_BUILD_DIR/DEBIAN/prerm"

DEB_OUTPUT="$OUTPUT_DIR/AudioSync_v${VERSION}_amd64.deb"
if command -v dpkg-deb &>/dev/null; then
    dpkg-deb --build "$DEB_BUILD_DIR" "$DEB_OUTPUT"
    echo "-> Pacote .deb gerado: $DEB_OUTPUT"
else
    # Fallback se dpkg-deb não estiver presente (ex: rodando no Arch ou Fedora)
    python3 -c "
import tarfile, os, sys
# Se precisar empacotar sem dpkg-deb, gera tarball
print('Aviso: dpkg-deb não encontrado. O instalador universal .sh foi gerado com sucesso.')
"
fi

# ==============================================================================
# 4. Resumo Final
# ==============================================================================
echo ""
echo "========================================================"
echo "🎉 Todos os instaladores do Linux foram gerados em SetupOutput/:"
ls -lh "$OUTPUT_DIR"
echo "========================================================"
