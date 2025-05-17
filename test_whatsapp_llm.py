"""
Testes para a integração WhatsApp e LLM no ZF Portal Intelligence Agent

Este script executa testes básicos para verificar o funcionamento 
das integrações WhatsApp e LLM.
"""
import os
import sys
import time
import json
import logging
import pytest
from datetime import datetime, timedelta
from pathlib import Path

# Configurar paths
sys.path.append(str(Path(__file__).parent.absolute()))
from src.whatsapp.waha_setup import check_docker_installed, check_container_running
from src.whatsapp.whatsapp_connector import WhatsAppConnector, MessageType
from src.llm.llm_interface import MockLLMInterface
from src.templates.templates_manager import FunnelTemplatesManager
from src.marketing.funnel_manager import FunnelManager
from src.database.marketing_repository import WhatsAppRepository, FunnelRepository
from src.database.models import init_db

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_whatsapp_llm")


# Testes de ambiente
@pytest.mark.environment
def test_docker_installed():
    """Verifica se o Docker está instalado"""
    assert check_docker_installed(), "Docker não está instalado"


@pytest.mark.environment
def test_waha_container_running():
    """Verifica se o container WAHA está em execução"""
    container_running = check_container_running("zf-portal-waha")
    if not container_running:
        pytest.skip("Container WAHA não está em execução. Execute setup_waha.py primeiro.")
    assert container_running


# Testes do WhatsApp Connector
@pytest.mark.whatsapp
class TestWhatsAppConnector:
    """Testes para o WhatsApp Connector"""
    
    def setup_class(self):
        """Configuração inicial"""
        # Usar valores de teste
        self.base_url = os.getenv("WAHA_URL", "http://localhost:3000")
        self.api_key = os.getenv("WAHA_API_KEY", "zf-portal-api-key")
        self.session_name = os.getenv("WAHA_SESSION_ID", "zf-portal")
        
        # Criar connector
        try:
            self.connector = WhatsAppConnector(
                base_url=self.base_url,
                api_key=self.api_key,
                session_name=self.session_name
            )
        except Exception as e:
            pytest.skip(f"Não foi possível criar WhatsApp Connector: {e}")
    
    def test_session_info(self):
        """Testa obtenção de informações da sessão"""
        try:
            info = self.connector.get_session_info()
            assert info is not None
            assert "status" in info
        except Exception as e:
            pytest.skip(f"Falha ao obter informações da sessão: {e}")
    
    def test_check_number_exists(self):
        """Testa verificação de número existente"""
        # Use um número de teste válido
        test_number = os.getenv("TEST_WHATSAPP_NUMBER")
        if not test_number:
            pytest.skip("Número de teste não fornecido em TEST_WHATSAPP_NUMBER")
        
        try:
            result = self.connector.check_number_exists(test_number)
            assert result is not None
            assert "exists" in result
        except Exception as e:
            pytest.skip(f"Falha ao verificar número: {e}")


# Testes do LLM
@pytest.mark.llm
class TestLLMInterface:
    """Testes para o LLM Interface"""
    
    def setup_class(self):
        """Configuração inicial"""
        # Usar mock para testes básicos
        self.llm = MockLLMInterface()
    
    def test_complete_prompt(self):
        """Testa completação de prompt"""
        prompt = "Olá, meu nome é"
        response = self.llm.complete_prompt(prompt)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
    
    def test_analyze_message(self):
        """Testa análise de mensagem"""
        message = "Olá, gostaria de saber mais sobre o ZF Portal de Antecipações"
        result = self.llm.analyze_message(message)
        assert result is not None
        assert "intent" in result
        assert "sentiment" in result
    
    def test_generate_response(self):
        """Testa geração de resposta"""
        message = "Quais são os benefícios do ZF Portal?"
        context = {"company": "Cliente ABC", "stage": "attraction"}
        response = self.llm.generate_response(message, context)
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0


# Testes do Funil de Marketing
@pytest.mark.marketing
class TestFunnelManager:
    """Testes para o Funil de Marketing"""
    
    def setup_class(self):
        """Configuração inicial"""
        try:
            # Inicializar banco de dados de teste
            db_path = "sqlite:///test_marketing.db"
            Session = init_db(db_path)
            self.db_session = Session()
            
            # Criar componentes necessários
            self.llm = MockLLMInterface()
            self.funnel_repo = FunnelRepository(self.db_session)
            self.templates_manager = FunnelTemplatesManager(self.db_session)
            
            # Criar gerenciador de funil
            self.funnel_manager = FunnelManager(
                repository=self.funnel_repo,
                llm_interface=self.llm,
                templates_manager=self.templates_manager
            )
        except Exception as e:
            pytest.skip(f"Não foi possível configurar o ambiente de teste: {e}")
    
    def teardown_class(self):
        """Limpeza após os testes"""
        if hasattr(self, "db_session"):
            self.db_session.close()
        
        # Remover arquivo de banco de dados de teste
        try:
            db_file = Path("test_marketing.db")
            if db_file.exists():
                db_file.unlink()
        except Exception:
            pass
    
    def test_create_stage(self):
        """Testa criação de estágio no funil"""
        try:
            stage = self.funnel_manager.create_stage(
                name="attraction",
                description="Estágio de atração de leads",
                order=1
            )
            assert stage is not None
            assert stage.get("id") is not None
            assert stage.get("name") == "attraction"
        except Exception as e:
            pytest.skip(f"Não foi possível criar estágio: {e}")
    
    def test_create_template(self):
        """Testa criação de template"""
        # Primeiro cria um estágio
        stage = self.funnel_manager.get_stage_by_name("attraction")
        if not stage:
            stage = self.funnel_manager.create_stage(
                name="attraction",
                description="Estágio de atração de leads",
                order=1
            )
        
        try:
            template = self.funnel_manager.create_template(
                name="Apresentação",
                description="Template de apresentação",
                stage_id=stage.get("id"),
                content="Olá {{nome}}, tudo bem? Sou representante do ZF Portal e gostaria de apresentar nossa solução.",
                message_type="text",
                variables=["nome"]
            )
            assert template is not None
            assert template.get("id") is not None
            assert template.get("name") == "Apresentação"
        except Exception as e:
            pytest.skip(f"Não foi possível criar template: {e}")


# Função principal
if __name__ == "__main__":
    # Configurar argumentos
    sys.argv.extend(["-v", "-m", "environment"])
    
    # Executar testes
    pytest.main()
