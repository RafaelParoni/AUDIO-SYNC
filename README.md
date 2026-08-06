# AudioSync 🎧

[![Portuguese](https://img.shields.io/badge/Language-Português-green.svg)](#português)
[![English](https://img.shields.io/badge/Language-English-blue.svg)](#english)

---

<a id="português"></a>
## 🇧🇷 Português

O **AudioSync** é um software criado para espelhar, em tempo real e com baixíssima latência (via UDP), todo o áudio do seu computador (como um Notebook) diretamente para as caixas de som de outro computador (como um PC Desktop) na mesma rede local.

O aplicativo utiliza a biblioteca `pyaudiowpatch` integrada à API nativa **WASAPI** do Windows, o que permite capturar o áudio (Loopback) sem a necessidade de ativadores como "Stereo Mix". Tudo é encapsulado em uma interface linda e moderna feita com `CustomTkinter`.

### 🌟 Funcionalidades
- **Modo Servidor & Cliente:** Configure facilmente qual máquina irá Enviar o som (Client) e qual irá Receber (Server).
- **Interface Gráfica Premium:** Criada com CustomTkinter com gradientes estéticos (Ciano/Azul Escuro).
- **Console de Logs:** Visualize erros ou as conexões (Server/Client) em tempo real de forma prática usando o sistema nativo de menu.
- **Autostart & Autosync:** Capacidade de iniciar automaticamente junto ao Windows (salva no Registro) e iniciar a sincronização (Client/Server) automaticamente ao abrir.
- **System Tray:** Roda oculto na bandeja do sistema para não incomodar na sua barra de tarefas.
- **Instalador Inno Setup:** Empacotado perfeitamente em um instalador fácil e prático de usar (`.exe`).

### ⚙️ Como Usar (Versão Portátil/Instalada)
1. Baixe o instalador gerado `AudioSync_Setup_v1.1.exe`.
2. Instale em ambas as máquinas (Notebook e Desktop).
3. **No PC que vai TOCAR o som (Recebedor):** Selecione o modo `Server`, anote o IP exibido na tela, e clique em Iniciar.
4. **No PC que vai ENVIAR o som (Transmissor):** Selecione o modo `Client`, digite o IP do Servidor na caixa de texto, e clique em Iniciar.
5. Pronto! O áudio já estará sincronizado.

### 🛠️ Para Desenvolvedores (Rodando da Fonte)
Você precisa ter o Python 3.10+ instalado no Windows.
```bash
git clone https://github.com/RafaelParoni/AUDIO-SYNC.git
cd AUDIO-SYNC
pip install -r requirements.txt
python app.py
```
*(Para gerar o executável você mesmo, certifique-se de usar o PyInstaller ou InnoSetup fornecidos na raiz do projeto).*

---

<a id="english"></a>
## 🇺🇸 English

**AudioSync** is a software designed to mirror, in real-time and with ultra-low latency (via UDP), all the audio playing on one computer (like a Laptop) directly to the speakers of another computer (like a Desktop PC) on the same local network.

The application leverages the `pyaudiowpatch` library integrated with the native Windows **WASAPI** loopback API, capturing your system audio effortlessly without the need to mess around with "Stereo Mix". Everything is encapsulated in a beautiful and modern UI built with `CustomTkinter`.

### 🌟 Features
- **Server & Client Modes:** Easily configure which machine will Send the audio (Client) and which will Receive (Server).
- **Premium GUI:** Built with CustomTkinter featuring aesthetic gradients (Cyan/Dark Blue).
- **Real-Time Log Console:** Quickly check connections or troubleshoot errors using the native Dropdown Menu.
- **Autostart & Autosync:** Capability to automatically run on Windows Startup (via Registry) and start the syncing connection automatically.
- **System Tray:** Runs hidden in the system tray so it doesn't clutter your taskbar.
- **Inno Setup Installer:** Perfectly packaged into a ready-to-use `.exe` installer.

### ⚙️ How to Use (Installed/Standalone)
1. Download the generated installer `AudioSync_Setup_v1.1.exe`.
2. Install it on both machines (Laptop and Desktop).
3. **On the PC that will PLAY the sound (Receiver):** Select `Server` mode, note the IP address shown on the screen, and click Start.
4. **On the PC that will SEND the sound (Transmitter):** Select `Client` mode, type the Server's IP address into the input box, and click Start.
5. Done! Your audio will be seamlessly synchronized.

### 🛠️ For Developers (Running from Source)
You need to have Python 3.10+ installed on Windows.
```bash
git clone https://github.com/RafaelParoni/AUDIO-SYNC.git
cd AUDIO-SYNC
pip install -r requirements.txt
python app.py
```
*(To build the executable yourself, make sure to use PyInstaller or the provided InnoSetup script in the project root).*

---
> 🖥️ Developed by **[Rafael Paroni](https://rafaelparoni.vercel.app/audio-sync)**.
