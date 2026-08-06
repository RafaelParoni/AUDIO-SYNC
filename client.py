import socket
import struct
import time
import pyaudiowpatch as pyaudio

UDP_PORT = 50005
CHUNK = 256

def run_client(udp_ip, stop_event, status_callback=None):
    """
    Função principal do cliente. Captura o áudio do Notebook (Loopback WASAPI)
    e envia via UDP para o ip especificado.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    p = pyaudio.PyAudio()
    try:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        if status_callback: status_callback("Erro: O sistema não suporta WASAPI.")
        return

    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
                
    if not default_speakers["isLoopbackDevice"]:
        if status_callback: status_callback("Erro: Dispositivo de Loopback não encontrado.")
        return

    sample_rate = int(default_speakers["defaultSampleRate"])
    channels = default_speakers["maxInputChannels"]
    header = struct.pack('<IH', sample_rate, channels)

    stream = p.open(format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    frames_per_buffer=CHUNK,
                    input=True,
                    input_device_index=default_speakers["index"])

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
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()
        if status_callback:
            status_callback("Cliente Parado.")
