"""
Módulo para processamento de webhooks WhatsApp

Este módulo implementa o processamento de eventos recebidos
via webhook do servidor WAHA, incluindo recebimento de mensagens,
confirmações de entrega e outros eventos.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from fastapi.responses import JSONResponse

from .whatsapp_message_handler import WhatsAppMessageHandler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp_webhook_handler")


class WhatsAppWebhookHandler:
    """
    Classe para processamento de webhooks recebidos do servidor WAHA
    """
    
    def __init__(
        self, 
        message_handler: WhatsAppMessageHandler,
        api_key: str = None
    ):
        """
        Inicializa o handler de webhooks
        
        Args:
            message_handler: Instância do handler de mensagens
            api_key: Chave API para validação dos webhooks (opcional)
        """
        self.message_handler = message_handler
        self.api_key = api_key
        self.event_handlers: Dict[str, List[Callable]] = {
            "message": [],
            "message-ack": [],
            "qr": [],
            "connection": [],
            "any": []
        }
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Adiciona um handler para um tipo específico de evento
        
        Args:
            event_type: Tipo de evento (message, message-ack, etc.) ou "any"
            handler: Função de callback que processa o evento
                     Deve aceitar um parâmetro dict com os dados do evento
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Handler adicionado para evento: {event_type}")
    
    def validate_webhook_request(self, api_key_header: str = None) -> bool:
        """
        Valida uma requisição de webhook
        
        Args:
            api_key_header: Valor do header x-api-key
        
        Returns:
            bool: True se a requisição é válida
        """
        # Se não há chave configurada, qualquer requisição é válida
        if not self.api_key:
            return True
        
        # Valida a chave API
        return api_key_header == self.api_key
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um payload de webhook
        
        Args:
            payload: Dados do webhook
        
        Returns:
            Dict: Resposta para o webhook
        """
        try:
            # Extrai informações do webhook
            event = payload.get("event", "unknown")
            session = payload.get("session", "default")
            data = payload.get("data", {})
            
            logger.info(f"Webhook recebido - Evento: {event}, Sessão: {session}")
            
            # Processa com base no tipo de evento
            if event == "message":
                # Mensagem recebida
                self._process_message_event(data)
            elif event == "message-ack":
                # Confirmação de mensagem
                self._process_ack_event(data)
            elif event == "qr":
                # Código QR gerado
                self._process_qr_event(data)
            elif event == "connection":
                # Atualização de estado da conexão
                self._process_connection_event(data)
            
            # Chama os handlers específicos para o tipo de evento
            self._call_event_handlers(event, data)
            
            # Chama os handlers genéricos
            self._call_event_handlers("any", {
                "event": event,
                "session": session,
                "data": data
            })
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return {"success": False, "error": str(e)}
    
    def _process_message_event(self, data: Dict[str, Any]) -> None:
        """
        Processa evento de mensagem recebida
        
        Args:
            data: Dados da mensagem
        """
        # Extrai os dados relevantes
        message = data.get("message", {})
        
        # Passa a mensagem para o handler
        self.message_handler.process_incoming_message(message)
    
    def _process_ack_event(self, data: Dict[str, Any]) -> None:
        """
        Processa evento de confirmação de mensagem
        
        Args:
            data: Dados da confirmação
        """
        ack = data.get("ack", {})
        message_id = ack.get("id", "unknown")
        status = ack.get("status", "unknown")
        
        logger.info(f"Confirmação recebida - Mensagem: {message_id}, Status: {status}")
        
        # Atualiza status da mensagem no banco de dados se disponível
        if hasattr(self.message_handler, "db_interface") and self.message_handler.db_interface:
            self.message_handler.db_interface.update_message_status(
                message_id=message_id,
                status=status
            )
    
    def _process_qr_event(self, data: Dict[str, Any]) -> None:
        """
        Processa evento de código QR
        
        Args:
            data: Dados do código QR
        """
        qr = data.get("qr", "")
        attempt = data.get("attempt", 0)
        
        logger.info(f"Código QR gerado - Tentativa: {attempt}")
    
    def _process_connection_event(self, data: Dict[str, Any]) -> None:
        """
        Processa evento de mudança de estado da conexão
        
        Args:
            data: Dados da conexão
        """
        state = data.get("state", "")
        
        logger.info(f"Estado da conexão alterado: {state}")
    
    def _call_event_handlers(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Chama os handlers registrados para o tipo de evento
        
        Args:
            event_type: Tipo do evento
            data: Dados do evento
        """
        if event_type not in self.event_handlers:
            return
        
        for handler in self.event_handlers[event_type]:
            try:
                handler(data)
            except Exception as e:
                logger.error(f"Erro ao executar handler de evento: {e}")


class WhatsAppWebhookRouter:
    """
    Classe para configuração de rotas FastAPI para webhooks WhatsApp
    """
    
    def __init__(
        self, 
        webhook_handler: WhatsAppWebhookHandler,
        prefix: str = "/webhook/whatsapp"
    ):
        """
        Inicializa o router para webhooks
        
        Args:
            webhook_handler: Instância do handler de webhooks
            prefix: Prefixo para rotas de webhook
        """
        self.webhook_handler = webhook_handler
        self.router = APIRouter(prefix=prefix)
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """
        Configura as rotas para webhooks
        """
        @self.router.post("/")
        async def whatsapp_webhook(
            request: Request,
            x_api_key: Optional[str] = Header(None)
        ):
            # Valida a requisição
            if not self.webhook_handler.validate_webhook_request(x_api_key):
                raise HTTPException(status_code=403, detail="Acesso não autorizado")
            
            # Processa o payload
            payload = await request.json()
            response = self.webhook_handler.process_webhook(payload)
            
            return JSONResponse(content=response)
        
        @self.router.get("/")
        async def whatsapp_webhook_verification(
            request: Request,
            x_api_key: Optional[str] = Header(None)
        ):
            # Valida a requisição
            if not self.webhook_handler.validate_webhook_request(x_api_key):
                raise HTTPException(status_code=403, detail="Acesso não autorizado")
            
            # Responde à verificação
            return JSONResponse(content={"status": "ok", "message": "ZF Portal WhatsApp Webhook Service"})
    
    def get_router(self) -> APIRouter:
        """
        Retorna o router configurado
        
        Returns:
            APIRouter: Router FastAPI para webhooks
        """
        return self.router


# Exemplo de integração com FastAPI
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn
    from whatsapp_connector import WhatsAppConnector
    from whatsapp_message_handler import WhatsAppMessageHandler
    
    # Mock de interface para exemplificar
    class MockDBInterface:
        def update_message_status(self, message_id, status):
            print(f"Status da mensagem atualizado - ID: {message_id}, Status: {status}")
    
    # Configurações
    waha_url = "http://localhost:3000"
    api_key = "zf_portal_waha_key"
    session = "zf_portal_session"
    
    # Inicialização dos componentes
    connector = WhatsAppConnector(waha_url, api_key, session)
    
    # Mock do DB
    db_interface = MockDBInterface()
    
    # Handler de mensagens
    message_handler = WhatsAppMessageHandler(connector)
    message_handler.db_interface = db_interface  # Atribui a interface mock
    
    # Handler de webhook
    webhook_handler = WhatsAppWebhookHandler(message_handler, api_key)
    
    # Adiciona um handler para eventos de mensagem
    def log_message(data):
        print(f"Mensagem recebida: {data}")
    
    webhook_handler.add_event_handler("message", log_message)
    
    # Cria a aplicação FastAPI
    app = FastAPI(title="ZF Portal WhatsApp API")
    
    # Configura router de webhook
    webhook_router = WhatsAppWebhookRouter(webhook_handler)
    app.include_router(webhook_router.get_router())
    
    # Para executar: uvicorn whatsapp_webhook_handler:app --reload
