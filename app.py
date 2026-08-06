import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import sys
import winreg
import socket

# Pystray para a bandeja do sistema
import pystray
from PIL import Image, ImageDraw

# Importa as funções que criamos em server.py e client.py
from server import run_server
from client import run_client

CONFIG_FILE = "config.json"
APP_NAME = "AudioSync"

def get_script_path():
    """Retorna o caminho absoluto do executável ou script em execução."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__)

def get_config_path():
    """O config.json será salvo na mesma pasta do executável."""
    return os.path.join(os.path.dirname(get_script_path()), CONFIG_FILE)

def get_local_ip():
    """Tenta descobrir o IP local da máquina"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def create_tray_icon_image():
    """Gera um ícone simples para a bandeja do sistema (se não houver um .ico)"""
    image = Image.new('RGB', (64, 64), color=(30, 30, 30))
    d = ImageDraw.Draw(image)
    # Desenha um quadrado verde no meio
    d.rectangle([16, 16, 48, 48], fill=(0, 200, 0))
    return image

class AudioSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Sync Launcher")
        self.root.geometry("400x380")
        self.root.resizable(False, False)
        
        # Configurações padrão
        self.config = {
            "mode": "server", 
            "ip": "", 
            "autostart": False,
            "autosync": False
        }
        self.load_config()
        
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.tray_icon = None

        self.setup_ui()
        self.setup_tray()
        
        # Intercepta o botão de fechar (X)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Verifica se o programa foi iniciado automaticamente pelo Windows
        if "--autostart" in sys.argv:
            # Esconde a janela
            self.root.withdraw()
            if self.config.get("autosync", False):
                self.start_sync()
            
    def load_config(self):
        try:
            if os.path.exists(get_config_path()):
                with open(get_config_path(), "r") as f:
                    self.config.update(json.load(f))
        except Exception:
            pass

    def save_config(self):
        try:
            with open(get_config_path(), "w") as f:
                json.dump(self.config, f)
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            
    def toggle_autostart(self):
        self.config["autostart"] = self.autostart_var.get()
        self.save_config()
        self.apply_autostart(self.config["autostart"])
        
    def toggle_autosync(self):
        self.config["autosync"] = self.autosync_var.get()
        self.save_config()

    def apply_autostart(self, enable):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                cmd = f'"{get_script_path()}" --autostart'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showerror("Erro de Permissão", f"Falha ao configurar inicialização automática:\n{e}")

    def setup_ui(self):
        self.mode_var = tk.StringVar(value=self.config["mode"])
        
        # Exibe IP Local
        self.local_ip = get_local_ip()
        tk.Label(self.root, text=f"IP DESTE COMPUTADOR: {self.local_ip}", 
                 fg="darkred", font=("Arial", 11, "bold")).pack(pady=10)

        # Seção do Modo de Operação
        frame_mode = tk.LabelFrame(self.root, text="Modo de Operação", padx=10, pady=10)
        frame_mode.pack(fill="x", padx=10, pady=5)
        
        tk.Radiobutton(frame_mode, text="Servidor (PC Desktop - Recebe Áudio)", 
                       variable=self.mode_var, value="server", 
                       command=self.on_mode_change).pack(anchor="w")
        tk.Radiobutton(frame_mode, text="Cliente (Notebook - Envia Áudio)", 
                       variable=self.mode_var, value="client", 
                       command=self.on_mode_change).pack(anchor="w")
        
        # Seção de Configuração do Outro IP
        self.frame_ip = tk.Frame(self.root)
        self.ip_label = tk.Label(self.frame_ip, text="IP do Cliente (Notebook):")
        self.ip_label.pack(side="left")
        self.ip_entry = tk.Entry(self.frame_ip, width=15)
        self.ip_entry.insert(0, self.config["ip"])
        self.ip_entry.pack(side="left", padx=5)
        self.frame_ip.pack(fill="x", padx=15, pady=5)
        
        # Atualiza o texto da label do IP
        self.on_mode_change()
        
        # Autostart e AutoSync
        self.autostart_var = tk.BooleanVar(value=self.config.get("autostart", False))
        tk.Checkbutton(self.root, text="Iniciar automaticamente com o Windows (Oculto)", 
                       variable=self.autostart_var, 
                       command=self.toggle_autostart).pack(anchor="w", padx=15, pady=2)
                       
        self.autosync_var = tk.BooleanVar(value=self.config.get("autosync", False))
        tk.Checkbutton(self.root, text="Iniciar Sincronização Automaticamente ao abrir", 
                       variable=self.autosync_var, 
                       command=self.toggle_autosync).pack(anchor="w", padx=15, pady=2)

        # Labels de Status
        self.status_var = tk.StringVar(value="Status: Parado")
        tk.Label(self.root, textvariable=self.status_var, fg="blue", font=("Arial", 9, "bold")).pack(pady=5)

        # Botões Iniciar e Parar
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(pady=5)
        
        self.btn_start = tk.Button(frame_btns, text="Iniciar", command=self.start_sync, bg="lightgreen", width=12, font=("Arial", 10, "bold"))
        self.btn_start.pack(side="left", padx=10)
        
        self.btn_stop = tk.Button(frame_btns, text="Parar", command=self.stop_sync, bg="salmon", width=12, state="disabled", font=("Arial", 10, "bold"))
        self.btn_stop.pack(side="left", padx=10)

    def on_mode_change(self):
        """Muda o texto do campo de IP dependendo do modo"""
        if self.mode_var.get() == "server":
            self.ip_label.config(text="IP do Cliente (Notebook):")
        else:
            self.ip_label.config(text="IP do Servidor (PC):")

    def set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(f"Status: {text}"))

    def start_sync(self):
        if self.is_running: return
        
        mode = self.mode_var.get()
        ip = self.ip_entry.get().strip()
        
        if not ip:
            messagebox.showerror("Erro", "Por favor, insira o IP do outro computador.")
            return

        self.config["mode"] = mode
        self.config["ip"] = ip
        self.save_config()
        
        self.stop_event.clear()
        
        if mode == "server":
            self.worker_thread = threading.Thread(target=run_server, args=(ip, self.stop_event, self.set_status), daemon=True)
        else:
            self.worker_thread = threading.Thread(target=run_client, args=(ip, self.stop_event, self.set_status), daemon=True)
            
        self.worker_thread.start()
        self.is_running = True
        
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.ip_entry.config(state="disabled")

    def stop_sync(self):
        if not self.is_running: return
        self.stop_event.set()
        self.set_status("Parando...")
        self.is_running = False
        
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.ip_entry.config(state="normal")

    # ==========================
    # Lógica do System Tray
    # ==========================
    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Abrir AudioSync', self.show_window),
            pystray.MenuItem('Sair Completamente', self.quit_app)
        )
        self.tray_icon = pystray.Icon("AudioSync", create_tray_icon_image(), "AudioSync", menu)
        # Roda o ícone em uma thread separada para não travar o tkinter
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        """Ao clicar no X, apenas esconde a janela."""
        self.root.withdraw()
        
    def show_window(self, icon=None, item=None):
        """Restaura a janela do modo oculto."""
        # after() garante que a chamada ocorra na main thread do tkinter
        self.root.after(0, self.root.deiconify)
        
    def quit_app(self, icon=None, item=None):
        """Fecha a aplicação de verdade."""
        self.stop_event.set()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSyncApp(root)
    root.mainloop()
