"""
Especificação Técnica: Módulo de Integração WhatsApp (WAHA)

Este documento detalha as especificações técnicas para o desenvolvimento do módulo de integração
com WhatsApp usando WAHA (WhatsApp Web API) no projeto ZF Portal Intelligence Agent.
"""

# Especificação Técnica: Módulo de Integração WhatsApp (WAHA)

## 1. Visão Geral

O módulo de integração com WhatsApp será responsável por estabelecer comunicação bidirecional com contatos via WhatsApp, utilizando a biblioteca WAHA (WhatsApp Web API). Esta especificação define os componentes, interfaces e fluxos de dados necessários para implementação deste módulo.

## 2. Componentes do Módulo

### 2.1 Arquitetura

A integração com WhatsApp será implementada através de uma arquitetura cliente-servidor, onde:

- **Servidor WAHA**: Aplicação Node.js que gerencia a sessão do WhatsApp Web
- **Cliente Python**: Biblioteca em Python que se comunica com o servidor WAHA via API REST
- **Sistema de Webhooks**: Mecanismo para receber notificações em tempo real do servidor WAHA

```
+-------------------+        +------------------+        +------------------+
|                   |        |                  |        |                  |
| ZF Portal Agent   |<------>| Cliente Python   |<------>| Servidor WAHA    |<-----> WhatsApp
| (Aplicação Python)|        | (API Wrapper)    |        | (Node.js)        |        Web
|                   |        |                  |        |                  |
+-------------------+        +------------------+        +------------------+
        ^                                                        |
        |                                                        |
        +--------------------------------------------------------+
                              Webhooks
```

### 2.2 Componentes Principais

#### 2.2.1 Módulo `whatsapp_connector.py`

```python
"""
Módulo responsável pela comunicação com o servidor WAHA.
Implementa cliente HTTP para realizar operações na API do WAHA.
"""

class WhatsAppConnector:
    """
    Classe para conexão com a API WAHA.
    Gerencia a comunicação entre a aplicação Python e o servidor WAHA.
    """
    
    def __init__(self, api_url, webhook_url=None, session_id=None):
        """
        Inicializa o conector com a URL da API WAHA.
        
        Args:
            api_url (str): URL do servidor WAHA
            webhook_url (str, opcional): URL para receber webhooks
            session_id (str, opcional): ID de sessão existente
        """
        pass
    
    async def initialize_session(self):
        """
        Inicializa uma nova sessão no WhatsApp Web ou reconecta a uma sessão existente.
        
        Returns:
            dict: Informações da sessão inicializada
        """
        pass
    
    async def get_qr_code(self):
        """
        Obtém o QR code para autenticação no WhatsApp Web.
        
        Returns:
            str: URL da imagem do QR code ou string base64
        """
        pass
    
    async def check_session_status(self):
        """
        Verifica o status da sessão atual.
        
        Returns:
            str: Status da sessão (CONNECTED, DISCONNECTED, etc.)
        """
        pass
    
    async def send_message(self, to, message, options=None):
        """
        Envia uma mensagem de texto para um contato.
        
        Args:
            to (str): Número do destinatário no formato internacional (ex: "5511999999999")
            message (str): Conteúdo da mensagem
            options (dict, opcional): Opções adicionais para a mensagem
            
        Returns:
            dict: Resposta da API com detalhes da mensagem enviada
        """
        pass
    
    async def send_image(self, to, image_path=None, image_url=None, caption=None):
        """
        Envia uma imagem para um contato.
        
        Args:
            to (str): Número do destinatário
            image_path (str, opcional): Caminho local para a imagem
            image_url (str, opcional): URL da imagem
            caption (str, opcional): Legenda da imagem
            
        Returns:
            dict: Resposta da API com detalhes da mensagem enviada
        """
        pass
    
    async def send_document(self, to, document_path=None, document_url=None, filename=None):
        """
        Envia um documento para um contato.
        
        Args:
            to (str): Número do destinatário
            document_path (str, opcional): Caminho local para o documento
            document_url (str, opcional): URL do documento
            filename (str, opcional): Nome do arquivo
            
        Returns:
            dict: Resposta da API com detalhes da mensagem enviada
        """
        pass
    
    async def send_template_message(self, to, template_data):
        """
        Envia uma mensagem baseada em template com botões ou listas.
        
        Args:
            to (str): Número do destinatário
            template_data (dict): Dados do template (botões, listas, etc.)
            
        Returns:
            dict: Resposta da API com detalhes da mensagem enviada
        """
        pass
    
    async def get_contacts(self):
        """
        Obtém a lista de contatos disponíveis.
        
        Returns:
            list: Lista de contatos
        """
        pass
    
    async def check_number_exists(self, phone_number):
        """
        Verifica se um número existe no WhatsApp.
        
        Args:
            phone_number (str): Número a verificar
            
        Returns:
            bool: True se o número existir no WhatsApp
        """
        pass
```

