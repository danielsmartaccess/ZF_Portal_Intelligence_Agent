#!/usr/bin/env python
"""
Script de debug para identificar problemas com a sessão do ChatbotService
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("debug_chatbot")

# Adicionar diretório raiz ao path para imports relativos
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Carregar variáveis de ambiente
load_dotenv()

# Importar os módulos necessários
from src.chatbot.chatbot_service import ChatbotService
from src.whatsapp.whatsapp_connector import WhatsAppConnector

def debug_session():
    """Executar debug da sessão do chatbot"""
    try:
        # Criar instância do serviço
        service = ChatbotService()
        print(f"\nChatbotService configurado:")
        print(f"  - URL WAHA: {service.waha_url}")
        print(f"  - API Key: {service.api_key}")
        print(f"  - Nome da sessão: {service.session_name}")
        
        # Verificar a configuração do conector
        connector = service.connector
        print(f"\nWhatsAppConnector do ChatbotService:")
        print(f"  - URL base: {connector.base_url}")
        print(f"  - API Key: {connector.api_key}")
        print(f"  - Nome da sessão: {connector.session_name}")
        
        # Criar uma instância separada do conector para comparar
        direct_connector = WhatsAppConnector("http://localhost:3000", "zf-portal-api-key")
        print(f"\nWhatsAppConnector criado diretamente:")
        print(f"  - URL base: {direct_connector.base_url}")
        print(f"  - API Key: {direct_connector.api_key}")
        print(f"  - Nome da sessão: {direct_connector.session_name}")
        
        # Tentar iniciar sessão e capturar erro
        print("\nTentando iniciar sessão com ChatbotService...")
        try:
            result = service.start()
            print(f"Resultado: {result}")
        except Exception as e:
            print(f"Erro ao iniciar sessão: {e}")
        
        print("\nVerificando URL dos endpoints utilizados:")
        # Monitorar qual endpoint está sendo chamado
        endpoint = f"api/sessions/{service.session_name}/start"
        url = f"{service.waha_url}/{endpoint.lstrip('/')}"
        print(f"URL para iniciar sessão: {url}")
        
        # Verificar status da sessão
        endpoint = f"api/sessions/{service.session_name}/status"
        url = f"{service.waha_url}/{endpoint.lstrip('/')}"
        print(f"URL para verificar status: {url}")
        
    except Exception as e:
        print(f"Erro durante debug: {e}")

if __name__ == "__main__":
    debug_session()
