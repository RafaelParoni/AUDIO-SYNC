import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import sys
import winreg
import socket

import pystray
from PIL import Image, ImageDraw
import logging
import webbrowser

# Configura o sistema de logs
logging.basicConfig(
    filename='audiosync.log', 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            try:
                self.text_widget.configure(state="normal")
                self.text_widget.insert("end", msg + "\n")
                self.text_widget.configure(state="disabled")
                self.text_widget.yview("end")
            except:
                pass
        self.text_widget.after(0, append)

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

def get_data_dir():
    """Retorna o diretório correto contendo os arquivos de data (ícones etc), funciona no Python puro e PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# Força o Windows a reconhecer o app como um programa independente (corrige o ícone na barra de tarefas)
try:
    import ctypes
    myappid = 'rafaelparoni.audiosync.launcher.1.1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

def create_tray_icon_image():
    """Gera um ícone simples para a bandeja do sistema ou carrega o do usuário"""
    icon_path = os.path.join(get_data_dir(), "audioSyncNoText.png")
    try:
        return Image.open(icon_path)
    except Exception:
        image = Image.new('RGB', (64, 64), color=(0, 0, 0))
        d = ImageDraw.Draw(image)
        d.rectangle([16, 16, 48, 48], fill=(0, 200, 0))
        return image

class AudioSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuração do CustomTkinter
        ctk.set_appearance_mode("dark")  # Modo Escuro
        ctk.set_default_color_theme("blue")
        
        self.title("AudioSync Launcher")
        self.geometry("450x550")
        self.resizable(False, False)
        
        try:
            # Pega o diretório base correto
            base_dir = get_data_dir()
            icon_path_png = os.path.join(base_dir, "audioSyncNoText.png")
            icon_path_ico = os.path.join(base_dir, "AudioSyncNoText.ico")
            
            self._icon_img = tk.PhotoImage(file=icon_path_png)
            
            def apply_icon():
                try:
                    self.iconphoto(True, self._icon_img)
                    self.wm_iconphoto(True, self._icon_img)
                except Exception as e:
                    logging.error(f"Erro photo: {e}")
                
                try:
                    self.iconbitmap(icon_path_ico)
                    self.wm_iconbitmap(icon_path_ico)
                except Exception as e:
                    pass
                    
            apply_icon()
            self.after(200, apply_icon)
            self.after(500, apply_icon)
        except Exception as e:
            logging.error(f"Erro ao carregar icone da janela: {e}")
        
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
        self.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        # Verifica se o programa foi iniciado automaticamente pelo Windows
        if "--autostart" in sys.argv:
            self.withdraw()
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
        # Gradiente Baseado no seu Portfólio: #5DE0E6 -> #004AAD
        c_cyan = (93, 224, 230)
        c_blue = (0, 74, 173)
        
        btn_width, btn_height = 140, 40
        
        # Barra de Navegação no Topo
        self.top_bar = ctk.CTkFrame(self, height=40, fg_color="#1E1E1E", corner_radius=0)
        self.top_bar.pack(fill="x", side="top")
        
        btn_font = ctk.CTkFont(size=12, weight="bold")
        
        self.btn_log = ctk.CTkButton(self.top_bar, text="📝 Logs", width=60, fg_color="transparent", hover_color="#333333", font=btn_font, command=self.open_logs_menu)
        self.btn_log.pack(side="left", padx=5, pady=5)
        
        self.btn_sobre = ctk.CTkButton(self.top_bar, text="ℹ️ Sobre", width=60, fg_color="transparent", hover_color="#333333", font=btn_font, command=self.open_sobre_menu)
        self.btn_sobre.pack(side="left", padx=5, pady=5)
        
        self.btn_sair = ctk.CTkButton(self.top_bar, text="❌ Sair", width=60, fg_color="transparent", hover_color="#802020", font=btn_font, text_color="#FF6666", command=self.quit_app)
        self.btn_sair.pack(side="right", padx=5, pady=5)

        # Container Principal com padding
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Exibe IP Local em destaque
        self.local_ip = get_local_ip()
        
        # Título
        ctk.CTkLabel(self.main_frame, text="AUDIO SYNC", 
                     font=ctk.CTkFont(family="Inter", size=24, weight="bold"),
                     text_color="#5DE0E6").pack(pady=(0, 5))
                     
        ctk.CTkLabel(self.main_frame, text=f"IP DESTE COMPUTADOR: {self.local_ip}", 
                     font=ctk.CTkFont(size=14, weight="bold"), text_color="#A0A0A0").pack(pady=(0, 20))

        # Seção do Modo de Operação
        self.mode_var = tk.StringVar(value=self.config["mode"])
        
        frame_mode = ctk.CTkFrame(self.main_frame)
        frame_mode.pack(fill="x", pady=10)
        
        ctk.CTkLabel(frame_mode, text="Modo de Operação", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(10, 0))
        
        ctk.CTkRadioButton(frame_mode, text="Servidor (PC Desktop - Recebe)", 
                           variable=self.mode_var, value="server", 
                           command=self.on_mode_change, fg_color="#004AAD").pack(anchor="w", padx=20, pady=5)
                           
        ctk.CTkRadioButton(frame_mode, text="Cliente (Notebook - Envia)", 
                           variable=self.mode_var, value="client", 
                           command=self.on_mode_change, fg_color="#004AAD").pack(anchor="w", padx=20, pady=(5, 15))
        
        # Seção de Configuração do Outro IP
        self.frame_ip = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.frame_ip.pack(fill="x", pady=10)
        
        self.ip_label = ctk.CTkLabel(self.frame_ip, text="IP do Cliente (Notebook):", font=ctk.CTkFont(weight="bold"))
        self.ip_label.pack(side="left", padx=(0, 10))
        
        self.ip_entry = ctk.CTkEntry(self.frame_ip, width=150, placeholder_text="Ex: 192.168.0.X")
        self.ip_entry.insert(0, self.config["ip"])
        self.ip_entry.pack(side="left")
        
        self.on_mode_change()
        
        # Checkboxes de automação
        self.autostart_var = tk.BooleanVar(value=self.config.get("autostart", False))
        ctk.CTkCheckBox(self.main_frame, text="Iniciar oculto com o Windows", 
                        variable=self.autostart_var, command=self.toggle_autostart,
                        fg_color="#004AAD").pack(anchor="w", pady=(15, 5))
                       
        self.autosync_var = tk.BooleanVar(value=self.config.get("autosync", False))
        ctk.CTkCheckBox(self.main_frame, text="Sincronizar automaticamente", 
                        variable=self.autosync_var, command=self.toggle_autosync,
                        fg_color="#004AAD").pack(anchor="w", pady=5)

        # Labels de Status
        self.status_var = tk.StringVar(value="Status: Parado")
        self.status_label = ctk.CTkLabel(self.main_frame, textvariable=self.status_var, font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(pady=15)

        # Botões Iniciar e Parar
        frame_btns = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_btns.pack(pady=5)
        
        # Botão Iniciar com cor sólida Azul Claro
        self.btn_start = ctk.CTkButton(frame_btns, text="INICIAR", 
                                       command=self.start_sync, 
                                       width=btn_width, height=btn_height,
                                       fg_color="#5DE0E6",
                                       hover_color="#004AAD",
                                       text_color="black", # Preto tem melhor contraste no ciano
                                       font=ctk.CTkFont(weight="bold", size=14))
        self.btn_start.pack(side="left", padx=10)
        
        # Botão Parar (Normal)
        self.btn_stop = ctk.CTkButton(frame_btns, text="PARAR", 
                                      command=self.stop_sync, 
                                      width=btn_width, height=btn_height,
                                      fg_color="#2b2b2b", hover_color="#802020",
                                      text_color="white", state="disabled",
                                      font=ctk.CTkFont(weight="bold", size=14))
        self.btn_stop.pack(side="left", padx=10)

        # Autostart / Autosync
        if self.config.get("autostart", False):
            self.autostart_var.set(True)
        if self.config.get("autosync", False):
            self.autosync_var.set(True)
            self.after(500, self.start_sync)

    def open_logs_menu(self):
        menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", 
                       activebackground="#004AAD", activeforeground="white", 
                       bd=0, font=("Segoe UI", 10))
        menu.add_command(label="Ver Logs (Console)", command=self.show_log_console)
        menu.add_command(label="Abrir Pasta de Logs", command=self.open_log_folder)
        
        # Calcula a posição abaixo do botão
        x = self.btn_log.winfo_rootx()
        y = self.btn_log.winfo_rooty() + self.btn_log.winfo_height()
        menu.post(x, y)

    def show_log_console(self):
        if hasattr(self, 'log_win') and self.log_win.winfo_exists():
            self.log_win.lift()
            return
            
        self.log_win = ctk.CTkToplevel(self)
        self.log_win.title("Console de Logs (Tempo Real)")
        self.log_win.geometry("500x350")
        
        self.log_textbox = ctk.CTkTextbox(self.log_win, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Lê o histórico de logs do arquivo
        try:
            with open('audiosync.log', 'r') as f:
                content = f.read()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", content)
                self.log_textbox.configure(state="disabled")
                self.log_textbox.yview("end")
        except: pass
        
        # Adiciona o Handler em tempo real
        handler = TextHandler(self.log_textbox)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger = logging.getLogger()
        logger.addHandler(handler)
        
        def on_close():
            logger.removeHandler(handler)
            self.log_win.destroy()
            
        self.log_win.protocol("WM_DELETE_WINDOW", on_close)

    def open_log_folder(self):
        import os
        log_path = os.path.abspath('.')
        try:
            os.startfile(log_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta: {e}")
            
    def open_sobre_menu(self):
        menu = tk.Menu(self, tearoff=0, bg="#2b2b2b", fg="white", 
                       activebackground="#004AAD", activeforeground="white", 
                       bd=0, font=("Segoe UI", 10))
        menu.add_command(label="Acessar o Site", command=lambda: webbrowser.open("https://rafaelparoni.vercel.app/audio-sync"))
        menu.add_command(label="Sobre o Software", command=self.show_sobre_info)
        
        x = self.btn_sobre.winfo_rootx()
        y = self.btn_sobre.winfo_rooty() + self.btn_sobre.winfo_height()
        menu.post(x, y)
        
    def show_sobre_info(self):
        sobre_win = ctk.CTkToplevel(self)
        sobre_win.title("Sobre o AudioSync")
        sobre_win.geometry("350x200")
        sobre_win.resizable(False, False)
        sobre_win.transient(self)
        sobre_win.grab_set()
        
        ctk.CTkLabel(sobre_win, text="AUDIO SYNC", font=ctk.CTkFont(size=20, weight="bold"), text_color="#5DE0E6").pack(pady=(30, 5))
        desc = "Software de espelhamento de áudio via rede local.\nDesenvolvido para sincronização de baixa latência."
        ctk.CTkLabel(sobre_win, text=desc, justify="center").pack(pady=10, padx=20)

    def on_mode_change(self):
        mode = self.mode_var.get()
        self.save_config()
        if mode == "server":
            self.ip_label.configure(text="Sincronizar apenas com IP:")
            self.ip_entry.configure(placeholder_text="Opcional. Ex: 192.168.0.X")
        else:
            self.ip_label.configure(text="IP do Desktop (Servidor):")
            self.ip_entry.configure(placeholder_text="Obrigatório! Ex: 192.168.0.X")

    def set_status(self, text):
        self.after(0, lambda: self.status_var.set(f"Status: {text}"))
        
        # Muda a cor baseada no status
        if "Iniciado" in text or "Recebendo" in text:
            self.after(0, lambda: self.status_label.configure(text_color="#5DE0E6"))
        elif "Parado" in text:
            self.after(0, lambda: self.status_label.configure(text_color="#A0A0A0"))
        else:
            self.after(0, lambda: self.status_label.configure(text_color="white"))

    def start_sync(self):
        if self.is_running: return
        
        mode = self.mode_var.get()
        ip = self.ip_entry.get().strip()
        
        if mode == "client" and not ip:
            messagebox.showerror("Erro", "No modo Cliente, você precisa informar o IP do Servidor.")
            return

        self.config["mode"] = mode
        self.config["ip"] = ip
        self.save_config()
        
        self.stop_event.clear()
        
        logging.info(f"Iniciando sincronização no modo {mode.upper()}. IP Alvo: {ip if ip else 'Todos'}")
        
        if mode == "server":
            self.worker_thread = threading.Thread(target=run_server, args=(ip, self.stop_event, self.set_status), daemon=True)
        else:
            self.worker_thread = threading.Thread(target=run_client, args=(ip, self.stop_event, self.set_status), daemon=True)
            
        self.worker_thread.start()
        self.is_running = True
        
        # Desabilita o botão Iniciar (fica cinza)
        self.btn_start.configure(state="disabled", fg_color="#333333", text_color="gray")
        self.btn_stop.configure(state="normal")
        self.ip_entry.configure(state="disabled")

    def stop_sync(self):
        if not self.is_running: return
        self.stop_event.set()
        logging.info("Sincronização parada pelo usuário.")
        self.set_status("Parando...")
        self.is_running = False
        
        # Habilita o botão Iniciar (volta pro Ciano)
        self.btn_start.configure(state="normal", fg_color="#5DE0E6", text_color="black")
        self.btn_stop.configure(state="disabled")
        self.ip_entry.configure(state="normal")

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem('Abrir AudioSync', self.show_window),
            pystray.MenuItem('Sair Completamente', self.quit_app)
        )
        self.tray_icon = pystray.Icon("AudioSync", create_tray_icon_image(), "AudioSync", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def hide_window(self):
        self.withdraw()
        
    def show_window(self, icon=None, item=None):
        self.after(0, self.deiconify)
        
    def quit_app(self, icon=None, item=None):
        logging.info("Encerrando o aplicativo pelo usuário...")
        self.stop_event.set()
        if self.tray_icon:
            self.tray_icon.stop()
        self.quit()

if __name__ == "__main__":
    app = AudioSyncApp()
    app.mainloop()
