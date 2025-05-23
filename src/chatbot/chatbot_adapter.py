"""
Adaptador para integração do chatbot com o sistema principal

Este módulo conecta o chatbot WhatsApp ao sistema principal da aplicação,
permitindo a utilização dos serviços existentes.
"""

import logging
import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot_adapter")


class ChatbotSystemAdapter:
    """
    Adaptador para integração do chatbot com o sistema principal
    """
    
    def __init__(self, db_service=None, llm_service=None, config_service=None):
        """
        Inicializa o adaptador de sistema para o chatbot
        
        Args:
            db_service: Serviço de banco de dados
            llm_service: Serviço de modelo de linguagem (LLM)
            config_service: Serviço de configuração
        """
        self.db_service = db_service
        self.llm_service = llm_service
        self.config_service = config_service
        
        # Carregar configurações
        self.config = self._load_config()
        
        logger.info("Adaptador de sistema para chatbot inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega configurações para o chatbot
        
        Returns:
            Dict[str, Any]: Configurações do chatbot
        """
        # Primeiro tenta usar o serviço de configuração, se disponível
        if self.config_service:
            try:
                return self.config_service.get_config("chatbot") or {}
            except Exception as e:
                logger.warning(f"Erro ao carregar configurações pelo serviço: {e}")
        
        # Configurações padrão
        return {
            "log_conversations": True,
            "use_llm": False,  # Desativado por padrão, será implementado no futuro
            "save_contacts": True,
            "auto_respond": True
        }
    
    def log_conversation(self, user_id: str, message: str, is_incoming: bool) -> bool:
        """
        Registra uma conversa no banco de dados
        
        Args:
            user_id: ID do usuário (número de telefone)
            message: Texto da mensagem
            is_incoming: True se a mensagem foi recebida, False se foi enviada
            
        Returns:
            bool: True se o registro foi bem-sucedido
        """
        if not self.config.get("log_conversations", True):
            return True  # Logging desabilitado
            
        # Se o serviço de banco de dados estiver disponível
        if self.db_service:
            try:
                # Registra a conversa no banco de dados
                message_data = {
                    "user_id": user_id,
                    "message": message,
                    "is_incoming": is_incoming,
                    "timestamp": datetime.now()
                }
                
                self.db_service.add_conversation_log(message_data)
                return True
            except Exception as e:
                logger.error(f"Erro ao registrar conversa: {e}")
                return False
        
        # Se não houver serviço de banco de dados, simplesmente loga
        logger.info(f"{'Recebida de' if is_incoming else 'Enviada para'} {user_id}: {message}")
        return True
    
    def save_contact(self, user_id: str, contact_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva ou atualiza um contato no banco de dados
        
        Args:
            user_id: ID do usuário (número de telefone)
            contact_data: Dados adicionais do contato (opcional)
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        if not self.config.get("save_contacts", True):
            return True  # Salvamento desabilitado
            
        # Se o serviço de banco de dados estiver disponível
        if self.db_service:
            try:
                # Dados básicos do contato
                data = {
                    "phone_number": user_id,
                    "last_contact": datetime.now(),
                    "source": "chatbot_whatsapp"
                }
                
                # Adicionar dados extras, se fornecidos
                if contact_data:
                    data.update(contact_data)
                
                # Salvar ou atualizar contato
                self.db_service.add_or_update_contact(data)
                return True
            except Exception as e:
                logger.error(f"Erro ao salvar contato: {e}")
                return False
        
        # Se não houver serviço de banco de dados
        logger.info(f"Contato registrado: {user_id}")
        return True
    
    def generate_llm_response(self, user_id: str, message: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Gera uma resposta usando o modelo de linguagem
        
        Args:
            user_id: ID do usuário (número de telefone)
            message: Texto da mensagem
            context: Contexto da conversa
            
        Returns:
            Optional[str]: Resposta gerada pelo LLM ou None se não disponível
        """
        if not self.config.get("use_llm", False):
            return None  # LLM desabilitado
            
        # Se o serviço LLM estiver disponível
        if self.llm_service:
            try:
                # Formatar contexto para o LLM
                prompt = self._format_llm_prompt(user_id, message, context)
                
                # Obter resposta do LLM
                response = self.llm_service.generate_response(prompt)
                return response
            except Exception as e:
                logger.error(f"Erro ao gerar resposta com LLM: {e}")
                return None
        
        # Se não houver serviço LLM
        return None
    
    def _format_llm_prompt(self, user_id: str, message: str, context: Dict[str, Any]) -> str:
        """
        Formata o prompt para o LLM
        
        Args:
            user_id: ID do usuário (número de telefone)
            message: Texto da mensagem
            context: Contexto da conversa
            
        Returns:
            str: Prompt formatado
        """
        # Histórico das últimas mensagens
        history = context.get("history", [])
        history_text = ""
        
        for entry in history:
            history_text += f"{'Usuário' if entry.get('is_incoming', True) else 'Assistente'}: {entry.get('message', '')}\n"
        
        # Formatar prompt
        prompt = f"""
        Você é um assistente virtual da ZF Portal, respondendo a mensagens de WhatsApp.
        
        Informações do usuário:
        - Número: {user_id}
        - Mensagens anteriores: {len(history)}
        
        Histórico recente:
        {history_text}
        
        Nova mensagem do usuário: {message}
        
        Responda de forma educada e profissional, fornecendo informações sobre produtos e serviços da ZF quando apropriado.
        """
        
        return prompt.strip()
