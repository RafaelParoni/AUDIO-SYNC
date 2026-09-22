import os
import sys
import socket
import struct
import time
import subprocess

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio

UDP_PORT = 50005
CHUNK = 256

def _get_linux_monitor_name():
    """Tenta descobrir o nome do monitor do dispositivo padrão de saída no Linux."""
    try:
        res = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip() + ".monitor"
    except Exception:
        pass
    try:
        res = subprocess.run(["pactl", "info"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if "Default Sink:" in line:
                    sink = line.split("Default Sink:", 1)[1].strip()
                    if sink:
                        return sink + ".monitor"
    except Exception:
        pass
    return None

def _get_capture_device(p, status_callback=None):
    """
    Retorna o dispositivo de captura (loopback) adequado para a plataforma atual.
    No Windows: utiliza WASAPI loopback.
    No Linux: utiliza o monitor do PulseAudio / PipeWire.
    """
    if sys.platform == "win32":
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except (OSError, AttributeError):
            if status_callback: status_callback("Erro: O sistema não suporta WASAPI.")
            return None

        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers.get("isLoopbackDevice", False):
            if hasattr(p, "get_loopback_device_info_generator"):
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break

        if not default_speakers.get("isLoopbackDevice", False):
            if status_callback: status_callback("Erro: Dispositivo de Loopback não encontrado no Windows.")
            return None

        sample_rate = int(default_speakers["defaultSampleRate"])
        channels = default_speakers["maxInputChannels"]
        return default_speakers, sample_rate, channels

    else:
        # Plataforma Linux / Unix
        monitor_name = _get_linux_monitor_name()
        if monitor_name:
            os.environ["PULSE_SOURCE"] = monitor_name

        device_count = p.get_device_count()
        selected_device = None
        fallback_monitor = None
        pulse_default = None

        for i in range(device_count):
            try:
                dev = p.get_device_info_by_index(i)
                if dev.get("maxInputChannels", 0) <= 0:
                    continue
                name = dev.get("name", "")
                
                # Se for exatamente o monitor do sink padrão
                if monitor_name and monitor_name in name:
                    selected_device = dev
                    break
                # Se o nome contiver 'monitor'
                if "monitor" in name.lower() and fallback_monitor is None:
                    fallback_monitor = dev
                # Guarda 'pulse' ou 'default' como opção
                if name.lower() in ("pulse", "default") and pulse_default is None:
                    pulse_default = dev
            except Exception:
                continue

        chosen = selected_device or fallback_monitor or pulse_default
        if not chosen:
            try:
                chosen = p.get_default_input_device_info()
            except Exception:
                pass

        if not chosen:
            if status_callback: status_callback("Erro: Nenhum dispositivo de áudio/monitor encontrado no Linux.")
            return None

        sample_rate = int(chosen.get("defaultSampleRate", 44100))
        channels = chosen.get("maxInputChannels", 2)
        if channels > 2:
            channels = 2
        elif channels <= 0:
            channels = 2

        return chosen, sample_rate, channels

def run_client(udp_ip, stop_event, status_callback=None):
    """
    Função principal do cliente. Captura o áudio do computador (Loopback/Monitor)
    e envia via UDP para o IP especificado.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    p = pyaudio.PyAudio()

    device_info = _get_capture_device(p, status_callback)
    if not device_info:
        p.terminate()
        sock.close()
        return

    target_device, sample_rate, channels = device_info
    header = struct.pack('<IH', sample_rate, channels)

    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        frames_per_buffer=CHUNK,
                        input=True,
                        input_device_index=target_device["index"])
    except Exception as e:
        if status_callback:
            status_callback(f"Erro ao abrir stream de áudio: {e}")
        p.terminate()
        sock.close()
        return

    if status_callback:
        status_callback(f"Transmitindo para {udp_ip} ({sample_rate}Hz, {channels} canais)")

    try:
        while not stop_event.is_set():
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                sock.sendto(header + data, (udp_ip, UDP_PORT))
            except Exception as e:
                time.sleep(0.01)
    finally:
        try:
            stream.stop_stream()
            stream.close()
        except Exception:
            pass
        p.terminate()
        sock.close()
        if status_callback:
            status_callback("Cliente Parado.")
