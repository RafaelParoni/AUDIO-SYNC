import os
import sys
import socket
import struct
import time
import subprocess
import logging

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio

UDP_PORT = 50005
CHUNK = 256  # 256 amostras = 5.3ms a 48kHz (1024 bytes PCM estéreo)

# ------------------------------------------------------------------------------
# Módulo de Captura no Linux (PulseAudio / PipeWire)
# ------------------------------------------------------------------------------

def _get_linux_monitor_source():
    """
    Descobre o nome do monitor do dispositivo padrão de saída (speakers) no Linux.
    O monitor captura exclusivamente o áudio reproduzido pelo sistema (YouTube, jogos, músicas)
    e NUNCA o microfone físico.
    """
    # 1. Tentar 'pactl get-default-sink'
    try:
        res = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip() + ".monitor"
    except Exception:
        pass

    # 2. Tentar 'pactl info' (para versões mais antigas do PulseAudio)
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

    # 3. Tentar listar sources ativas que terminem em .monitor
    try:
        res = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 2 and ".monitor" in parts[1]:
                    return parts[1]
    except Exception:
        pass

    # Fallback padrão aceito por PulseAudio e PipeWire
    return "@DEFAULT_SINK@.monitor"

def _run_client_linux(udp_ip, stop_event, status_callback=None):
    """
    Captura de áudio nativa no Linux utilizando 'parec' direcionado ao Monitor do Sink.
    Garante que o som do sistema (YouTube, músicas etc.) seja capturado sem captar o microfone.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
    except Exception:
        pass

    monitor_source = _get_linux_monitor_source()
    sample_rate = 48000
    channels = 2
    header = struct.pack('<IH', sample_rate, channels)
    
    # 256 amostras * 2 canais * 2 bytes por amostra (16-bit) = 1024 bytes
    chunk_bytes = CHUNK * channels * 2

    # Comando parec para capturar o áudio cru do monitor
    cmd = [
        "parec",
        "--format=s16le",
        f"--rate={sample_rate}",
        f"--channels={channels}",
        "-d", monitor_source,
        "--latency-msec=10"
    ]

    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=chunk_bytes * 4
        )
    except Exception as e:
        logging.error(f"Erro ao iniciar parec no Linux: {e}")
        proc = None

    if proc and proc.poll() is None:
        if status_callback:
            status_callback(f"Transmitindo som do sistema ({sample_rate}Hz) para {udp_ip}")

        try:
            while not stop_event.is_set():
                data = proc.stdout.read(chunk_bytes)
                if not data:
                    time.sleep(0.005)
                    continue
                sock.sendto(header + data, (udp_ip, UDP_PORT))
        finally:
            try:
                proc.terminate()
                proc.wait(timeout=1)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            sock.close()
            if status_callback:
                status_callback("Cliente Parado.")
        return

    # Fallback via PyAudio (se parec não estiver disponível)
    if status_callback:
        status_callback("Aviso: parec não disponível, tentando via PyAudio...")

    # Define o monitor antes de instanciar o PyAudio para o driver PulseAudio reconhecer
    os.environ["PULSE_SOURCE"] = monitor_source
    p = pyaudio.PyAudio()

    chosen_index = None
    device_count = p.get_device_count()
    for i in range(device_count):
        try:
            dev = p.get_device_info_by_index(i)
            if dev.get("maxInputChannels", 0) > 0 and "monitor" in dev.get("name", "").lower():
                chosen_index = i
                break
        except Exception:
            pass

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            frames_per_buffer=CHUNK,
            input=True,
            input_device_index=chosen_index
        )
    except Exception as e:
        if status_callback:
            status_callback(f"Erro ao abrir áudio no Linux: {e}")
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
            except Exception:
                time.sleep(0.005)
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

# ------------------------------------------------------------------------------
# Módulo de Captura no Windows (WASAPI Loopback)
# ------------------------------------------------------------------------------

def _run_client_windows(udp_ip, stop_event, status_callback=None):
    """
    Captura de áudio nativa no Windows utilizando WASAPI Loopback (pyaudiowpatch).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 262144)
    except Exception:
        pass

    p = pyaudio.PyAudio()
    default_speakers = None

    # 1. Tentar helper oficial do pyaudiowpatch
    if hasattr(p, "get_default_wasapi_loopback"):
        try:
            default_speakers = p.get_default_wasapi_loopback()
        except Exception:
            default_speakers = None

    # 2. Fallback de busca manual de loopback
    if not default_speakers:
        try:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_device = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            if hasattr(p, "get_loopback_device_info_generator"):
                for loopback in p.get_loopback_device_info_generator():
                    if default_device["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
        except Exception:
            pass

    if not default_speakers:
        if status_callback:
            status_callback("Erro: Dispositivo de Loopback (WASAPI) não encontrado no Windows.")
        p.terminate()
        sock.close()
        return

    sample_rate = int(default_speakers["defaultSampleRate"])
    channels = default_speakers["maxInputChannels"]
    header = struct.pack('<IH', sample_rate, channels)

    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=channels,
            rate=sample_rate,
            frames_per_buffer=CHUNK,
            input=True,
            input_device_index=default_speakers["index"]
        )
    except Exception as e:
        if status_callback:
            status_callback(f"Erro ao abrir stream WASAPI: {e}")
        p.terminate()
        sock.close()
        return

    if status_callback:
        status_callback(f"Transmitindo som para {udp_ip} ({sample_rate}Hz, {channels} canais)")

    try:
        while not stop_event.is_set():
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                sock.sendto(header + data, (udp_ip, UDP_PORT))
            except Exception:
                time.sleep(0.005)
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

# ------------------------------------------------------------------------------
# Ponto de Entrada Principal
# ------------------------------------------------------------------------------

def run_client(udp_ip, stop_event, status_callback=None):
    """
    Função principal do cliente. Dispara a captura de áudio apropriada
    de acordo com a plataforma (Windows ou Linux).
    """
    if sys.platform == "win32":
        _run_client_windows(udp_ip, stop_event, status_callback)
    else:
        _run_client_linux(udp_ip, stop_event, status_callback)

