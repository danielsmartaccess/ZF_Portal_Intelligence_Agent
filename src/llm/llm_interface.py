"""
Módulo de interface para comunicação com Modelos de Linguagem (LLM)

Este módulo implementa interfaces para comunicação com diferentes
provedores de modelos de linguagem (LLM) como OpenAI, Azure OpenAI,
Anthropic, entre outros.
"""

import os
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import requests
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from functools import lru_cache

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("llm_interface")


class LLMProvider(Enum):
    """Provedores de LLM suportados"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    CUSTOM = "custom"


class BaseLLMInterface(ABC):
    """
    Classe base para interfaces de comunicação com LLMs
    """
    
    @abstractmethod
    def complete_prompt(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Completa um prompt com o LLM
        
        Args:
            prompt: Prompt para o LLM
            max_tokens: Número máximo de tokens na resposta
        
        Returns:
            str: Resposta do LLM
        """
        pass
    
    @abstractmethod
    def analyze_message(
        self, 
        message: str, 
        sender: str = None, 
        contact_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analisa uma mensagem para extrair intenção e outras informações
        
        Args:
            message: Texto da mensagem
            sender: Identificador do remetente (opcional)
            contact_info: Informações adicionais sobre o contato (opcional)
        
        Returns:
            Dict: Resultado da análise
        """
        pass
    
    @abstractmethod
    def generate_response(
        self, 
        message: str, 
        context: Dict[str, Any] = None, 
        tone: str = "professional"
    ) -> str:
        """
        Gera uma resposta para uma mensagem
        
        Args:
            message: Mensagem a responder
            context: Informações de contexto
            tone: Tom da resposta (professional, friendly, etc.)
        
        Returns:
            str: Resposta gerada
        """
        pass
    
    @abstractmethod
    def classify_funnel_stage(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Classifica o estágio do cliente no funil de marketing com base no histórico de conversa
        
        Args:
            conversation_history: Histórico de mensagens trocadas
        
        Returns:
            str: Estágio do funil (attraction, relationship, conversion, etc.)
        """
        pass


class OpenAIInterface(BaseLLMInterface):
    """
    Interface para comunicação com API OpenAI
    """
    
    def __init__(
        self, 
        api_key: str = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        """
        Inicializa a interface OpenAI
        
        Args:
            api_key: Chave API da OpenAI (padrão: busca na variável OPENAI_API_KEY)
            model: Modelo a ser utilizado
            temperature: Temperatura para geração (0.0 a 1.0)
            max_retries: Número máximo de tentativas em caso de erro
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key não fornecida e não encontrada como variável de ambiente")
        
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Configura o cliente OpenAI
        openai.api_key = self.api_key
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((openai.error.ServiceUnavailableError, openai.error.APIError, openai.error.Timeout))
    )
    def complete_prompt(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Completa um prompt com a API OpenAI
        
        Args:
            prompt: Prompt para o LLM
            max_tokens: Número máximo de tokens na resposta
        
        Returns:
            str: Resposta do LLM
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except (openai.error.RateLimitError, openai.error.ServiceUnavailableError) as e:
            logger.warning(f"Erro temporário na API OpenAI: {e}")
            time.sleep(2)
            raise
        except Exception as e:
            logger.error(f"Erro ao completar prompt com OpenAI: {e}")
            return ""
    
    def analyze_message(
        self, 
        message: str, 
        sender: str = None, 
        contact_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analisa uma mensagem para extrair intenção e outras informações
        
        Args:
            message: Texto da mensagem
            sender: Identificador do remetente (opcional)
            contact_info: Informações adicionais sobre o contato (opcional)
        
        Returns:
            Dict: Resultado da análise
        """
        # Constrói o prompt para análise
        analysis_prompt = f"""
        Analise a seguinte mensagem enviada por WhatsApp e forneça:
        
        1. Intenção principal do remetente (greeting, question, interest, complaint, objection, request_info, ready_to_buy, appointment, thank_you, farewell, other)
        2. Sentimento geral (positive, negative, neutral)
        3. Estágio do funil de marketing (attraction, relationship, conversion, customer, unknown)
        4. Uma resposta sugerida para esta mensagem
        5. Próximas ações recomendadas
        
        Mensagem: "{message}"
        """
        
        # Adiciona informações de contexto se disponíveis
        if sender:
            analysis_prompt += f"\nRemetente: {sender}"
        
        if contact_info:
            analysis_prompt += "\nInformações do contato: " + json.dumps(contact_info, ensure_ascii=False)
        
        analysis_prompt += """
        
        Responda no formato JSON com as seguintes chaves:
        - intent: string (greeting, question, interest, etc.)
        - sentiment: string (positive, negative, neutral)
        - funnel_stage: string (attraction, relationship, conversion, customer, unknown)
        - suggested_response: string
        - next_actions: array de objetos com type e outros campos
        """
        
        # Realiza a chamada ao LLM
        raw_response = self.complete_prompt(analysis_prompt)
        
        # Tenta extrair o JSON da resposta
        try:
            # Limita a resposta para o bloco JSON
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.warning(f"Resposta não contém JSON válido: {raw_response}")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON da resposta: {e}")
            logger.debug(f"Resposta bruta: {raw_response}")
            return {}
    
    def generate_response(
        self, 
        message: str, 
        context: Dict[str, Any] = None, 
        tone: str = "professional"
    ) -> str:
        """
        Gera uma resposta para uma mensagem
        
        Args:
            message: Mensagem a responder
            context: Informações de contexto
            tone: Tom da resposta (professional, friendly, etc.)
        
        Returns:
            str: Resposta gerada
        """
        # Constrói o prompt para geração de resposta
        response_prompt = f"""
        Gere uma resposta para a seguinte mensagem recebida via WhatsApp.
        Use um tom {tone} e seja conciso, já que é uma resposta para WhatsApp.
        
        Mensagem recebida: "{message}"
        """
        
        # Adiciona contexto se disponível
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            response_prompt += f"\n\nContexto do cliente:\n{context_str}"
        
        return self.complete_prompt(response_prompt, max_tokens=300)
    
    def classify_funnel_stage(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        Classifica o estágio do cliente no funil de marketing com base no histórico de conversa
        
        Args:
            conversation_history: Histórico de mensagens trocadas
        
        Returns:
            str: Estágio do funil (attraction, relationship, conversion, etc.)
        """
        # Formata o histórico de conversa para o prompt
        conversation_text = ""
        for msg in conversation_history:
            role = "Cliente" if msg.get("direction") == "inbound" else "Empresa"
            text = msg.get("content", "")
            conversation_text += f"{role}: {text}\n"
        
        # Constrói o prompt para classificação
        classification_prompt = f"""
        Com base no histórico de conversa entre um cliente e nossa empresa por WhatsApp,
        classifique o estágio atual do cliente no funil de marketing.
        
        Histórico de conversa:
        {conversation_text}
        
        Estágios possíveis:
        - attraction: Cliente está apenas conhecendo a empresa/produto
        - relationship: Cliente já conhece e está interagindo, mas ainda não demonstrou intenção clara de compra
        - conversion: Cliente demonstrou intenção de compra ou está em processo de decisão
        - customer: Cliente já realizou uma compra
        - unknown: Não há informação suficiente para classificar
        
        Responda apenas com o nome do estágio.
        """
        
        response = self.complete_prompt(classification_prompt, max_tokens=50)
        
        # Normaliza a resposta para garantir que seja um dos valores válidos
        valid_stages = ["attraction", "relationship", "conversion", "customer", "unknown"]
        
        # Procura por um estágio válido na resposta
        for stage in valid_stages:
            if stage in response.lower():
                return stage
        
        # Se não encontrar um estágio válido, retorna unknown
        return "unknown"


class AzureOpenAIInterface(OpenAIInterface):
    """
    Interface para comunicação com API Azure OpenAI
    """
    
    def __init__(
        self, 
        api_key: str = None,
        endpoint: str = None,
        deployment_name: str = None,
        api_version: str = "2023-05-15",
        temperature: float = 0.7,
        max_retries: int = 3
    ):
        """
        Inicializa a interface Azure OpenAI
        
        Args:
            api_key: Chave API do Azure OpenAI (padrão: busca em AZURE_OPENAI_API_KEY)
            endpoint: Endpoint da API (padrão: busca em AZURE_OPENAI_ENDPOINT)
            deployment_name: Nome do deployment do modelo
            api_version: Versão da API
            temperature: Temperatura para geração (0.0 a 1.0)
            max_retries: Número máximo de tentativas em caso de erro
        """
        # Usa os valores padrão das variáveis de ambiente se não fornecidos
        self.api_key = api_key or os.environ.get("AZURE_OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Azure OpenAI API key não fornecida e não encontrada como variável de ambiente")
        
        self.endpoint = endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint não fornecido e não encontrado como variável de ambiente")
        
        self.deployment_name = deployment_name
        if not self.deployment_name:
            raise ValueError("Azure OpenAI deployment name é obrigatório")
        
        self.api_version = api_version
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Configura o cliente OpenAI para Azure
        openai.api_type = "azure"
        openai.api_key = self.api_key
        openai.api_base = self.endpoint
        openai.api_version = self.api_version
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((openai.error.ServiceUnavailableError, openai.error.APIError, openai.error.Timeout))
    )
    def complete_prompt(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Completa um prompt com a API Azure OpenAI
        
        Args:
            prompt: Prompt para o LLM
            max_tokens: Número máximo de tokens na resposta
        
        Returns:
            str: Resposta do LLM
        """
        try:
            response = openai.ChatCompletion.create(
                deployment_id=self.deployment_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=self.temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except (openai.error.RateLimitError, openai.error.ServiceUnavailableError) as e:
            logger.warning(f"Erro temporário na API Azure OpenAI: {e}")
            time.sleep(2)
            raise
        except Exception as e:
            logger.error(f"Erro ao completar prompt com Azure OpenAI: {e}")
            return ""


class MockLLMInterface(BaseLLMInterface):
    """
    Implementação simulada para uso em testes ou quando não há conexão com LLM
    """
    
    def __init__(self):
        """Inicializa a interface mock"""
        logger.warning("Usando interface LLM simulada (mock). Respostas serão genéricas.")
    
    def complete_prompt(self, prompt: str, max_tokens: int = 500) -> str:
        """Simula a completação de prompt"""
        return "Esta é uma resposta simulada do LLM. A integração real não está disponível."
    
    def analyze_message(
        self, 
        message: str, 
        sender: str = None, 
        contact_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simula a análise de mensagem"""
        return {
            "intent": "generic",
            "sentiment": "neutral",
            "topics": ["general"],
            "action_required": False,
            "priority": "medium"
        }
    
    def generate_response(
        self, 
        message: str, 
        context: Dict[str, Any] = None, 
        tone: str = "professional"
    ) -> str:
        """Simula a geração de resposta"""
        return "Obrigado pelo contato. Esta é uma resposta automática simulada."
    
    def classify_funnel_stage(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Simula a classificação de estágio no funil"""
        return "attraction"  # Retorna estágio inicial por padrão
    
    def evaluate_lead_score(self, profile: Dict[str, Any], interactions: List[Dict[str, Any]]) -> int:
        """Simula a avaliação de pontuação de lead"""
        return 50  # Pontuação média por padrão
    
    def generate_personalized_content(
        self,
        contact_info: Dict[str, Any],
        stage: str,
        template: str
    ) -> str:
        """Simula a geração de conteúdo personalizado"""
        return "Este é um conteúdo personalizado simulado para o seu perfil."


class LLMInterfaceFactory:
    """
    Factory para criação de interfaces LLM
    """
    
    @staticmethod
    def create_interface(provider: LLMProvider, config: Dict[str, Any] = None) -> BaseLLMInterface:
        """
        Cria uma interface para o provedor especificado
        
        Args:
            provider: Provedor de LLM
            config: Configurações específicas para o provedor
        
        Returns:
            BaseLLMInterface: Interface para o LLM
        
        Raises:
            ValueError: Se o provedor não for suportado
        """
        config = config or {}
        
        if provider == LLMProvider.OPENAI:
            return OpenAIInterface(
                api_key=config.get("api_key"),
                model=config.get("model", "gpt-4"),
                temperature=config.get("temperature", 0.7)
            )
        elif provider == LLMProvider.AZURE_OPENAI:
            return AzureOpenAIInterface(
                api_key=config.get("api_key"),
                endpoint=config.get("endpoint"),
                deployment_name=config.get("deployment_name"),
                api_version=config.get("api_version", "2023-05-15"),
                temperature=config.get("temperature", 0.7)
            )
        else:
            raise ValueError(f"Provedor LLM não suportado: {provider}")


@lru_cache()
def get_llm_interface() -> BaseLLMInterface:
    """
    Obtém uma instância da interface LLM com base nas configurações
    
    Returns:
        BaseLLMInterface: Instância da interface LLM configurada
    """
    try:
        # Importação tardia para evitar problemas de circularidade
        from ..api.config import get_settings
        
        settings = get_settings()
        provider = settings.llm_provider
        
        if provider.lower() == LLMProvider.OPENAI.value:
            return OpenAIInterface(
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                temperature=settings.llm_temperature
            )
        elif provider.lower() == LLMProvider.AZURE_OPENAI.value:
            return AzureOpenAIInterface(
                api_key=settings.llm_api_key,
                endpoint=settings.azure_endpoint,
                deployment_id=settings.azure_deployment_id,
                api_version=getattr(settings, "azure_api_version", "2023-05-15")
            )
        else:
            logger.warning(f"Provedor LLM não suportado: {provider}. Usando OpenAI como fallback.")
            return OpenAIInterface(
                api_key=settings.llm_api_key,
                model=settings.llm_model,
                temperature=settings.llm_temperature
            )
    except Exception as e:
        logger.error(f"Erro ao criar interface LLM: {e}")
        # Retorna interface mock em caso de erro
        return MockLLMInterface()


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo com OpenAI
    try:
        # Supondo que OPENAI_API_KEY está definido como variável de ambiente
        openai_interface = LLMInterfaceFactory.create_interface(
            LLMProvider.OPENAI,
            {"model": "gpt-3.5-turbo"}
        )
        
        # Exemplo de análise de mensagem
        message = "Olá, gostaria de conhecer mais sobre os serviços que vocês oferecem."
        analysis = openai_interface.analyze_message(message)
        
        print("Análise da mensagem:")
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
        
        # Exemplo de geração de resposta
        response = openai_interface.generate_response(
            message,
            context={"nome": "João", "interesses": "automação"}
        )
        
        print("\nResposta gerada:")
        print(response)
        
    except ValueError as e:
        print(f"Erro: {e}")
