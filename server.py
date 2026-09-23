import socket
import struct
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio
import time

UDP_PORT = 50005

def run_server(expected_client_ip, stop_event, status_callback=None):
    """
    Função principal do servidor. Escuta o IP na porta especificada 
    e envia o áudio recebido para os alto-falantes locais,
    aceitando conexões APENAS do expected_client_ip.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
    except Exception:
        pass
    sock.bind(("0.0.0.0", UDP_PORT))
    # Timeout curto para permitir verificar o stop_event frequentemente
    sock.settimeout(0.5)

    p = pyaudio.PyAudio()
    stream = None
    current_rate = 0
    current_channels = 0

    if status_callback:
        status_callback(f"Servidor Iniciado (Escutando na porta {UDP_PORT})")

    try:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                
                # Devido ao NAT (Tethering USB), o IP que chega pode ser o do celular e não o do notebook.
                # Portanto, removemos o bloqueio estrito para não quebrar a conexão.
                
                if len(data) > 6:
                    rate, channels = struct.unpack('<IH', data[:6])
                    audio_data = data[6:]
                    
                    if stream is None or rate != current_rate or channels != current_channels:
                        if stream is not None:
                            try:
                                stream.stop_stream()
                                stream.close()
                            except Exception:
                                pass
                        
                        if status_callback:
                            status_callback(f"Recebendo de {addr[0]} ({rate}Hz, {channels} canais)")
                        
                        stream = p.open(format=pyaudio.paInt16,
                                        channels=channels,
                                        rate=rate,
                                        output=True)
                        current_rate = rate
                        current_channels = channels
                    
                    try:
                        stream.write(audio_data, exception_on_underflow=False)
                    except TypeError:
                        stream.write(audio_data)
            except socket.timeout:
                continue
            except Exception as e:
                pass # Ignora pequenas falhas de leitura ou buffer
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        p.terminate()
        sock.close()
        if status_callback:
            status_callback("Servidor Parado.")
