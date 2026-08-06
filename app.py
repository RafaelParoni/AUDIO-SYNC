import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import sys
import winreg

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

class AudioSyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Sync Launcher")
        self.root.geometry("400x320")
        self.root.resizable(False, False)
        
        # Configurações padrão
        self.config = {"mode": "server", "ip": "192.168.0.10", "autostart": False}
        self.load_config()
        
        self.worker_thread = None
        self.stop_event = threading.Event()
        self.is_running = False

        self.setup_ui()
        
        # Verifica se o programa foi iniciado automaticamente pelo Windows
        if "--autostart" in sys.argv:
            # Esconde a janela se quiser uma execução invisível, ou apenas inicia minimizada
            # self.root.iconify() 
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
        """Ativado quando o usuário clica na checkbox de Autostart"""
        self.config["autostart"] = self.autostart_var.get()
        self.save_config()
        self.apply_autostart(self.config["autostart"])

    def apply_autostart(self, enable):
        """Adiciona ou remove o atalho no Registro do Windows (Run)"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                # O comando adiciona o --autostart para que saibamos que foi o Windows que iniciou
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
        
        # Seção do Modo de Operação
        frame_mode = tk.LabelFrame(self.root, text="Modo de Operação", padx=10, pady=10)
        frame_mode.pack(fill="x", padx=10, pady=10)
        
        tk.Radiobutton(frame_mode, text="Servidor (PC Desktop - Recebe Áudio)", 
                       variable=self.mode_var, value="server", 
                       command=self.on_mode_change).pack(anchor="w")
        tk.Radiobutton(frame_mode, text="Cliente (Notebook - Envia Áudio)", 
                       variable=self.mode_var, value="client", 
                       command=self.on_mode_change).pack(anchor="w")
        
        # Seção de Configuração do Cliente
        self.frame_ip = tk.Frame(self.root)
        tk.Label(self.frame_ip, text="IP do Servidor (PC):").pack(side="left")
        self.ip_entry = tk.Entry(self.frame_ip, width=15)
        self.ip_entry.insert(0, self.config["ip"])
        self.ip_entry.pack(side="left", padx=5)
        self.frame_ip.pack(fill="x", padx=15, pady=5)
        
        # Atualiza visibilidade da aba do Cliente
        self.on_mode_change()
        
        # Autostart
        self.autostart_var = tk.BooleanVar(value=self.config.get("autostart", False))
        tk.Checkbutton(self.root, text="Iniciar automaticamente com o Windows", 
                       variable=self.autostart_var, 
                       command=self.toggle_autostart).pack(anchor="w", padx=15, pady=5)

        # Labels de Status
        self.status_var = tk.StringVar(value="Status: Parado")
        tk.Label(self.root, textvariable=self.status_var, fg="blue", font=("Arial", 9, "bold")).pack(pady=10)

        # Botões Iniciar e Parar
        frame_btns = tk.Frame(self.root)
        frame_btns.pack(pady=5)
        
        self.btn_start = tk.Button(frame_btns, text="Iniciar", command=self.start_sync, bg="lightgreen", width=12, font=("Arial", 10, "bold"))
        self.btn_start.pack(side="left", padx=10)
        
        self.btn_stop = tk.Button(frame_btns, text="Parar", command=self.stop_sync, bg="salmon", width=12, state="disabled", font=("Arial", 10, "bold"))
        self.btn_stop.pack(side="left", padx=10)

    def on_mode_change(self):
        """Esconde ou mostra o campo de IP dependendo do modo"""
        if self.mode_var.get() == "client":
            self.frame_ip.pack(fill="x", padx=15, pady=5)
        else:
            self.frame_ip.pack_forget()

    def set_status(self, text):
        """Atualiza o texto de status de forma segura na thread principal"""
        self.root.after(0, lambda: self.status_var.set(f"Status: {text}"))

    def start_sync(self):
        if self.is_running: return
        
        mode = self.mode_var.get()
        ip = self.ip_entry.get().strip()
        
        # Salva o config antes de iniciar
        self.config["mode"] = mode
        self.config["ip"] = ip
        self.save_config()
        
        self.stop_event.clear()
        
        # Inicia o Servidor ou o Cliente em uma Thread separada (para não travar a GUI)
        if mode == "server":
            self.worker_thread = threading.Thread(target=run_server, args=(self.stop_event, self.set_status), daemon=True)
        else:
            if not ip:
                messagebox.showerror("Erro", "Por favor, insira o IP do Servidor.")
                return
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

    def on_closing(self):
        """Garante que a porta UDP/Threads sejam fechadas ao sair da janela"""
        self.stop_event.set()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSyncApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