#### 2.2.2 Módulo `whatsapp_session_manager.py`

```python
"""
Módulo para gerenciamento de sessões do WhatsApp.
Responsável por iniciar, monitorar e restaurar sessões.
"""

class WhatsAppSessionManager:
    """
    Classe para gerenciar sessões do WhatsApp.
    Lida com autenticação, reconexão e manutenção de múltiplas sessões.
    """
    
    def __init__(self, sessions_dir, connector):
        """
        Inicializa o gerenciador de sessões.
        
        Args:
            sessions_dir (str): Diretório para armazenar dados de sessão
            connector (WhatsAppConnector): Instância do conector WhatsApp
        """
        pass
    
    async def create_session(self, session_name):
        """
        Cria uma nova sessão do WhatsApp.
        
        Args:
            session_name (str): Nome para a sessão
            
        Returns:
            str: ID da sessão criada
        """
        pass
    
    async def restore_session(self, session_id):
        """
        Restaura uma sessão existente.
        
        Args:
            session_id (str): ID da sessão a restaurar
            
        Returns:
            bool: True se a sessão foi restaurada com sucesso
        """
        pass
    
    async def get_session_info(self, session_id):
        """
        Obtém informações de uma sessão específica.
        
        Args:
            session_id (str): ID da sessão
            
        Returns:
            dict: Informações da sessão
        """
        pass
    
    async def monitor_sessions(self):
        """
        Monitora o estado de todas as sessões ativas e tenta reconectar quando necessário.
        
        Returns:
            dict: Estado de todas as sessões monitoradas
        """
        pass
    
    async def logout_session(self, session_id):
        """
        Encerra uma sessão específica.
        
        Args:
            session_id (str): ID da sessão a encerrar
            
        Returns:
            bool: True se a sessão foi encerrada com sucesso
        """
        pass
```

#### 2.2.3 Módulo `whatsapp_message_handler.py`

```python
"""
Módulo para processamento de mensagens do WhatsApp.
Gerencia o envio de diferentes tipos de conteúdo e o processamento de mensagens recebidas.
"""

class WhatsAppMessageHandler:
    """
    Classe para manipulação de mensagens do WhatsApp.
    Gerencia o fluxo de envio e recebimento de mensagens.
    """
    
    def __init__(self, connector, db_session=None):
        """
        Inicializa o manipulador de mensagens.
        
        Args:
            connector (WhatsAppConnector): Instância do conector WhatsApp
            db_session (Session, opcional): Sessão do banco de dados para registro
        """
        pass
    
    async def process_incoming_message(self, message_data):
        """
        Processa uma mensagem recebida via webhook.
        
        Args:
            message_data (dict): Dados da mensagem recebida
            
        Returns:
            dict: Resultado do processamento
        """
        pass
    
    async def send_text_message(self, to, text, metadata=None):
        """
        Envia uma mensagem de texto simples.
        
        Args:
            to (str): Número do destinatário
            text (str): Texto da mensagem
            metadata (dict, opcional): Metadados adicionais para rastreamento
            
        Returns:
            dict: Resultado do envio
        """
        pass
    
    async def send_rich_message(self, to, content_type, content, metadata=None):
        """
        Envia uma mensagem rica (imagem, documento, vídeo, áudio).
        
        Args:
            to (str): Número do destinatário
            content_type (str): Tipo de conteúdo ("image", "document", "video", "audio")
            content (str): Caminho ou URL do conteúdo
            metadata (dict, opcional): Metadados adicionais para rastreamento
            
        Returns:
            dict: Resultado do envio
        """
        pass
    
    async def send_interactive_message(self, to, interactive_type, content, metadata=None):
        """
        Envia uma mensagem interativa (botões, listas).
        
        Args:
            to (str): Número do destinatário
            interactive_type (str): Tipo de interação ("button", "list")
            content (dict): Estrutura de conteúdo interativo
            metadata (dict, opcional): Metadados adicionais para rastreamento
            
        Returns:
            dict: Resultado do envio
        """
        pass
    
    async def register_message_in_db(self, message_data, message_type, status="sent"):
        """
        Registra uma mensagem no banco de dados.
        
        Args:
            message_data (dict): Dados da mensagem
            message_type (str): Tipo da mensagem
            status (str): Status inicial da mensagem
            
        Returns:
            int: ID da mensagem registrada
        """
        pass
```

