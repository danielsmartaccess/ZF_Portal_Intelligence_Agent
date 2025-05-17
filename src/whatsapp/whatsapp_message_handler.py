"""
Módulo para processamento de mensagens WhatsApp

Este módulo implementa o processamento de mensagens recebidas e enviadas
via WhatsApp, incluindo análise de conteúdo e integração com o modelo
de linguagem (LLM) para respostas inteligentes.
"""

import json
import logging
import re
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from enum import Enum

from .whatsapp_connector import WhatsAppConnector, MessageType

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp_message_handler")


class FunnelStage(Enum):
    """Estágios do funil de marketing"""
    UNKNOWN = "unknown"
    ATTRACTION = "attraction"  # Atração
    RELATIONSHIP = "relationship"  # Relacionamento
    CONVERSION = "conversion"  # Conversão
    CUSTOMER = "customer"  # Cliente


class MessageIntent(Enum):
    """Intenções identificadas em mensagens"""
    GREETING = "greeting"  # Saudação
    QUESTION = "question"  # Pergunta
    INTEREST = "interest"  # Demonstração de interesse
    COMPLAINT = "complaint"  # Reclamação
    OBJECTION = "objection"  # Objeção
    REQUEST_INFO = "request_info"  # Solicitação de informação
    READY_TO_BUY = "ready_to_buy"  # Pronto para comprar
    APPOINTMENT = "appointment"  # Agendamento
    THANK_YOU = "thank_you"  # Agradecimento
    FAREWELL = "farewell"  # Despedida
    OTHER = "other"  # Outros


