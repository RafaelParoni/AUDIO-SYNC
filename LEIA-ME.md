# Audio Sync (Notebook -> PC Desktop)

Este projeto cria uma ponte em tempo real (via UDP) para enviar o áudio que está sendo reproduzido no seu Notebook diretamente para os alto-falantes do PC Desktop. 

Utiliza a biblioteca `pyaudiowpatch` com o **WASAPI** do Windows, o que garante a captura nativa do áudio ("Loopback") sem a necessidade de ativar ou configurar recursos antigos como o "Stereo Mix".

## Requisitos
- Windows (10 ou 11).
- Python 3.x instalado no PC Desktop e no Notebook.

## 1. Instalação das dependências (Nas DUAS máquinas)

Abra o prompt de comando (CMD) ou PowerShell na pasta do projeto e instale a dependência necessária:

```bash
pip install -r requirements.txt
```
*(Isso instalará o `pyaudiowpatch`, que é uma versão do pyaudio com suporte especializado para Windows WASAPI Loopback).*

---

## 2. Configurando e Rodando o Servidor (PC Desktop)

O PC Desktop será o Servidor. Ele ficará aguardando o recebimento do áudio e tocará em suas caixas de som padrão.

1. **Descubra o IP local do PC Desktop:**
   - No PC Desktop, abra o CMD ou PowerShell e digite:
     ```bash
     ipconfig
     ```
   - Procure pelo endereço **IPv4** da sua conexão de rede (Wi-Fi ou Ethernet) e anote-o. Exemplo: `192.168.1.15`.

2. **Execute o servidor:**
   - No terminal, ainda na pasta do projeto, inicie o script:
     ```bash
     python server.py
     ```
   - *Nota:* Caso o Firewall do Windows pergunte, **permita** o acesso na rede. Ele precisa liberar a porta UDP 50005.

---

## 3. Configurando e Rodando o Cliente (Notebook)

O Notebook será o Cliente. Ele capturará o próprio som do sistema e vai direcionar tudo para o IP do PC.

1. **Edite o arquivo `client.py`:**
   - Abra o `client.py` em um bloco de notas ou editor de código.
   - Encontre a linha:
     ```python
     UDP_IP = "192.168.X.X"
     ```
   - Altere esse valor colocando exatamente o IP que você anotou no PC Desktop.
   - Salve o arquivo.

2. **Execute o cliente:**
   - No Notebook, abra o CMD/PowerShell na pasta do projeto e inicie o script:
     ```bash
     python client.py
     ```

Pronto! Qualquer áudio que você tocar no Notebook sairá instantaneamente no PC Desktop com latência baixíssima.

## Detalhes Técnicos e Resiliência
- Como você mencionou o uso do NAT (Tethering USB), o UDP funcionará de forma unidirecional. Como o Notebook (cliente) é quem inicia o fluxo enviando para o Desktop (servidor), e como o Desktop está em uma porta que permite escuta (`0.0.0.0`), a travessia deve funcionar adequadamente desde que o IP interno da sua rede Wi-Fi seja alcançável pelo roteamento do seu celular.
- A aplicação utiliza `CHUNK` pequeno de pacotes para manter uma sincronia razoável, perfeitamente aceitável para vídeos e uso geral.
- Pequenas perdas de conexão (pacotes dropados) serão absorvidas naturalmente sem travar o aplicativo ou atrasar o áudio futuro.
