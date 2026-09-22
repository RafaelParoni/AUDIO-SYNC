# AudioSync 🎧

[![Portuguese](https://img.shields.io/badge/Language-Português-green.svg)](#português)
[![English](https://img.shields.io/badge/Language-English-blue.svg)](#english)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue.svg)](#)

---

<a id="português"></a>
## 🇧🇷 Português

O **AudioSync** é um software multiplataforma criado para espelhar, em tempo real e com baixíssima latência (via UDP), todo o áudio do seu computador (como um Notebook) diretamente para as caixas de som de outro computador (como um PC Desktop) na mesma rede local.

O aplicativo opera de forma nativa e sem fricção:
- No **Windows**: utiliza `pyaudiowpatch` integrado à API nativa **WASAPI** (Loopback), capturando o áudio do sistema sem necessitar de Stereo Mix ou cabos virtuais.
- No **Linux**: utiliza o **PulseAudio** ou **PipeWire** (captura nativa do monitor do dispositivo padrão de saída), integrado através do PyAudio.

Ambos os sistemas operacionais podem atuar tanto como **Servidor** (quem toca o som) quanto como **Cliente** (quem envia o som), permitindo sincronizar livremente entre Windows e Linux (ex: Notebook Linux -> Desktop Windows, ou vice-versa).

### 🌟 Funcionalidades
- **Modo Servidor & Cliente:** Configure facilmente qual máquina irá Enviar o som (Client) e qual irá Receber (Server).
- **Multiplataforma:** Suporte total para **Windows** (10/11) e distribuições **Linux** (Ubuntu, Debian, Fedora, Arch, Mint, Pop!_OS, etc.).
- **Interface Gráfica Premium:** Criada com CustomTkinter com paleta estética moderna (Ciano/Azul Escuro).
- **Console de Logs:** Visualize erros ou as conexões (Server/Client) em tempo real de forma prática usando o menu da aplicação.
- **Autostart & Autosync:** Inicia automaticamente junto ao sistema operacional (Registro no Windows, especificação XDG `.desktop` no Linux) e conecta a sincronização no boot.
- **System Tray:** Roda minimizado na bandeja do sistema para não ocupar espaço na sua barra de tarefas.
- **Instaladores Dedicados:** Empacotado com Inno Setup (`.exe`) para Windows e script automatizado de instalação (`install_linux.sh`) com entrada de aplicativo (`.desktop`) para Linux.

---

### ⚙️ Como Usar

1. Execute o AudioSync em ambas as máquinas (Notebook e Desktop).
2. **No computador que vai TOCAR o som (Recebedor):**
   - Selecione o modo `Servidor (PC Desktop - Recebe)`.
   - Anote o IP exibido na tela (`IP DESTE COMPUTADOR`).
   - Clique em **INICIAR**.
3. **No computador que vai ENVIAR o som (Transmissor):**
   - Selecione o modo `Cliente (Notebook - Envia)`.
   - Digite o IP do Servidor no campo de texto.
   - Clique em **INICIAR**.
4. Pronto! O áudio do computador transmissor será tocado imediatamente no receptor.

---

### 🐧 Instalação no Linux

#### 1. Assistente de Instalação (Setup Wizard)
Assim como no Windows, você pode rodar o assistente interativo de instalação que configura o diretório de instalação, instala as dependências, cria os atalhos no Menu e na Área de Trabalho e inclui o desinstalador:
```bash
git clone https://github.com/RafaelParoni/AUDIO-SYNC.git
cd AUDIO-SYNC
chmod +x AudioSync_Setup_Linux.sh
./AudioSync_Setup_Linux.sh
```

#### 2. Gerar Instaladores (.deb e .sh auto-extraível) para Distribuição
Para gerar os pacotes prontos de distribuição na pasta `SetupOutput/`:
```bash
chmod +x build_linux_setup.sh
./build_linux_setup.sh
```
Isso gerará dentro de `SetupOutput/`:
- `AudioSync_v1.1_amd64.deb` (Instalador `.deb` para Ubuntu, Debian, Mint)
- `AudioSync_Setup_v1.1.sh` (Instalador auto-extraível universal para qualquer Linux)

#### Instalação Manual no Linux
1. Instale as dependências do sistema:
   - **Debian / Ubuntu / Mint:**
     ```bash
     sudo apt update && sudo apt install -y python3 python3-pip python3-tk python3-venv portaudio19-dev pulseaudio-utils libappindicator3-1 gir1.2-appindicator3-0.1
     ```
   - **Fedora:**
     ```bash
     sudo dnf install -y python3 python3-pip python3-tkinter portaudio-devel pulseaudio-utils libappindicator-gtk3
     ```
   - **Arch Linux:**
     ```bash
     sudo pacman -S python python-pip tk portaudio pulseaudio libappindicator-gtk3
     ```
2. Crie e ative o ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Execute o programa:
   ```bash
   python3 app.py
   ```

---

### 🪟 Instalação no Windows

1. Baixe o instalador gerado `AudioSync_Setup_v1.1.exe` na aba de Releases ou gere o instalador com o Inno Setup.
2. Ou execute a partir do código-fonte (requer Python 3.10+):
   ```bash
   git clone https://github.com/RafaelParoni/AUDIO-SYNC.git
   cd AUDIO-SYNC
   pip install -r requirements.txt
   python app.py
   ```

---

<a id="english"></a>
## 🇺🇸 English

**AudioSync** is a cross-platform tool designed to mirror, in real-time and with ultra-low latency (via UDP), all the audio playing on one computer (such as a Laptop) directly to the speakers of another computer (such as a Desktop PC) on the same local network.

AudioSync operates natively across platforms:
- On **Windows**: leverages `pyaudiowpatch` coupled with the native **WASAPI** loopback API, capturing system audio without requiring Stereo Mix or virtual audio cables.
- On **Linux**: captures from **PulseAudio** or **PipeWire** (native monitor source of the default output sink), integrated through PyAudio.

Both systems can act either as **Server** (receiver/playback) or **Client** (transmitter/capture), enabling seamless interoperability between Windows and Linux machines.

### 🌟 Features
- **Server & Client Modes:** Easily configure which machine will Send the audio (Client) and which will Receive (Server).
- **Cross-Platform:** Full support for **Windows** (10/11) and **Linux** distributions (Ubuntu, Debian, Fedora, Arch, Mint, Pop!_OS, etc.).
- **Premium GUI:** Built with CustomTkinter featuring a clean, dark-mode gradient aesthetic (Cyan/Dark Blue).
- **Real-Time Log Console:** Quickly troubleshoot connections and audio device discovery in real time.
- **Autostart & Autosync:** Capability to run silently on system startup (Windows Registry / Linux XDG `.desktop`) and automatically establish the audio stream.
- **System Tray:** Minimizes to the system tray to stay out of the taskbar.
- **Dedicated Installers:** Inno Setup (`.exe`) for Windows and an automated setup script (`install_linux.sh`) with desktop integration for Linux.

---

### ⚙️ How to Use

1. Launch AudioSync on both computers (Laptop and Desktop).
2. **On the PC that will PLAY the sound (Receiver):**
   - Select `Server` mode.
   - Note down the IP displayed on the screen (`IP DESTE COMPUTADOR`).
   - Click **INICIAR**.
3. **On the PC that will SEND the sound (Transmitter):**
   - Select `Client` mode.
   - Enter the Server's IP address into the input box.
   - Click **INICIAR**.
4. Done! Audio will be streamed with ultra-low latency.

---

### 🐧 Linux Installation

#### 1. Setup Wizard
Just like on Windows, you can run an interactive installation wizard that configures the installation directory, installs dependencies, creates desktop and menu shortcuts, and includes an uninstaller:
```bash
git clone https://github.com/RafaelParoni/AUDIO-SYNC.git
cd AUDIO-SYNC
chmod +x AudioSync_Setup_Linux.sh
./AudioSync_Setup_Linux.sh
```

#### 2. Building Packages (.deb and standalone .sh) for Distribution
To generate standalone installer packages in `SetupOutput/`:
```bash
chmod +x build_linux_setup.sh
./build_linux_setup.sh
```
This builds inside `SetupOutput/`:
- `AudioSync_v1.1_amd64.deb` (Debian/Ubuntu/Mint installer package)
- `AudioSync_Setup_v1.1.sh` (Self-extracting universal installer for any Linux distro)

#### Manual Setup
1. Install system dependencies:
   - **Debian / Ubuntu / Mint:**
     ```bash
     sudo apt update && sudo apt install -y python3 python3-pip python3-tk python3-venv portaudio19-dev pulseaudio-utils libappindicator3-1 gir1.2-appindicator3-0.1
     ```
   - **Fedora:**
     ```bash
     sudo dnf install -y python3 python3-pip python3-tkinter portaudio-devel pulseaudio-utils libappindicator-gtk3
     ```
   - **Arch Linux:**
     ```bash
     sudo pacman -S python python-pip tk portaudio pulseaudio libappindicator-gtk3
     ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python3 app.py
   ```

---

> 🖥️ Developed by **[Rafael Paroni](https://rafaelparoni.vercel.app/audio-sync)**.