class WhatsAppMessageHandler:
    """
    Classe para processamento de mensagens WhatsApp
    """
    
    def __init__(
        self, 
        whatsapp_connector: WhatsAppConnector,
        llm_interface=None,
        db_interface=None,
        templates_manager=None
    ):
        """
        Inicializa o processador de mensagens WhatsApp
        
        Args:
            whatsapp_connector: Instância do conector WhatsApp
            llm_interface: Interface para comunicação com modelo de linguagem
            db_interface: Interface para acesso ao banco de dados
            templates_manager: Gerenciador de templates de mensagem
        """
        self.connector = whatsapp_connector
        self.llm_interface = llm_interface
        self.db_interface = db_interface
        self.templates_manager = templates_manager
        self.message_handlers: Dict[str, List[Callable]] = {
            "text": [],
            "image": [],
            "document": [],
            "audio": [],
            "video": [],
            "button_response": [],
            "list_response": [],
            "any": []
        }
    
    def add_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Adiciona um handler para um tipo específico de mensagem
        
        Args:
            message_type: Tipo de mensagem (text, image, etc.) ou "any"
            handler: Função de callback que processa a mensagem
                     Deve aceitar um parâmetro dict com os dados da mensagem
        """
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        
        self.message_handlers[message_type].append(handler)
    
    def process_incoming_message(self, message_data: Dict[str, Any]) -> None:
        """
        Processa uma mensagem recebida pelo webhook
        
        Args:
            message_data: Dados da mensagem recebida
        """
        try:
            logger.info(f"Processando mensagem: {message_data.get('id', 'sem id')}")
            
            # Extrai informações básicas
            message_type = self._get_message_type(message_data)
            
            # Registra detalhes da mensagem
            self._log_message_details(message_data, message_type)
            
            # Salva a mensagem no banco de dados se disponível
            if self.db_interface:
                self._save_message_to_db(message_data, message_type)
            
            # Chama os handlers específicos para o tipo de mensagem
            self._call_message_handlers(message_type, message_data)
            
            # Chama os handlers genéricos
            self._call_message_handlers("any", message_data)
            
            # Se temos integração com LLM, analisa a mensagem
            if self.llm_interface and message_type == "text":
                self._analyze_message_with_llm(message_data)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
    
    def _get_message_type(self, message_data: Dict[str, Any]) -> str:
        """
        Determina o tipo de mensagem recebida
        
        Args:
            message_data: Dados da mensagem
        
        Returns:
            str: Tipo da mensagem (text, image, etc.)
        """
        # Lógica para identificar o tipo de mensagem com base na estrutura
        if "message" in message_data:
            msg = message_data["message"]
            
            # Verifica o tipo com base na presença de campos específicos
            if "text" in msg:
                return "text"
            elif "imageMessage" in msg:
                return "image"
            elif "documentMessage" in msg:
                return "document"
            elif "audioMessage" in msg:
                return "audio"
            elif "videoMessage" in msg:
                return "video"
            elif "buttonResponseMessage" in msg:
                return "button_response"
            elif "listResponseMessage" in msg:
                return "list_response"
        
        # Se não conseguir identificar
        return "unknown"
    
    def _log_message_details(self, message_data: Dict[str, Any], message_type: str) -> None:
        """
        Registra detalhes da mensagem no log
        
        Args:
            message_data: Dados da mensagem
            message_type: Tipo da mensagem
        """
        sender = message_data.get("key", {}).get("remoteJid", "desconhecido")
        sender = sender.split("@")[0] if "@" in sender else sender
        
        message_id = message_data.get("key", {}).get("id", "sem id")
        
        logger.info(f"Mensagem de {sender} ({message_type}): ID={message_id}")
    
    def _save_message_to_db(self, message_data: Dict[str, Any], message_type: str) -> None:
        """
        Salva a mensagem no banco de dados
        
        Args:
            message_data: Dados da mensagem
            message_type: Tipo da mensagem
        """
        if not self.db_interface:
            return
        
        try:
            # Extrai informações da mensagem
            sender = message_data.get("key", {}).get("remoteJid", "")
            sender = sender.split("@")[0] if "@" in sender else sender
            
            message_id = message_data.get("key", {}).get("id", "")
            timestamp = message_data.get("messageTimestamp", "")
            
            # Extrai o conteúdo da mensagem com base no tipo
            content = self._extract_message_content(message_data, message_type)
            
            # Cria dicionário com dados para salvar
            message_record = {
                "message_id": message_id,
                "sender": sender,
                "message_type": message_type,
                "content": content,
                "timestamp": timestamp,
                "raw_data": json.dumps(message_data)
            }
            
            # Salva no banco de dados
            self.db_interface.save_whatsapp_message(message_record)
            
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem no banco de dados: {e}")
    
    def _extract_message_content(self, message_data: Dict[str, Any], message_type: str) -> str:
        """
        Extrai o conteúdo da mensagem com base no tipo
        
        Args:
            message_data: Dados da mensagem
            message_type: Tipo da mensagem
        
        Returns:
            str: Conteúdo da mensagem
        """
        if "message" not in message_data:
            return ""
        
        msg = message_data["message"]
        
        if message_type == "text":
            return msg.get("text", "")
        elif message_type == "image":
            return msg.get("imageMessage", {}).get("caption", "[Imagem]")
        elif message_type == "document":
            doc = msg.get("documentMessage", {})
            return f"[Documento: {doc.get('fileName', 'sem nome')}]"
        elif message_type == "audio":
            return "[Áudio]"
        elif message_type == "video":
            return msg.get("videoMessage", {}).get("caption", "[Vídeo]")
        elif message_type == "button_response":
            return msg.get("buttonResponseMessage", {}).get("selectedButtonId", "")
        elif message_type == "list_response":
            return msg.get("listResponseMessage", {}).get("title", "")
        
        return "[Conteúdo não interpretado]"
    
    def _call_message_handlers(self, message_type: str, message_data: Dict[str, Any]) -> None:
        """
        Chama os handlers registrados para o tipo de mensagem
        
        Args:
            message_type: Tipo da mensagem
            message_data: Dados da mensagem
        """
        if message_type not in self.message_handlers:
            return
        
        for handler in self.message_handlers[message_type]:
            try:
                handler(message_data)
            except Exception as e:
                logger.error(f"Erro ao executar handler de mensagem: {e}")
    
    def _analyze_message_with_llm(self, message_data: Dict[str, Any]) -> None:
        """
        Analisa a mensagem com o modelo de linguagem
        
        Args:
            message_data: Dados da mensagem
        """
        if not self.llm_interface:
            return
        
        try:
            # Extrai o texto da mensagem
            message_text = message_data.get("message", {}).get("text", "")
            if not message_text:
                return
            
            # Extrai sender para contexto
            sender = message_data.get("key", {}).get("remoteJid", "")
            sender = sender.split("@")[0] if "@" in sender else sender
            
            # Obtém contexto do contato do banco de dados
            contact_info = {}
            if self.db_interface:
                contact_info = self.db_interface.get_contact_by_whatsapp(sender) or {}
            
            # Análise com LLM
            analysis = self.llm_interface.analyze_message(
                message_text,
                sender,
                contact_info=contact_info
            )
            
            # Processa o resultado da análise
            self._process_llm_analysis(sender, message_text, analysis)
            
        except Exception as e:
            logger.error(f"Erro ao analisar mensagem com LLM: {e}")
    
    def _process_llm_analysis(
        self, 
        sender: str, 
        message_text: str, 
        analysis: Dict[str, Any]
    ) -> None:
        """
        Processa o resultado da análise do LLM
        
        Args:
            sender: Número do remetente
            message_text: Texto da mensagem
            analysis: Resultado da análise do LLM
        """
        if not analysis:
            return
        
        try:
            # Extrai informações da análise
            intent = analysis.get("intent", MessageIntent.OTHER.value)
            sentiment = analysis.get("sentiment", "neutral")
            funnel_stage = analysis.get("funnel_stage", FunnelStage.UNKNOWN.value)
            suggested_response = analysis.get("suggested_response")
            next_actions = analysis.get("next_actions", [])
            
            logger.info(f"Análise LLM - Intenção: {intent}, Sentimento: {sentiment}, Estágio: {funnel_stage}")
            
            # Atualiza informações do contato no DB
            if self.db_interface:
                self.db_interface.update_contact_analysis(
                    whatsapp=sender,
                    intent=intent,
                    sentiment=sentiment,
                    funnel_stage=funnel_stage
                )
            
            # Se há uma resposta sugerida, envia
            if suggested_response and self.db_interface:
                # Verifica se existe configuração de automação para resposta
                auto_settings = self.db_interface.get_automation_settings()
                
                if auto_settings.get("auto_respond", False):
                    # Se configurado para resposta automática, envia a resposta
                    self.send_text_message(sender, suggested_response)
                    logger.info(f"Resposta automática enviada para {sender}")
                else:
                    # Caso contrário, salva como sugestão
                    self.db_interface.save_suggested_response(
                        whatsapp=sender,
                        original_message=message_text,
                        suggested_response=suggested_response
                    )
                    logger.info(f"Resposta sugerida salva para {sender}")
            
            # Processa ações recomendadas
            for action in next_actions:
                self._process_recommended_action(sender, action)
            
        except Exception as e:
            logger.error(f"Erro ao processar análise do LLM: {e}")
    
    def _process_recommended_action(self, sender: str, action: Dict[str, Any]) -> None:
        """
        Processa uma ação recomendada pelo LLM
        
        Args:
            sender: Número do remetente
            action: Ação recomendada
        """
        action_type = action.get("type")
        
        if not action_type:
            return
        
        try:
            if action_type == "schedule_followup":
                # Agendar seguimento
                when = action.get("when")
                message = action.get("message")
                
                if when and message and self.db_interface:
                    self.db_interface.schedule_message(
                        to=sender,
                        message=message,
                        scheduled_time=when
                    )
                    logger.info(f"Agendado seguimento para {sender} em {when}")
                    
            elif action_type == "update_funnel_stage":
                # Atualizar estágio no funil
                new_stage = action.get("stage")
                
                if new_stage and self.db_interface:
                    self.db_interface.update_contact_funnel_stage(
                        whatsapp=sender,
                        funnel_stage=new_stage
                    )
                    logger.info(f"Estágio do funil atualizado para {sender}: {new_stage}")
                    
            elif action_type == "tag_contact":
                # Adicionar tag ao contato
                tags = action.get("tags", [])
                
                if tags and self.db_interface:
                    self.db_interface.add_contact_tags(
                        whatsapp=sender,
                        tags=tags
                    )
                    logger.info(f"Tags adicionadas para {sender}: {', '.join(tags)}")
                    
            elif action_type == "notify_human":
                # Notificar um humano para intervir
                reason = action.get("reason", "Intervenção necessária")
                
                if self.db_interface:
                    self.db_interface.create_human_task(
                        whatsapp=sender,
                        reason=reason
                    )
                    logger.info(f"Notificação criada para intervenção humana com {sender}")
                
        except Exception as e:
            logger.error(f"Erro ao processar ação recomendada: {e}")
    
    def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto
        
        Args:
            to: Número do destinatário
            text: Texto da mensagem
        
        Returns:
            Dict: Resposta da API
        """
        return self.connector.send_text_message(to, text)
    
    def send_template_message(self, to: str, template_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envia mensagem de template com parâmetros
        
        Args:
            to: Número do destinatário
            template_name: Nome do template
            params: Parâmetros para preencher o template
        
        Returns:
            Dict: Resposta da API
        """
        if not self.templates_manager:
            raise ValueError("Template manager não configurado")
        
        template_content = self.templates_manager.get_template(template_name, params or {})
        
        if not template_content:
            raise ValueError(f"Template não encontrado: {template_name}")
        
        return self.connector.send_text_message(to, template_content)
    
    def send_message_by_funnel_stage(self, to: str, funnel_stage: FunnelStage, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Envia mensagem apropriada para o estágio do funil
        
        Args:
            to: Número do destinatário
            funnel_stage: Estágio do funil
            params: Parâmetros adicionais
        
        Returns:
            Dict: Resposta da API
        """
        # Mapeia estágios do funil para templates
        template_mapping = {
            FunnelStage.ATTRACTION: "atracao_inicial",
            FunnelStage.RELATIONSHIP: "relacionamento_lead",
            FunnelStage.CONVERSION: "oferta_conversao",
            FunnelStage.CUSTOMER: "boas_vindas_cliente"
        }
        
        # Se for um estágio desconhecido, usa template genérico
        template_name = template_mapping.get(funnel_stage, "mensagem_generica")
        
        # Envia o template
        return self.send_template_message(to, template_name, params)
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analisa um texto com o LLM sem enviar mensagem
        
        Args:
            text: Texto para análise
        
        Returns:
            Dict: Resultado da análise
        """
        if not self.llm_interface:
            return {}
        
        try:
            return self.llm_interface.analyze_text(text)
        except Exception as e:
            logger.error(f"Erro ao analisar texto com LLM: {e}")
            return {}


# Exemplo de uso
if __name__ == "__main__":
    # Mock das interfaces
    class MockLLMInterface:
        def analyze_message(self, text, sender, contact_info=None):
            print(f"Analisando mensagem: {text}")
            return {
                "intent": MessageIntent.GREETING.value,
                "sentiment": "positive",
                "funnel_stage": FunnelStage.ATTRACTION.value,
                "suggested_response": f"Olá! Obrigado pela mensagem: '{text}'",
                "next_actions": [
                    {
                        "type": "tag_contact",
                        "tags": ["novo_contato", "interesse_inicial"]
                    }
                ]
            }
    
    class MockDBInterface:
        def save_whatsapp_message(self, message):
            print(f"Salvando mensagem no DB: {message}")
            
        def get_contact_by_whatsapp(self, whatsapp):
            return {"nome": "Contato Teste", "email": "teste@example.com"}
            
        def update_contact_analysis(self, whatsapp, intent, sentiment, funnel_stage):
            print(f"Atualizando análise do contato {whatsapp}: {intent}, {sentiment}, {funnel_stage}")
            
        def get_automation_settings(self):
            return {"auto_respond": True}
    
    # Configuração para exemplo
    from whatsapp_connector import WhatsAppConnector
    
    waha_url = "http://localhost:3000"
    api_key = "zf_portal_waha_key"
    session = "zf_portal_session"
    
    # Inicializa o conector
    connector = WhatsAppConnector(waha_url, api_key, session)
    
    # Cria interfaces mock
    llm = MockLLMInterface()
    db = MockDBInterface()
    
    # Inicializa o handler
    handler = WhatsAppMessageHandler(connector, llm, db)
    
    # Exemplo de mensagem recebida
    sample_message = {
        "key": {
            "remoteJid": "5511999998888@c.us",
            "id": "MSG_ID_12345"
        },
        "messageTimestamp": 1691234567,
        "message": {
            "text": "Olá, gostaria de saber mais sobre seus produtos!"
        }
    }
    
    # Processa a mensagem
    handler.process_incoming_message(sample_message)
