"""
Serviço de gerenciamento do chatbot para WhatsApp.

Este módulo implementa a lógica principal para gerenciar o chatbot,
conectando-o ao WhatsApp via WAHA.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from src.whatsapp.whatsapp_connector import WhatsAppConnector, MessageType
from src.whatsapp.whatsapp_message_handler import WhatsAppMessageHandler
from .chatbot_handler import ChatbotHandler, ChatbotResponse

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot_service")


class ChatbotService:
    """
    Serviço para gerenciar o chatbot WhatsApp
    """
    
    def __init__(self, 
                waha_url: str = "http://localhost:3000", 
                api_key: str = "zf-portal-api-key", 
                session_name: str = "zf-portal"):
        """
        Inicializa o serviço de chatbot
        
        Args:
            waha_url: URL do servidor WAHA (padrão: http://localhost:3000)
            api_key: Chave API para autenticação com WAHA (padrão: zf-portal-api-key)
            session_name: Nome da sessão WhatsApp (padrão: zf-portal)
        """
        self.waha_url = waha_url
        self.api_key = api_key
        self.session_name = session_name
        
        # Inicializar conector WhatsApp
        self.connector = WhatsAppConnector(waha_url, api_key, session_name)
        
        # Inicializar handler de chatbot
        self.chatbot_handler = ChatbotHandler()
        
        # Inicializar handler de mensagens WhatsApp
        self.message_handler = WhatsAppMessageHandler(self.connector)
        
        # Registrar handlers para mensagens
        self._register_message_handlers()
        
        # Estado da sessão
        self.is_connected = False
    
    def _register_message_handlers(self):
        """Registra handlers para processar mensagens"""
        self.message_handler.add_text_handler(self._process_text_message)
    
    def _process_text_message(self, message_data: Dict[str, Any]) -> bool:
        """
        Processa mensagens de texto recebidas
        
        Args:
            message_data: Dados da mensagem recebida
            
        Returns:
            bool: True se a mensagem foi processada com sucesso
        """
        try:
            # Extrair informações relevantes da mensagem
            sender = message_data.get("key", {}).get("remoteJid", "").split('@')[0]
            text = message_data.get("message", {}).get("conversation", "")
            
            if not text:
                # Tentar extrair texto de mensagem extendida
                ext_msg = message_data.get("message", {}).get("extendedTextMessage", {})
                text = ext_msg.get("text", "")
            
            if not text or not sender:
                logger.warning("Mensagem recebida sem texto ou remetente")
                return False
            
            logger.info(f"Mensagem recebida de {sender}: {text}")
            
            # Processar mensagem com o chatbot
            response = self.chatbot_handler.process_message(sender, text)
            
            # Enviar resposta
            self.connector.send_text_message(sender, response.text)
            
            # Se houver botões na resposta
            if response.buttons:
                buttons = [{"id": str(i), "text": btn} for i, btn in enumerate(response.buttons)]
                self.connector.send_button_message(sender, response.button_text or "Opções:", buttons)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de texto: {e}")
            return False
    
    def start(self) -> bool:
        """
        Inicia o serviço de chatbot
        
        Returns:
            bool: True se o serviço foi iniciado com sucesso
        """
        try:
            # Iniciar sessão WhatsApp
            status = self.connector.start_session()
            logger.info(f"Status da sessão WhatsApp: {status}")
            
            # Verificar status da sessão
            self._check_session_connected()
            
            return self.is_connected
        except Exception as e:
            logger.error(f"Erro ao iniciar serviço de chatbot: {e}")
            return False
    
    def _check_session_connected(self) -> bool:
        """
        Verifica se a sessão está conectada
        
        Returns:
            bool: True se a sessão estiver conectada
        """
        try:
            status = self.connector.check_session_status()
            self.is_connected = status.get("status") == "CONNECTED"
            return self.is_connected
        except Exception as e:
            logger.error(f"Erro ao verificar status da sessão: {e}")
            self.is_connected = False
            return False
    
    def get_qr_code(self) -> Optional[str]:
        """
        Obtém o QR code para autenticação
        
        Returns:
            Optional[str]: String do QR code ou None se não disponível
        """
        try:
            qr_data = self.connector.get_qr_code()
            return qr_data.get("qr")
        except Exception as e:
            logger.error(f"Erro ao obter QR code: {e}")
            return None
    
    def send_message(self, to: str, text: str) -> bool:
        """
        Envia uma mensagem de texto
        
        Args:
            to: Número do destinatário
            text: Texto da mensagem
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        try:
            self.connector.send_text_message(to, text)
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem: {e}")
            return False
    
    def send_template(self, to: str, template_name: str, template_data: Dict[str, Any]) -> bool:
        """
        Envia uma mensagem de template
        
        Args:
            to: Número do destinatário
            template_name: Nome do template
            template_data: Dados para o template
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        try:
            # Formatar template conforme documentação WAHA
            template = {
                "name": template_name,
                "language": {
                    "code": "pt_BR"
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": template_data.get("parameters", [])
                    }
                ]
            }
            
            self.connector.send_template_message(to, template)
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar template: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Para o serviço de chatbot
        
        Returns:
            bool: True se o serviço foi parado com sucesso
        """
        try:
            self.connector.stop_session()
            logger.info("Serviço de chatbot parado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao parar serviço de chatbot: {e}")
            return False
