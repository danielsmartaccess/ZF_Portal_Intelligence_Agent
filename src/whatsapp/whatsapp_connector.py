"""
Módulo para comunicação com servidor WAHA (WhatsApp HTTP API)

Este módulo implementa a interface de comunicação com o servidor WAHA
para envio e recebimento de mensagens WhatsApp.
"""

import requests
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from enum import Enum


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp_connector")


class MessageType(Enum):
    """Tipos de mensagem suportados pelo WhatsApp"""
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    BUTTON = "button"
    TEMPLATE = "template"
    LIST = "list"


class WhatsAppConnector:
    """
    Classe para comunicação com o servidor WAHA (WhatsApp HTTP API)
    """
    
    def __init__(self, base_url: str, api_key: str, session_name: str = "default"):
        """
        Inicializa o conector WhatsApp
        
        Args:
            base_url: URL base do servidor WAHA
            api_key: Chave API para autenticação
            session_name: Nome da sessão WhatsApp (padrão: "default")
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_name = session_name
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        Realiza uma requisição HTTP para o servidor WAHA
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint da API
            data: Dados para envio (opcional)
        
        Returns:
            Dict: Resposta da requisição como dicionário
        
        Raises:
            Exception: Se a requisição falhar
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            raise Exception(f"Falha na comunicação com servidor WAHA: {e}")
    
    def start_session(self) -> Dict:
        """
        Inicia uma sessão WhatsApp
        
        Returns:
            Dict: Resposta da API com status da sessão
        """
        endpoint = f"api/sessions/{self.session_name}/start"
        logger.info(f"Iniciando sessão WhatsApp: {self.session_name}")
        return self._make_request("POST", endpoint)
    
    def check_session_status(self) -> Dict:
        """
        Verifica o status da sessão WhatsApp
        
        Returns:
            Dict: Status da sessão
        """
        endpoint = f"api/sessions/{self.session_name}/status"
        return self._make_request("GET", endpoint)
    
    def get_qr_code(self) -> Dict:
        """
        Obtém o código QR para autenticação WhatsApp
        
        Returns:
            Dict: Dados do código QR
        """
        endpoint = f"api/sessions/{self.session_name}/qr"
        return self._make_request("GET", endpoint)
    
    def stop_session(self) -> Dict:
        """
        Encerra a sessão WhatsApp
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/stop"
        logger.info(f"Encerrando sessão WhatsApp: {self.session_name}")
        return self._make_request("POST", endpoint)
    
    def logout_session(self) -> Dict:
        """
        Realiza logout da sessão WhatsApp
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/logout"
        logger.info(f"Realizando logout da sessão WhatsApp: {self.session_name}")
        return self._make_request("POST", endpoint)
    
    def send_text_message(self, to: str, text: str) -> Dict:
        """
        Envia uma mensagem de texto via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional (ex: 5511999998888)
            text: Texto da mensagem
        
        Returns:
            Dict: Resposta da API com detalhes da mensagem enviada
        """
        endpoint = f"api/sessions/{self.session_name}/messages/text"
        data = {
            "chatId": f"{to}@c.us",
            "text": text
        }
        
        logger.info(f"Enviando mensagem para {to}")
        return self._make_request("POST", endpoint, data)
    
    def send_image(self, to: str, image_url: str, caption: str = None) -> Dict:
        """
        Envia uma imagem via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional
            image_url: URL da imagem ou path base64
            caption: Legenda da imagem (opcional)
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/messages/image"
        data = {
            "chatId": f"{to}@c.us",
            "image": image_url
        }
        
        if caption:
            data["caption"] = caption
        
        logger.info(f"Enviando imagem para {to}")
        return self._make_request("POST", endpoint, data)
    
    def send_document(self, to: str, document_url: str, filename: str = None) -> Dict:
        """
        Envia um documento via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional
            document_url: URL do documento ou path base64
            filename: Nome do arquivo (opcional)
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/messages/document"
        data = {
            "chatId": f"{to}@c.us",
            "document": document_url
        }
        
        if filename:
            data["filename"] = filename
        
        logger.info(f"Enviando documento para {to}")
        return self._make_request("POST", endpoint, data)
    
    def send_template_message(self, to: str, template: Dict[str, Any]) -> Dict:
        """
        Envia uma mensagem de template via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional
            template: Configuração do template conforme documentação WAHA
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/messages/template"
        
        # Garantindo que o template tenha o chatId
        template["chatId"] = f"{to}@c.us"
        
        logger.info(f"Enviando template para {to}")
        return self._make_request("POST", endpoint, template)
    
    def send_button_message(self, to: str, text: str, buttons: List[Dict[str, str]]) -> Dict:
        """
        Envia uma mensagem com botões via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional
            text: Texto da mensagem
            buttons: Lista de botões no formato [{"id": "btn1", "text": "Click me"}]
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/messages/buttons"
        data = {
            "chatId": f"{to}@c.us",
            "text": text,
            "buttons": buttons
        }
        
        logger.info(f"Enviando mensagem com botões para {to}")
        return self._make_request("POST", endpoint, data)
    
    def send_list_message(self, to: str, text: str, button_text: str, sections: List[Dict]) -> Dict:
        """
        Envia uma mensagem com lista de opções via WhatsApp
        
        Args:
            to: Número do destinatário no formato internacional
            text: Texto da mensagem
            button_text: Texto do botão que abre a lista
            sections: Seções da lista conforme documentação WAHA
        
        Returns:
            Dict: Resposta da API
        """
        endpoint = f"api/sessions/{self.session_name}/messages/list"
        data = {
            "chatId": f"{to}@c.us",
            "text": text,
            "buttonText": button_text,
            "sections": sections
        }
        
        logger.info(f"Enviando mensagem com lista para {to}")
        return self._make_request("POST", endpoint, data)
    
    def get_chats(self) -> List[Dict]:
        """
        Obtém a lista de chats
        
        Returns:
            List[Dict]: Lista de chats
        """
        endpoint = f"api/sessions/{self.session_name}/chats"
        response = self._make_request("GET", endpoint)
        return response.get("chats", [])
    
    def get_messages(self, chat_id: str, limit: int = 20) -> List[Dict]:
        """
        Obtém mensagens de um chat específico
        
        Args:
            chat_id: ID do chat
            limit: Limite de mensagens a retornar (padrão: 20)
        
        Returns:
            List[Dict]: Lista de mensagens
        """
        endpoint = f"api/sessions/{self.session_name}/chats/{chat_id}/messages?limit={limit}"
        response = self._make_request("GET", endpoint)
        return response.get("messages", [])
    
    def send_message(self, to: str, message_type: MessageType, content: Union[str, Dict], **kwargs) -> Dict:
        """
        Método genérico para envio de mensagens de diferentes tipos
        
        Args:
            to: Número do destinatário no formato internacional
            message_type: Tipo da mensagem (enum MessageType)
            content: Conteúdo da mensagem (texto, url ou dicionário com configurações)
            **kwargs: Argumentos adicionais específicos para cada tipo de mensagem
        
        Returns:
            Dict: Resposta da API
        """
        if message_type == MessageType.TEXT:
            return self.send_text_message(to, content)
        elif message_type == MessageType.IMAGE:
            return self.send_image(to, content, kwargs.get("caption"))
        elif message_type == MessageType.DOCUMENT:
            return self.send_document(to, content, kwargs.get("filename"))
        elif message_type == MessageType.BUTTON:
            return self.send_button_message(to, content, kwargs.get("buttons", []))
        elif message_type == MessageType.LIST:
            return self.send_list_message(
                to, 
                content, 
                kwargs.get("button_text", "Ver opções"), 
                kwargs.get("sections", [])
            )
        elif message_type == MessageType.TEMPLATE:
            if isinstance(content, dict):
                return self.send_template_message(to, content)
            raise ValueError("Para mensagens de template, o content deve ser um dicionário")
        else:
            raise ValueError(f"Tipo de mensagem não implementado: {message_type}")


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de configuração
    waha_url = "http://localhost:3000"
    api_key = "zf_portal_waha_key"
    session = "zf_portal_session"
    
    # Inicialização do conector
    connector = WhatsAppConnector(waha_url, api_key, session)
    
    # Inicia a sessão
    session_status = connector.start_session()
    print(f"Status da sessão: {session_status}")
    
    # Verificação de QR code (quando necessário)
    qr_data = connector.get_qr_code()
    if "qr" in qr_data:
        print(f"Escaneie o QR code: {qr_data['qr']}")
    
    # Espera pela autenticação
    print("Aguardando autenticação...")
    while True:
        status = connector.check_session_status()
        if status.get("status") == "CONNECTED":
            print("Sessão conectada com sucesso!")
            break
        time.sleep(5)
    
    # Exemplo de envio de mensagem
    number = "5511999998888"  # Substitua pelo número real
    response = connector.send_text_message(number, "Olá do ZF Portal Intelligence Agent!")
    print(f"Mensagem enviada: {response}")
