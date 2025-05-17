"""
Módulo para classificação e gerenciamento de leads no funil de marketing

Este módulo implementa a classificação de leads em estágios do funil
de marketing e o gerenciamento de interações em cada estágio.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum

from ..llm import BaseLLMInterface
from ..templates import TemplatesManager, FunnelTemplatesManager
from ..whatsapp import WhatsAppConnector

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("funnel_manager")


class FunnelStage(Enum):
    """Estágios do funil de marketing"""
    UNKNOWN = "unknown"
    ATTRACTION = "attraction"  # Atração
    RELATIONSHIP = "relationship"  # Relacionamento
    CONVERSION = "conversion"  # Conversão
    CUSTOMER = "customer"  # Cliente


class LeadScore(Enum):
    """Pontuação de qualificação de leads"""
    COLD = "cold"  # Frio (0-20)
    WARM = "warm"  # Morno (21-50)
    HOT = "hot"    # Quente (51-80)
    SALES_READY = "sales_ready"  # Pronto para vendas (81-100)


class LeadClassifier:
    """
    Classe para classificação de leads com base em interações
    """
    
    def __init__(self, llm_interface: Optional[BaseLLMInterface] = None):
        """
        Inicializa o classificador de leads
        
        Args:
            llm_interface: Interface para o modelo de linguagem (opcional)
        """
        self.llm_interface = llm_interface
    
    def classify_lead(
        self, 
        interactions: List[Dict[str, Any]],
        profile_data: Dict[str, Any] = None
    ) -> Tuple[FunnelStage, int]:
        """
        Classifica um lead com base em suas interações e perfil
        
        Args:
            interactions: Lista de interações com o lead
            profile_data: Dados do perfil do lead (opcional)
        
        Returns:
            Tuple[FunnelStage, int]: Estágio do funil e pontuação (0-100)
        """
        # Se não houver interações, retorna estágio desconhecido
        if not interactions:
            return FunnelStage.UNKNOWN, 0
        
        # Pontuação inicial com base no perfil
        initial_score = self._score_profile(profile_data) if profile_data else 0
        
        # Análise de interações sem LLM
        if not self.llm_interface:
            stage, score = self._classify_without_llm(interactions, initial_score)
            return stage, min(100, max(0, score))  # Garante que score está entre 0-100
        
        # Análise com LLM
        stage, score = self._classify_with_llm(interactions, profile_data, initial_score)
        return stage, min(100, max(0, score))  # Garante que score está entre 0-100
    
    def _score_profile(self, profile_data: Dict[str, Any]) -> int:
        """
        Calcula pontuação inicial com base no perfil
        
        Args:
            profile_data: Dados do perfil do lead
        
        Returns:
            int: Pontuação inicial (0-20)
        """
        score = 0
        
        # Pontuação com base em campos preenchidos
        if profile_data.get("email"):
            score += 5
        if profile_data.get("phone") or profile_data.get("whatsapp_number"):
            score += 5
        if profile_data.get("company"):
            score += 3
        if profile_data.get("position"):
            score += 2
        if profile_data.get("industry"):
            score += 2
        if profile_data.get("website"):
            score += 1
        if profile_data.get("linkedin_url"):
            score += 2
        
        return min(score, 20)  # Máximo de 20 pontos pelo perfil
    
    def _classify_without_llm(
        self,
        interactions: List[Dict[str, Any]],
        initial_score: int = 0
    ) -> Tuple[FunnelStage, int]:
        """
        Classifica lead sem usar LLM, baseado em heurísticas
        
        Args:
            interactions: Lista de interações com o lead
            initial_score: Pontuação inicial
        
        Returns:
            Tuple[FunnelStage, int]: Estágio do funil e pontuação
        """
        score = initial_score
        
        # Contadores para análise
        message_count = 0
        response_count = 0
        meetings_scheduled = 0
        days_since_first = None
        days_since_last = None
        has_pricing_question = False
        has_demo_request = False
        has_purchase_intent = False
        
        # Data atual para cálculos de tempo
        now = datetime.now()
        
        # Analisa cada interação
        first_date = None
        last_date = None
        
        for interaction in interactions:
            # Extrai data da interação
            interaction_date = interaction.get("date")
            if isinstance(interaction_date, str):
                try:
                    interaction_date = datetime.fromisoformat(interaction_date)
                except ValueError:
                    interaction_date = None
            
            # Atualiza datas para cálculos
            if interaction_date:
                if first_date is None or interaction_date < first_date:
                    first_date = interaction_date
                if last_date is None or interaction_date > last_date:
                    last_date = interaction_date
            
            # Contagem por tipo de interação
            interaction_type = interaction.get("type", "").lower()
            
            if interaction_type == "message":
                message_count += 1
                
                # Analisa conteúdo da mensagem (heurística simples)
                content = interaction.get("content", "").lower()
                if "preço" in content or "valor" in content or "custo" in content:
                    has_pricing_question = True
                if "demo" in content or "demonstração" in content:
                    has_demo_request = True
                if "comprar" in content or "contratar" in content or "assinar" in content:
                    has_purchase_intent = True
                
            elif interaction_type == "response":
                response_count += 1
            elif interaction_type == "meeting":
                meetings_scheduled += 1
        
        # Cálculo de tempo desde a primeira e última interação
        if first_date:
            days_since_first = (now - first_date).days
        if last_date:
            days_since_last = (now - last_date).days
        
        # Pontuação baseada em interações (máx: 80 pontos)
        score += min(message_count * 3, 15)  # Máx: 15 pontos
        score += min(response_count * 2, 10)  # Máx: 10 pontos
        score += min(meetings_scheduled * 10, 20)  # Máx: 20 pontos
        
        # Pontuação por indicadores de interesse
        if has_pricing_question:
            score += 10
        if has_demo_request:
            score += 15
        if has_purchase_intent:
            score += 20
        
        # Redução de pontuação por inatividade
        if days_since_last and days_since_last > 30:
            score -= min(days_since_last // 10, 20)  # Máx: -20 pontos
        
        # Determinação do estágio com base na pontuação
        if score >= 80:
            return FunnelStage.CONVERSION, score
        elif score >= 40:
            return FunnelStage.RELATIONSHIP, score
        elif score >= 10:
            return FunnelStage.ATTRACTION, score
        else:
            return FunnelStage.UNKNOWN, score
    
    def _classify_with_llm(
        self,
        interactions: List[Dict[str, Any]],
        profile_data: Dict[str, Any] = None,
        initial_score: int = 0
    ) -> Tuple[FunnelStage, int]:
        """
        Classifica lead usando LLM para análise semântica
        
        Args:
            interactions: Lista de interações com o lead
            profile_data: Dados do perfil do lead
            initial_score: Pontuação inicial
        
        Returns:
            Tuple[FunnelStage, int]: Estágio do funil e pontuação
        """
        if not self.llm_interface:
            return self._classify_without_llm(interactions, initial_score)
        
        try:
            # Prepara os dados para enviar ao LLM
            prompt_data = {
                "profile": profile_data or {},
                "interactions": interactions
            }
            
            # Constrói o prompt para o LLM
            prompt = f"""
            Analise o perfil e interações do lead a seguir para classificá-lo no funil de marketing
            e atribuir uma pontuação de qualificação (0-100).
            
            Dados do lead:
            {json.dumps(prompt_data, indent=2, ensure_ascii=False)}
            
            Classifique o estágio do funil:
            - UNKNOWN: Não há informações suficientes
            - ATTRACTION: Lead conheceu a empresa recentemente e está no início do relacionamento
            - RELATIONSHIP: Lead já interage com a empresa e demonstra algum interesse
            - CONVERSION: Lead demonstra forte interesse e intenção de compra
            - CUSTOMER: Lead já realizou uma compra
            
            Retorne apenas um JSON com as seguintes chaves:
            - stage: Estágio do funil (UNKNOWN, ATTRACTION, RELATIONSHIP, CONVERSION, CUSTOMER)
            - score: Pontuação de 0 a 100
            - reasoning: Breve explicação da classificação
            """
            
            # Consulta o LLM
            response = self.llm_interface.complete_prompt(prompt)
            
            # Extrai o JSON da resposta
            try:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                    
                    # Extrai os valores
                    stage_str = result.get("stage", "UNKNOWN")
                    score = result.get("score", initial_score)
                    
                    # Converte para enum
                    try:
                        stage = FunnelStage[stage_str]
                    except (KeyError, ValueError):
                        stage = FunnelStage.UNKNOWN
                    
                    return stage, score
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Erro ao processar resposta do LLM: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao classificar lead com LLM: {e}")
        
        # Em caso de falha, usa o método sem LLM
        return self._classify_without_llm(interactions, initial_score)


class FunnelManager:
    """
    Gerenciador do funil de marketing
    """
    
    def __init__(
        self,
        db_interface,
        whatsapp_connector: Optional[WhatsAppConnector] = None,
        llm_interface: Optional[BaseLLMInterface] = None,
        templates_manager: Optional[TemplatesManager] = None
    ):
        """
        Inicializa o gerenciador de funil
        
        Args:
            db_interface: Interface para o banco de dados
            whatsapp_connector: Conector WhatsApp (opcional)
            llm_interface: Interface para o modelo de linguagem (opcional)
            templates_manager: Gerenciador de templates (opcional)
        """
        self.db_interface = db_interface
        self.whatsapp_connector = whatsapp_connector
        self.llm_interface = llm_interface
        
        # Inicializa gerenciadores auxiliares
        self.templates_manager = templates_manager
        if templates_manager:
            self.funnel_templates = FunnelTemplatesManager(templates_manager)
        else:
            self.funnel_templates = None
        
        # Inicializa o classificador de leads
        self.lead_classifier = LeadClassifier(llm_interface)
    
    def classify_lead(self, lead_id: Union[str, int]) -> Tuple[FunnelStage, int]:
        """
        Classifica um lead no funil de marketing
        
        Args:
            lead_id: ID do lead
        
        Returns:
            Tuple[FunnelStage, int]: Estágio do funil e pontuação
        """
        # Obtém dados do lead
        lead_data = self.db_interface.get_lead(lead_id)
        if not lead_data:
            return FunnelStage.UNKNOWN, 0
        
        # Obtém interações do lead
        interactions = self.db_interface.get_lead_interactions(lead_id)
        
        # Classifica o lead
        stage, score = self.lead_classifier.classify_lead(interactions, lead_data)
        
        # Atualiza o estágio e pontuação no banco de dados
        self.db_interface.update_lead_funnel_stage(lead_id, stage.value, score)
        
        return stage, score
    
    def send_stage_message(
        self, 
        lead_id: Union[str, int],
        stage: FunnelStage = None,
        template_index: int = 0,
        params: Dict[str, Any] = None
    ) -> bool:
        """
        Envia mensagem apropriada para o estágio do lead no funil
        
        Args:
            lead_id: ID do lead
            stage: Estágio do funil (se None, usa a classificação atual)
            template_index: Índice do template a utilizar
            params: Parâmetros adicionais para o template
        
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        if not self.whatsapp_connector or not self.funnel_templates:
            logger.error("WhatsApp connector ou gerenciador de templates não configurado")
            return False
        
        # Obtém dados do lead
        lead_data = self.db_interface.get_lead(lead_id)
        if not lead_data:
            logger.error(f"Lead não encontrado: {lead_id}")
            return False
        
        # Obtém número de WhatsApp
        whatsapp_number = lead_data.get("whatsapp_number")
        if not whatsapp_number:
            logger.error(f"Lead {lead_id} não possui número de WhatsApp")
            return False
        
        # Se não foi especificado um estágio, classifica o lead
        if stage is None:
            stage, _ = self.classify_lead(lead_id)
        
        # Prepara parâmetros para o template
        template_params = {
            "nome": lead_data.get("nome", ""),
            "empresa": lead_data.get("empresa", ""),
            "cargo": lead_data.get("cargo", "")
        }
        
        # Adiciona parâmetros adicionais
        if params:
            template_params.update(params)
        
        # Obtém o template para o estágio
        message_text = self.funnel_templates.get_template_for_stage(
            stage.value,
            template_index,
            template_params
        )
        
        if not message_text:
            logger.error(f"Template não disponível para estágio {stage.value} (índice {template_index})")
            return False
        
        # Envia a mensagem
        try:
            result = self.whatsapp_connector.send_text_message(whatsapp_number, message_text)
            
            # Registra a interação
            self.db_interface.create_interaction(
                lead_id=lead_id,
                type="whatsapp_message",
                direction="outbound",
                content=message_text,
                metadata={
                    "funnel_stage": stage.value,
                    "template_index": template_index,
                    "message_id": result.get("id", "")
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para lead {lead_id}: {e}")
            return False
    
    def process_leads_by_stage(self, stage: FunnelStage, max_leads: int = 50) -> int:
        """
        Processa leads em um estágio específico do funil
        
        Args:
            stage: Estágio do funil a processar
            max_leads: Número máximo de leads a processar
        
        Returns:
            int: Número de leads processados
        """
        # Obtém leads no estágio especificado
        leads = self.db_interface.get_leads_by_stage(stage.value, limit=max_leads)
        
        processed_count = 0
        for lead in leads:
            lead_id = lead.get("id")
            
            # Verifica última interação
            last_interaction = self.db_interface.get_last_interaction(lead_id)
            
            # Calcula tempo desde última interação
            should_interact = False
            if not last_interaction:
                # Nenhuma interação anterior, deve interagir
                should_interact = True
            else:
                # Verifica tempo desde última interação com base no estágio
                last_date = last_interaction.get("date")
                if isinstance(last_date, str):
                    try:
                        last_date = datetime.fromisoformat(last_date)
                    except ValueError:
                        last_date = datetime.now() - timedelta(days=30)  # Fallback
                
                days_since = (datetime.now() - last_date).days
                
                # Define intervalos de contato por estágio
                if stage == FunnelStage.ATTRACTION and days_since >= 7:
                    should_interact = True
                elif stage == FunnelStage.RELATIONSHIP and days_since >= 5:
                    should_interact = True
                elif stage == FunnelStage.CONVERSION and days_since >= 3:
                    should_interact = True
            
            # Se deve interagir, envia mensagem apropriada
            if should_interact:
                # Obtém índice de template apropriado
                interactions_count = self.db_interface.count_lead_interactions(lead_id)
                template_index = min(interactions_count // 2, 1)  # Alterna entre templates 0 e 1
                
                if self.send_stage_message(lead_id, stage, template_index):
                    processed_count += 1
        
        return processed_count
    
    def process_all_leads(self, max_per_stage: int = 20) -> Dict[str, int]:
        """
        Processa leads em todos os estágios do funil
        
        Args:
            max_per_stage: Número máximo de leads a processar por estágio
        
        Returns:
            Dict[str, int]: Contagem de leads processados por estágio
        """
        results = {}
        
        # Processa leads em cada estágio
        for stage in FunnelStage:
            if stage == FunnelStage.UNKNOWN:
                continue  # Pula leads não classificados
                
            processed = self.process_leads_by_stage(stage, max_per_stage)
            results[stage.value] = processed
        
        return results
    
    def classify_all_leads(self, max_leads: int = 100) -> int:
        """
        Classifica todos os leads não classificados ou que precisam de reclassificação
        
        Args:
            max_leads: Número máximo de leads a classificar
        
        Returns:
            int: Número de leads classificados
        """
        # Obtém leads que precisam de classificação
        leads = self.db_interface.get_leads_for_classification(limit=max_leads)
        
        classified_count = 0
        for lead in leads:
            lead_id = lead.get("id")
            self.classify_lead(lead_id)
            classified_count += 1
        
        return classified_count
    
    def get_lead_status(self, lead_id: Union[str, int]) -> Dict[str, Any]:
        """
        Obtém o status completo de um lead
        
        Args:
            lead_id: ID do lead
        
        Returns:
            Dict: Status completo do lead
        """
        # Obtém dados do lead
        lead_data = self.db_interface.get_lead(lead_id)
        if not lead_data:
            return {}
        
        # Obtém estágio atual e pontuação
        stage = lead_data.get("funnel_stage", FunnelStage.UNKNOWN.value)
        score = lead_data.get("lead_score", 0)
        
        # Determina qualificação com base na pontuação
        qualification = LeadScore.COLD.value
        if score >= 80:
            qualification = LeadScore.SALES_READY.value
        elif score >= 50:
            qualification = LeadScore.HOT.value
        elif score >= 20:
            qualification = LeadScore.WARM.value
        
        # Calcula tempo no funil
        days_in_funnel = 0
        first_interaction = self.db_interface.get_first_interaction(lead_id)
        if first_interaction:
            first_date = first_interaction.get("date")
            if isinstance(first_date, str):
                try:
                    first_date = datetime.fromisoformat(first_date)
                    days_in_funnel = (datetime.now() - first_date).days
                except ValueError:
                    pass
        
        # Obtém quantidade de interações
        interactions_count = self.db_interface.count_lead_interactions(lead_id)
        
        # Retorna o status completo
        return {
            "lead_id": lead_id,
            "name": lead_data.get("nome", ""),
            "funnel_stage": stage,
            "lead_score": score,
            "qualification": qualification,
            "days_in_funnel": days_in_funnel,
            "interactions_count": interactions_count,
            "last_contact": lead_data.get("last_contact")
        }


# Exemplo de uso
if __name__ == "__main__":
    # Mock de interface de banco de dados para teste
    class MockDBInterface:
        def get_lead(self, lead_id):
            return {
                "id": lead_id,
                "nome": "João Silva",
                "empresa": "Acme Inc.",
                "cargo": "Gerente",
                "whatsapp_number": "5511999998888",
                "funnel_stage": "attraction",
                "lead_score": 25
            }
        
        def get_lead_interactions(self, lead_id):
            return [
                {
                    "id": 1,
                    "type": "message",
                    "direction": "inbound",
                    "content": "Olá, gostaria de saber mais sobre o serviço de vocês",
                    "date": (datetime.now() - timedelta(days=5)).isoformat()
                },
                {
                    "id": 2,
                    "type": "response",
                    "direction": "outbound",
                    "content": "Olá! Claro, vou te enviar mais informações.",
                    "date": (datetime.now() - timedelta(days=5)).isoformat()
                }
            ]
        
        def update_lead_funnel_stage(self, lead_id, stage, score):
            print(f"Lead {lead_id} atualizado: estágio={stage}, pontuação={score}")
        
        def get_leads_by_stage(self, stage, limit=50):
            return [{"id": 123, "nome": "João Silva"}]
        
        def get_last_interaction(self, lead_id):
            return {
                "id": 2,
                "type": "response",
                "direction": "outbound",
                "content": "Olá! Claro, vou te enviar mais informações.",
                "date": (datetime.now() - timedelta(days=5)).isoformat()
            }
        
        def count_lead_interactions(self, lead_id):
            return 2
        
        def create_interaction(self, lead_id, type, direction, content, metadata=None):
            print(f"Interação criada para lead {lead_id}: {type}, {direction}")
        
        def get_leads_for_classification(self, limit=100):
            return [{"id": 123}]
        
        def get_first_interaction(self, lead_id):
            return {
                "id": 1,
                "type": "message",
                "direction": "inbound",
                "content": "Olá, gostaria de saber mais sobre o serviço de vocês",
                "date": (datetime.now() - timedelta(days=10)).isoformat()
            }
    
    # Inicialização do gerenciador de funil para teste
    db = MockDBInterface()
    funnel_manager = FunnelManager(db)
    
    # Teste de classificação de lead
    lead_id = 123
    stage, score = funnel_manager.classify_lead(lead_id)
    
    print(f"Lead {lead_id} classificado como {stage.value} com pontuação {score}")
    
    # Teste de obtenção de status
    status = funnel_manager.get_lead_status(lead_id)
    print(f"Status do lead: {status}")