#### 2.2.4 Módulo `whatsapp_webhook_handler.py`

```python
"""
Módulo para gerenciamento de webhooks do WhatsApp.
Processa notificações em tempo real do servidor WAHA.
"""

class WhatsAppWebhookHandler:
    """
    Classe para lidar com webhooks recebidos do servidor WAHA.
    Processa eventos como mensagens recebidas, mudanças de status, etc.
    """
    
    def __init__(self, message_handler, db_session=None):
        """
        Inicializa o manipulador de webhooks.
        
        Args:
            message_handler (WhatsAppMessageHandler): Instância do manipulador de mensagens
            db_session (Session, opcional): Sessão do banco de dados
        """
        pass
    
    async def handle_webhook(self, webhook_data):
        """
        Processa dados recebidos via webhook.
        
        Args:
            webhook_data (dict): Dados recebidos no webhook
            
        Returns:
            dict: Resultado do processamento
        """
        pass
    
    async def process_message_received(self, message_data):
        """
        Processa uma mensagem recebida.
        
        Args:
            message_data (dict): Dados da mensagem
            
        Returns:
            dict: Resultado do processamento
        """
        pass
    
    async def process_message_status_update(self, status_data):
        """
        Processa uma atualização de status de mensagem (entregue, lida).
        
        Args:
            status_data (dict): Dados de status
            
        Returns:
            dict: Resultado do processamento
        """
        pass
    
    async def process_connection_update(self, connection_data):
        """
        Processa uma atualização de status de conexão.
        
        Args:
            connection_data (dict): Dados de conexão
            
        Returns:
            dict: Resultado do processamento
        """
        pass
```

## 3. Interfaces de API

### 3.1 API do Servidor WAHA

O servidor WAHA expõe uma API REST com os seguintes endpoints principais:

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /api/sessions | Lista todas as sessões |
| POST | /api/sessions | Cria uma nova sessão |
| GET | /api/sessions/{id} | Obtém detalhes de uma sessão |
| DELETE | /api/sessions/{id} | Encerra uma sessão |
| GET | /api/sessions/{id}/qr | Obtém QR code para autenticação |
| POST | /api/sessions/{id}/send/message | Envia mensagem de texto |
| POST | /api/sessions/{id}/send/image | Envia imagem |
| POST | /api/sessions/{id}/send/document | Envia documento |
| POST | /api/sessions/{id}/send/buttons | Envia mensagem com botões |
| POST | /api/sessions/{id}/send/list | Envia mensagem com lista |
| GET | /api/sessions/{id}/contacts | Lista contatos |
| GET | /api/sessions/{id}/chats | Lista conversas |

### 3.2 Webhook Events

O servidor WAHA envia eventos via webhook para os seguintes eventos:

| Evento | Descrição |
|--------|-----------|
| `message.received` | Nova mensagem recebida |
| `message.sent` | Mensagem enviada com sucesso |
| `message.delivered` | Mensagem entregue ao destinatário |
| `message.read` | Mensagem lida pelo destinatário |
| `session.connected` | Sessão WhatsApp conectada |
| `session.disconnected` | Sessão WhatsApp desconectada |
| `qr.updated` | QR code atualizado |

## 4. Modelo de Dados

### 4.1 Adições ao Modelo Existente

Para suportar a funcionalidade de WhatsApp, as seguintes modificações serão feitas ao modelo de dados:

#### 4.1.1 Tabela `contato` (existente)

Novas colunas:
- `whatsapp_number` (VARCHAR): Número de WhatsApp do contato
- `whatsapp_status` (VARCHAR): Status do contato no WhatsApp (verified, unverified, invalid)
- `last_whatsapp_interaction` (DATETIME): Data/hora da última interação via WhatsApp

#### 4.1.2 Nova Tabela `whatsapp_session`

```sql
CREATE TABLE whatsapp_session (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    qr_code TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    phone_number VARCHAR(20),
    phone_connected BOOLEAN DEFAULT FALSE,
    last_connection TIMESTAMP
);
```

#### 4.1.3 Nova Tabela `whatsapp_message`

