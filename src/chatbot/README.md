# Chatbot WhatsApp para ZF Portal Intelligence Agent

Este módulo implementa um chatbot para WhatsApp usando a integração WAHA (WhatsApp HTTP API). O chatbot permite comunicação bidirecional com clientes e leads via WhatsApp, com suporte para respostas automáticas e interação com botões.

## Requisitos

- Python 3.9+
- Docker (para executar o servidor WAHA)
- Biblioteca Python: requests, dotenv, etc. (ver requirements.txt)

## Instalação e Configuração

### 1. Configurar o ambiente

Execute o script `setup_chatbot.py` para configurar o ambiente necessário:

```bash
python setup_chatbot.py
```

Este script:
- Verifica se o Docker está em execução
- Configura e inicia o servidor WAHA (caso ainda não exista)
- Cria arquivos de configuração necessários

### 2. Obter QR Code para autenticação

Para obter o QR code e autenticar com o WhatsApp:

```bash
python run_chatbot.py --show-qr
```

Escaneie o QR code exibido usando o WhatsApp no seu smartphone para autenticar a sessão.

### 3. Iniciar o chatbot

Para iniciar o chatbot normalmente:

```bash
python run_chatbot.py
```

O chatbot ficará em execução, processando mensagens recebidas e enviando respostas automáticas.

## Estrutura do módulo

- `chatbot_service.py`: Serviço principal que gerencia a comunicação com o WhatsApp
- `chatbot_handler.py`: Manipulador das mensagens, implementando a lógica do chatbot
- `chatbot_adapter.py`: Adaptador para integração com o sistema principal
- `responses.json`: Arquivo com respostas pré-definidas para o chatbot

## Personalização

### Respostas personalizadas

Você pode editar o arquivo `responses.json` para personalizar as respostas do chatbot para diferentes intenções.

### Comportamentos avançados

Para implementar comportamentos mais avançados, você pode modificar a classe `ChatbotHandler` em `chatbot_handler.py`.

## Integração com LLM (Futuro)

O chatbot está preparado para integração com modelos de linguagem (LLM) para respostas mais inteligentes e contextuais. Esta funcionalidade será implementada em versões futuras.

## Monitoramento e Logs

Os logs do chatbot são gravados no console e podem ser redirecionados para arquivos de log. O formato de log inclui timestamp, nível de log e mensagem.

## Resolução de Problemas

### QR Code não aparece
- Verifique se o servidor WAHA está em execução: `docker ps`
- Reinicie o container: `docker restart zf-portal-waha`

### Mensagens não são recebidas/enviadas
- Verifique o status da sessão: `python run_chatbot.py --check-status`
- Verifique os logs do container WAHA: `docker logs zf-portal-waha`

### Docker não está funcionando
- Inicie o Docker Desktop
- Verifique se o serviço Docker está em execução
