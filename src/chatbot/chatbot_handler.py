"""
Módulo de manipulação de mensagens do chatbot

Este módulo implementa a lógica para processar mensagens recebidas e 
gerar respostas adequadas para o chatbot.
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
import json
import os
import random
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("chatbot_handler")


@dataclass
class ChatbotResponse:
    """
    Classe para representar uma resposta do chatbot
    """
    text: str
    buttons: List[str] = None
    button_text: str = None


class ChatbotHandler:
    """
    Manipulador de lógica do chatbot
    """
    
    def __init__(self):
        """
        Inicializa o manipulador de chatbot
        """
        # Carregar configurações e respostas pré-definidas
        self.load_responses()
        
        # Dicionário para armazenar o contexto das conversas (por usuário)
        self.conversation_contexts = {}
    
    def load_responses(self):
        """
        Carrega as respostas pré-definidas do chatbot
        """
        # Definir respostas padrão
        self.responses = {
            "greeting": [
                "Olá! Bem-vindo ao ZF Portal Intelligence Agent. Como posso ajudar você hoje?",
                "Oi! Sou o assistente virtual da ZF. Em que posso ser útil?",
                "Olá! Estou aqui para ajudar com suas dúvidas sobre ZF. Como posso ajudar?"
            ],
            "unknown": [
                "Não entendi sua mensagem. Poderia reformular?",
                "Desculpe, não consegui compreender. Poderia explicar melhor?",
                "Hmm, não tenho certeza do que você precisa. Poderia detalhar mais sua solicitação?"
            ],
            "farewell": [
                "Até logo! Foi um prazer ajudar.",
                "Até breve! Volte sempre que precisar.",
                "Obrigado por entrar em contato. Estou à disposição para futuras consultas!"
            ],
            "help": [
                "Posso ajudar com informações sobre ZF, serviços disponíveis, agendamento de consultas e muito mais. Como posso auxiliar hoje?"
            ]
        }
        
        # Tentar carregar respostas personalizadas de arquivo, se existir
        responses_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses.json")
        if os.path.exists(responses_file):
            try:
                with open(responses_file, 'r', encoding='utf-8') as file:
                    custom_responses = json.load(file)
                    # Combinar com respostas padrão
                    self.responses.update(custom_responses)
                logger.info(f"Respostas personalizadas carregadas de {responses_file}")
            except Exception as e:
                logger.error(f"Erro ao carregar respostas personalizadas: {e}")
    
    def _get_random_response(self, category: str) -> str:
        """
        Retorna uma resposta aleatória para a categoria especificada
        
        Args:
            category: Categoria da resposta
            
        Returns:
            str: Resposta aleatória
        """
        responses = self.responses.get(category, self.responses["unknown"])
        return random.choice(responses)
    
    def _identify_intent(self, message: str) -> str:
        """
        Identifica a intenção da mensagem
        
        Args:
            message: Texto da mensagem
            
        Returns:
            str: Intenção identificada
        """
        message = message.lower().strip()
        
        # Padrões simples para intenções básicas
        if re.search(r'\b(oi|olá|ola|bom dia|boa tarde|boa noite|hey|hi)\b', message):
            return "greeting"
        
        elif re.search(r'\b(tchau|adeus|até logo|ate logo|até mais|ate mais)\b', message):
            return "farewell"
        
        elif re.search(r'\b(ajuda|help|socorro|auxílio|auxilio|como funciona|instruções|instrucoes)\b', message):
            return "help"
            
        elif re.search(r'\b(serviços|servicos|produtos|ofertas)\b', message):
            return "services"
            
        elif re.search(r'\b(preço|preco|valor|custo|quanto custa)\b', message):
            return "pricing"
            
        elif re.search(r'\b(contato|telefone|email|e-mail|endereço|endereco|localização|localizacao)\b', message):
            return "contact"
            
        elif re.search(r'\b(agendar|agenda|marcar|reservar|consulta)\b', message):
            return "appointment"
            
        return "unknown"
    
    def _update_context(self, user_id: str, message: str, intent: str):
        """
        Atualiza o contexto da conversa para um usuário
        
        Args:
            user_id: ID do usuário
            message: Mensagem recebida
            intent: Intenção identificada
        """
        # Inicializar contexto se não existir
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                "last_message": "",
                "last_intent": "",
                "message_count": 0,
                "conversation_start": datetime.now(),
                "history": []
            }
        
        # Atualizar contexto
        context = self.conversation_contexts[user_id]
        context["last_message"] = message
        context["last_intent"] = intent
        context["message_count"] += 1
        
        # Adicionar ao histórico (limitado a 10 mensagens)
        context["history"].append({
            "message": message,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(context["history"]) > 10:
            context["history"].pop(0)
    
    def _get_response_for_intent(self, intent: str, user_id: str) -> ChatbotResponse:
        """
        Gera uma resposta para a intenção identificada
        
        Args:
            intent: Intenção identificada
            user_id: ID do usuário
            
        Returns:
            ChatbotResponse: Resposta formatada do chatbot
        """
        # Obter contexto da conversa
        context = self.conversation_contexts.get(user_id, {})
        message_count = context.get("message_count", 0)
        
        # Processar intenções específicas
        if intent == "greeting":
            # Se for primeira mensagem
            if message_count <= 1:
                text = self._get_random_response("greeting")
                buttons = ["Quero saber mais", "Falar com atendente"]
                return ChatbotResponse(text=text, buttons=buttons, button_text="Escolha uma opção")
            else:
                text = "Como posso ajudar hoje?"
                return ChatbotResponse(text=text)
        
        elif intent == "farewell":
            text = self._get_random_response("farewell")
            return ChatbotResponse(text=text)
        
        elif intent == "help":
            text = self._get_random_response("help")
            buttons = ["Conhecer serviços", "Falar com atendente", "Agendar consulta"]
            return ChatbotResponse(text=text, buttons=buttons, button_text="Escolha uma opção")
        
        elif intent == "services":
            text = "A ZF oferece soluções tecnológicas avançadas para o setor automotivo. Nossos principais serviços incluem: \n\n" + \
                   "🚗 Sistemas de transmissão\n" + \
                   "🛡️ Sistemas de segurança veicular\n" + \
                   "⚙️ Componentes de chassis\n" + \
                   "🔌 Sistemas eletrônicos"
            buttons = ["Solicitar orçamento", "Falar com especialista"]
            return ChatbotResponse(text=text, buttons=buttons, button_text="Próximo passo")
        
        elif intent == "pricing":
            text = "Para informações detalhadas sobre preços e orçamentos, precisamos entender melhor sua necessidade específica. Posso colocar você em contato com nossa equipe comercial."
            buttons = ["Falar com comercial", "Solicitar ligação"]
            return ChatbotResponse(text=text, buttons=buttons, button_text="Como prefere?")
            
        elif intent == "contact":
            text = "Entre em contato com a ZF pelos canais: \n\n" + \
                   "📞 Telefone: (11) 4009-0000\n" + \
                   "📧 E-mail: contato@zf.com\n" + \
                   "🌐 Site: www.zf.com/br\n" + \
                   "📍 Endereço: Av. Engenheiro Luís Carlos Berrini, 105 - São Paulo/SP"
            return ChatbotResponse(text=text)
            
        elif intent == "appointment":
            text = "Para agendar uma consulta com nossos especialistas, preciso de algumas informações. Qual seria o melhor dia e horário para você?"
            return ChatbotResponse(text=text)
            
        else:  # unknown ou outras intenções
            text = self._get_random_response("unknown")
            buttons = ["Menu principal", "Falar com atendente"]
            return ChatbotResponse(text=text, buttons=buttons, button_text="Precisa de ajuda?")
    
    def process_message(self, user_id: str, message: str) -> ChatbotResponse:
        """
        Processa uma mensagem recebida e retorna uma resposta
        
        Args:
            user_id: ID do usuário (número de telefone)
            message: Texto da mensagem recebida
            
        Returns:
            ChatbotResponse: Resposta do chatbot
        """
        try:
            # Identificar intenção
            intent = self._identify_intent(message)
            
            # Atualizar contexto
            self._update_context(user_id, message, intent)
            
            # Gerar resposta
            response = self._get_response_for_intent(intent, user_id)
            
            # Registrar interação
            logger.info(f"Mensagem de {user_id} com intent '{intent}'. Resposta: {response.text[:30]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            # Resposta de fallback em caso de erro
            return ChatbotResponse(
                text="Desculpe, tive um problema ao processar sua mensagem. Por favor, tente novamente em instantes."
            )