```sql
CREATE TABLE whatsapp_message (
    id SERIAL PRIMARY KEY,
    contato_id INTEGER REFERENCES contato(id),
    session_id INTEGER REFERENCES whatsapp_session(id),
    message_id VARCHAR(100) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- 'incoming' ou 'outgoing'
    message_type VARCHAR(20) NOT NULL, -- 'text', 'image', 'document', 'interactive', etc.
    content TEXT,
    media_url TEXT,
    status VARCHAR(20) NOT NULL, -- 'sent', 'delivered', 'read', 'failed'
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB
);
```

## 5. Fluxos de Implementação

### 5.1 Fluxo de Inicialização de Sessão

```
+----------------+         +-------------------+         +------------------+
| ZF Portal      |         |  WhatsApp         |         | WAHA Server      |
| Agent          |         |  Connector        |         |                  |
+-------+--------+         +---------+---------+         +--------+---------+
        |                            |                            |
        | initialize_session()       |                            |
        +--------------------------->|                            |
        |                            | POST /api/sessions         |
        |                            +--------------------------->|
        |                            |                            |
        |                            |        SessionID           |
        |                            |<---------------------------+
        |                            |                            |
        |                            | GET /api/sessions/{id}/qr  |
        |                            +--------------------------->|
        |                            |                            |
        |                            |         QR Code            |
        |                            |<---------------------------+
        |      QR Code + SessionID   |                            |
        |<---------------------------+                            |
        |                            |                            |
        |   [Usuário escaneia QR]    |                            |
        |                            |                            |
        |                            |    [Webhook: connected]    |
        |<------------------------------------------------------------+
        |                            |                            |
        | check_session_status()     |                            |
        +--------------------------->|                            |
        |                            | GET /api/sessions/{id}     |
        |                            +--------------------------->|
        |                            |                            |
        |                            |    {"status": "CONNECTED"} |
        |                            |<---------------------------+
        |   {"status": "CONNECTED"}  |                            |
        |<---------------------------+                            |
        |                            |                            |
```

### 5.2 Fluxo de Envio de Mensagem

```
+--------------+         +-------------------+         +---------------+         +-----------+
| ZF Portal    |         |  WhatsApp         |         | WAHA Server   |         | Contato   |
| Agent        |         |  MessageHandler   |         |               |         | WhatsApp  |
+------+-------+         +---------+---------+         +-------+-------+         +-----+-----+
       |                           |                           |                       |
       | send_message(to, text)    |                           |                       |
       +-------------------------->|                           |                       |
       |                           | register_message_in_db()  |                       |
       |                           +---+                       |                       |
       |                           |   |                       |                       |
       |                           |<--+                       |                       |
       |                           |                           |                       |
       |                           | POST /api/sessions/{id}/send/message              |
       |                           +----------------------------------------->|        |
       |                           |                           |              |        |
       |                           |                           |     Mensagem |        |
       |                           |                           |              +------->|
       |                           |                           |                       |
       |                           |      {"status": "sent", "messageId": "..."}      |
       |                           |<-----------------------------------------+       |
       |                           |                           |                       |
       |                           | update_message_status()   |                       |
       |                           +---+                       |                       |
       |                           |   |                       |                       |
       |                           |<--+                       |                       |
       |                           |                           |                       |
       |    {"success": true}      |                           |                       |
       |<--------------------------+                           |                       |
       |                           |                           |                       |
       |                           |         [Webhook: message.delivered]              |
       |<-----------------------------------------------------------------------+     |
       |                           |                           |                       |
       |                           | update_message_status("delivered")                |
       |                           +---+                       |                       |
       |                           |   |                       |                       |
       |                           |<--+                       |                       |
       |                           |                           |                       |
       |                           |         [Webhook: message.read]                   |
       |<-----------------------------------------------------------------------+     |
       |                           |                           |                       |
       |                           | update_message_status("read")                     |
       |                           +---+                       |                       |
       |                           |   |                       |                       |
       |                           |<--+                       |                       |
       |                           |                           |                       |
```

### 5.3 Fluxo de Recebimento de Mensagem

