import os
import sys
import io
import tarfile
import time

def create_ar_archive(members):
    """
    Cria um arquivo no formato Unix ar (utilizado pelo padrão Debian .deb).
    members é uma lista de tuplas: (filename, bytes_data)
    """
    out = io.BytesIO()
    out.write(b"!<arch>\n")
    
    for name, data in members:
        timestamp = str(int(time.time()))
        owner_id = "0"
        group_id = "0"
        mode = "100644"
        size = str(len(data))
        
        header = f"{name:<16}{timestamp:<12}{owner_id:<6}{group_id:<6}{mode:<8}{size:<10}`\n"
        out.write(header.encode("ascii"))
        out.write(data)
        
        # Alinhamento de 2 bytes (se ímpar, adiciona \n)
        if len(data) % 2 != 0:
            out.write(b"\n")
            
    return out.getvalue()

def build_deb(workspace_dir, output_path, version="1.1"):
    print(f"Construindo pacote Debian (.deb) para AudioSync v{version}...")
    
    # 1. debian-binary
    debian_binary = b"2.0\n"
    
    # 2. control.tar.gz
    control_content = f"""Package: audiosync
Version: {version}
Section: sound
Priority: optional
Architecture: all
Maintainer: Rafael Paroni <rafaelparoni.vercel.app>
Depends: python3, python3-tk, pulseaudio-utils, python3-pip, python3-venv, portaudio19-dev, libappindicator3-1 | libayatana-appindicator3-1
Installed-Size: 12000
Homepage: https://rafaelparoni.vercel.app/audio-sync
Description: AudioSync - Espelhamento de audio via rede local (UDP)
 Software para espelhar em tempo real e com baixissima latencia
 todo o audio do computador para outro computador na mesma rede local.
"""

    postinst_content = """#!/bin/sh
set -e

INSTALL_DIR="/opt/audiosync"
VENV_DIR="$INSTALL_DIR/venv"

# Cria ambiente virtual e instala dependências
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR" || true
    if [ -f "$VENV_DIR/bin/pip" ]; then
        "$VENV_DIR/bin/pip" install --upgrade pip -q || true
        "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q || true
    fi
fi

chmod -R a+rx "$INSTALL_DIR" 2>/dev/null || true
chmod 755 /usr/bin/audiosync 2>/dev/null || true

if command -v update-desktop-database > /dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi
if command -v gtk-update-icon-cache > /dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
fi

exit 0
"""

    prerm_content = """#!/bin/sh
set -e
rm -rf /opt/audiosync/venv
exit 0
"""

    control_tar_io = io.BytesIO()
    with tarfile.open(fileobj=control_tar_io, mode="w:gz") as tar:
        # ./control
        ti = tarfile.TarInfo(name="./control")
        ti.size = len(control_content.encode("utf-8"))
        ti.mode = 0o644
        ti.mtime = int(time.time())
        tar.addfile(ti, io.BytesIO(control_content.encode("utf-8")))
        
        # ./postinst
        ti_p = tarfile.TarInfo(name="./postinst")
        ti_p.size = len(postinst_content.encode("utf-8"))
        ti_p.mode = 0o755
        ti_p.mtime = int(time.time())
        tar.addfile(ti_p, io.BytesIO(postinst_content.encode("utf-8")))
        
        # ./prerm
        ti_pr = tarfile.TarInfo(name="./prerm")
        ti_pr.size = len(prerm_content.encode("utf-8"))
        ti_pr.mode = 0o755
        ti_pr.mtime = int(time.time())
        tar.addfile(ti_pr, io.BytesIO(prerm_content.encode("utf-8")))
        
    control_tar_bytes = control_tar_io.getvalue()
    
    # 3. data.tar.gz
    desktop_entry = """[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronização de Áudio via Rede Local (UDP)
Exec=/usr/bin/audiosync
Icon=audiosync
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
"""

    launcher_sh = """#!/bin/sh
INSTALL_DIR="/opt/audiosync"
VENV_DIR="$INSTALL_DIR/venv"

if [ -f "$VENV_DIR/bin/python3" ]; then
    exec "$VENV_DIR/bin/python3" "$INSTALL_DIR/app.py" "$@"
else
    # Fallback se venv não tiver sido criado
    exec python3 "$INSTALL_DIR/app.py" "$@"
fi
"""

    data_tar_io = io.BytesIO()
    with tarfile.open(fileobj=data_tar_io, mode="w:gz") as tar:
        # Adicionar arquivos da aplicação em /opt/audiosync/
        app_files = ["app.py", "client.py", "server.py", "config.json", "requirements.txt", "AudioSyncNoText.png"]
        for fname in app_files:
            fpath = os.path.join(workspace_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                ti = tarfile.TarInfo(name=f"./opt/audiosync/{fname}")
                ti.size = len(content)
                ti.mode = 0o644
                ti.mtime = int(time.time())
                tar.addfile(ti, io.BytesIO(content))
        
        # Launcher /usr/bin/audiosync
        ti_launch = tarfile.TarInfo(name="./usr/bin/audiosync")
        ti_launch.size = len(launcher_sh.encode("utf-8"))
        ti_launch.mode = 0o755
        ti_launch.mtime = int(time.time())
        tar.addfile(ti_launch, io.BytesIO(launcher_sh.encode("utf-8")))
        
        # Desktop Entry
        ti_desk = tarfile.TarInfo(name="./usr/share/applications/audiosync.desktop")
        ti_desk.size = len(desktop_entry.encode("utf-8"))
        ti_desk.mode = 0o644
        ti_desk.mtime = int(time.time())
        tar.addfile(ti_desk, io.BytesIO(desktop_entry.encode("utf-8")))
        
        # Ícone
        icon_path = os.path.join(workspace_dir, "AudioSyncNoText.png")
        if os.path.exists(icon_path):
            with open(icon_path, "rb") as f:
                icon_bytes = f.read()
            ti_icon = tarfile.TarInfo(name="./usr/share/icons/hicolor/128x128/apps/audiosync.png")
            ti_icon.size = len(icon_bytes)
            ti_icon.mode = 0o644
            ti_icon.mtime = int(time.time())
            tar.addfile(ti_icon, io.BytesIO(icon_bytes))

    data_tar_bytes = data_tar_io.getvalue()
    
    # 4. Cria arquivo .deb
    deb_bytes = create_ar_archive([
        ("debian-binary", debian_binary),
        ("control.tar.gz", control_tar_bytes),
        ("data.tar.gz", data_tar_bytes)
    ])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(deb_bytes)
        
    print(f"Sucesso: Pacote .deb gerado com sucesso: {output_path} ({len(deb_bytes)} bytes)")

def build_self_extracting_sh(workspace_dir, output_path, version="1.1"):
    print(f"Construindo instalador universal (.sh) para AudioSync v{version}...")
    
    app_files = ["app.py", "client.py", "server.py", "config.json", "requirements.txt", "AudioSyncNoText.png"]
    payload_io = io.BytesIO()
    with tarfile.open(fileobj=payload_io, mode="w:gz") as tar:
        for fname in app_files:
            fpath = os.path.join(workspace_dir, fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    content = f.read()
                ti = tarfile.TarInfo(name=fname)
                ti.size = len(content)
                ti.mode = 0o644
                ti.mtime = int(time.time())
                tar.addfile(ti, io.BytesIO(content))
    payload_bytes = payload_io.getvalue()
    
    installer_sh_header = f"""#!/usr/bin/env bash
# ==============================================================================
# AudioSync v{version} - Assistente de Instalacao para Linux
# ==============================================================================
set -e

VERSION="{version}"

clear
echo "======================================================"
echo "   AudioSync v$VERSION - Assistente de Instalacao"
echo "   Desenvolvido por Rafael Paroni"
echo "   https://rafaelparoni.vercel.app/audio-sync"
echo "======================================================"
echo ""

# Determina destino padrao
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

read -p "Pasta de instalacao [$DEFAULT_INSTALL_DIR]: " USER_DIR
INSTALL_DIR="${{USER_DIR:-$DEFAULT_INSTALL_DIR}}"

echo ""
echo "[1/4] Verificando dependencias do sistema..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y -q
    sudo apt-get install -y python3 python3-pip python3-tk python3-venv portaudio19-dev pulseaudio-utils libappindicator3-1 gir1.2-appindicator3-0.1 || true
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-pip python3-tkinter portaudio-devel pulseaudio-utils libappindicator-gtk3 || true
elif command -v pacman &> /dev/null; then
    sudo pacman -Syu --noconfirm python python-pip tk portaudio pulseaudio libappindicator-gtk3 || true
fi

echo ""
echo "[2/4] Extraindo arquivos em $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$DEFAULT_BIN_DIR"
mkdir -p "$DEFAULT_DESKTOP_DIR"
mkdir -p "$DEFAULT_ICON_DIR"

PAYLOAD_LINE=$(awk '/^__PAYLOAD_BELOW__/ {{print NR + 1; exit 0; }}' "$0")
tail -n +"$PAYLOAD_LINE" "$0" | tar -xz -C "$INSTALL_DIR"

echo ""
echo "[3/4] Configurando ambiente Python isolado..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

# Cria executavel
LAUNCHER="$INSTALL_DIR/audiosync"
cat << 'EOF_LAUNCHER' > "$LAUNCHER"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/venv/bin/activate"
exec python3 app.py "$@"
EOF_LAUNCHER
chmod +x "$LAUNCHER"

ln -sf "$LAUNCHER" "$DEFAULT_BIN_DIR/audiosync"

if [ -f "$INSTALL_DIR/AudioSyncNoText.png" ]; then
    cp "$INSTALL_DIR/AudioSyncNoText.png" "$DEFAULT_ICON_DIR/audiosync.png"
fi

echo ""
echo "[4/4] Criando atalho no Menu de Aplicativos..."
DESKTOP_FILE="$DEFAULT_DESKTOP_DIR/audiosync.desktop"
cat << EOF_DESK > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Version=1.0
Name=AudioSync
GenericName=Audio Mirroring Tool
Comment=Sincronizacao de Audio via Rede Local (UDP)
Exec=$LAUNCHER
Icon=$INSTALL_DIR/AudioSyncNoText.png
Terminal=false
Categories=AudioVideo;Audio;Network;
Keywords=audio;sync;stream;udp;
StartupNotify=true
EOF_DESK
chmod +x "$DESKTOP_FILE"

read -p "Deseja criar um atalho na Area de Trabalho? [S/n]: " DESK_OPT
DESK_OPT="${{DESK_OPT:-S}}"
if [[ "$DESK_OPT" =~ ^[Ss]$ ]]; then
    USER_DESK="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    if [ -d "$USER_DESK" ]; then
        cp "$DESKTOP_FILE" "$USER_DESK/audiosync.desktop"
        chmod +x "$USER_DESK/audiosync.desktop"
        gio set "$USER_DESK/audiosync.desktop" metadata::trusted true 2>/dev/null || true
    fi
fi

# Desinstalador
UNINSTALL_SH="$INSTALL_DIR/uninstall.sh"
cat << EOF_UN > "$UNINSTALL_SH"
#!/usr/bin/env bash
rm -rf "$INSTALL_DIR"
rm -f "$DEFAULT_DESKTOP_DIR/audiosync.desktop"
rm -f "$DEFAULT_BIN_DIR/audiosync"
rm -f "$HOME/Desktop/audiosync.desktop"
rm -f "$DEFAULT_ICON_DIR/audiosync.png"
echo "AudioSync desinstalado com sucesso!"
EOF_UN
chmod +x "$UNINSTALL_SH"

echo ""
echo "======================================================"
echo "Instalacao concluida com sucesso!"
echo "Comando no terminal: audiosync"
echo "======================================================"
echo ""

read -p "Deseja abrir o AudioSync agora? [S/n]: " RUN_NOW
RUN_NOW="${{RUN_NOW:-S}}"
if [[ "$RUN_NOW" =~ ^[Ss]$ ]]; then
    nohup "$LAUNCHER" >/dev/null 2>&1 &
fi

exit 0
__PAYLOAD_BELOW__
"""
    installer_bytes = installer_sh_header.replace("\r\n", "\n").encode("utf-8") + payload_bytes
    with open(output_path, "wb") as f:
        f.write(installer_bytes)
    print(f"Sucesso: Instalador universal .sh gerado com sucesso: {output_path} ({len(installer_bytes)} bytes)")

if __name__ == "__main__":
    ws = r"d:\Git\AUDIO-SYNC"
    out_deb = os.path.join(ws, "SetupOutput", "AudioSync_Setup_v1.1.deb")
    out_sh = os.path.join(ws, "SetupOutput", "AudioSync_Setup_v1.1.sh")
    build_deb(ws, out_deb)
    build_self_extracting_sh(ws, out_sh)