```
+-----------+         +---------------+         +-------------------+         +--------------+
| Contato   |         | WAHA Server   |         |  WhatsApp         |         | ZF Portal    |
| WhatsApp  |         |               |         |  WebhookHandler   |         | Agent        |
+-----+-----+         +-------+-------+         +---------+---------+         +------+-------+
      |                       |                           |                          |
      |                       |                           |                          |
      |      Mensagem         |                           |                          |
      +--------------------->+|                           |                          |
      |                       |                           |                          |
      |                       |   [Webhook: message.received]                        |
      |                       +-------------------------->|                          |
      |                       |                           |                          |
      |                       |                           | process_message_received()|
      |                       |                           +------------+             |
      |                       |                           |            |             |
      |                       |                           |<-----------+             |
      |                       |                           |                          |
      |                       |                           | register_message_in_db() |
      |                       |                           +------------+             |
      |                       |                           |            |             |
      |                       |                           |<-----------+             |
      |                       |                           |                          |
      |                       |                           | handle_incoming_message()|
      |                       |                           +------------------------->|
      |                       |                           |                          |
      |                       |                           |                          |
      |                       |                           |     process_message()    |
      |                       |                           |                     +----+
      |                       |                           |                     |    |
      |                       |                           |                     |<---+
      |                       |                           |                          |
      |                       |                           |      send_response()     |
      |                       |                           |<-------------------------+
      |                       |                           |                          |
      |                       |                           | send_text_message()      |
      |                       |                           +------------+             |
      |                       |                           |            |             |
      |                       |                           |<-----------+             |
      |                       |                           |                          |
      |                       | POST /api/sessions/{id}/send/message                 |
      |                       |<--------------------------+                          |
      |                       |                           |                          |
      |    Resposta           |                           |                          |
      |<---------------------+|                           |                          |
      |                       |                           |                          |
```

## 6. Configuração do Servidor WAHA

### 6.1 Requisitos do Sistema

- Node.js 14+ instalado
- Navegador Chromium acessível (para WhatsApp Web)
- Portas: 3000 (API) e 8080 (interface web) disponíveis

### 6.2 Processo de Instalação

```bash
# Clonar o repositório WAHA
git clone https://github.com/waha-api/waha.git
cd waha

# Instalar dependências
npm install

# Configurar variáveis de ambiente
cat > .env << EOL
PORT=3000
WEBHOOK_URL=http://localhost:8000/webhook/whatsapp
WEBHOOK_ALLOWED_EVENTS=message.received,message.sent,message.delivered,message.read,session.connected,session.disconnected
EOL

# Iniciar o servidor
npm start
```

### 6.3 Docker (Alternativa)

```yaml
# docker-compose.yml
version: '3'
services:
  waha:
    image: wahaapi/waha:latest
    ports:
      - "3000:3000"
      - "8080:8080"
    volumes:
      - ./waha_data:/app/data
    environment:
      - PORT=3000
      - WEBHOOK_URL=http://host.docker.internal:8000/webhook/whatsapp
      - WEBHOOK_ALLOWED_EVENTS=message.received,message.sent,message.delivered,message.read,session.connected,session.disconnected
    restart: unless-stopped
```

## 7. Considerações de Segurança

1. **Autenticação da API**:
   - Implementar autenticação JWT para acesso à API WAHA
   - Utilizar HTTPS para todas as comunicações

2. **Proteção de Dados**:
   - Criptografar dados sensíveis no banco de dados
   - Implementar políticas de retenção de mensagens

3. **Limitação de Taxa**:
   - Implementar limitadores de taxa para evitar bloqueio pelo WhatsApp
   - Monitorar padrões de uso para detectar comportamentos suspeitos

4. **Validação de Entrada**:
   - Sanitizar todos os dados de entrada
   - Implementar validação rigorosa de números de telefone

## 8. Testes

### 8.1 Testes Unitários

Desenvolver testes unitários para:
- Validação de formatos de número
- Geração de mensagens
- Processamento de webhooks

### 8.2 Testes de Integração

Implementar testes de integração para:
- Comunicação com servidor WAHA
- Fluxo completo de envio/recebimento
- Manipulação de falhas de rede

### 8.3 Testes de Carga

Conduzir testes de carga para:
- Determinar capacidade máxima de mensagens por minuto
- Identificar gargalos de desempenho
- Validar comportamento sob estresse

## 9. Monitoramento e Logs

- Implementar logging detalhado de todas as operações
- Configurar alertas para falhas de conexão
- Monitorar taxas de entrega e leitura
- Rastrear tempo de resposta da API

## 10. Próximos Passos

1. Configuração do ambiente de desenvolvimento para WAHA
2. Implementação do conector básico para testes
3. Desenvolvimento do gerenciador de sessões
4. Implementação do handler de mensagens
5. Integração de webhooks com o sistema existente
