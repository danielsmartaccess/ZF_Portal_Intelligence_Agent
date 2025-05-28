#!/usr/bin/env python
"""
Script para iniciar o chatbot WhatsApp

Este script configura e inicia o chatbot para WhatsApp utilizando
o servidor WAHA (WhatsApp HTTP API).
"""

import os
import sys
import time
import logging
import argparse
from dotenv import load_dotenv
import signal
import json

# Adicionar diretório raiz ao path para imports relativos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.chatbot.chatbot_service import ChatbotService
from src.chatbot.chatbot_adapter import ChatbotSystemAdapter

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_chatbot")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações padrão
DEFAULT_WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
DEFAULT_API_KEY = os.getenv("WAHA_API_KEY", "zf-portal-api-key")
DEFAULT_SESSION = os.getenv("WAHA_SESSION", "default")


def show_qr_code(qr_code: str):
    """
    Exibe o QR code no terminal para autenticação
    
    Args:
        qr_code: String do QR code
    """
    print("\nEscaneie o QR code abaixo com seu WhatsApp para autenticar:")
    print(qr_code)
    print("\nAguardando autenticação...")


def load_chatbot_config() -> dict:
    """
    Carrega configurações do chatbot a partir do arquivo de configuração ou .env
    
    Returns:
        dict: Configurações do chatbot
    """
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              "src", "chatbot", "config", "chatbot_config.json")
    
    config = {
        "waha_url": os.getenv("WAHA_URL", DEFAULT_WAHA_URL),
        "api_key": os.getenv("WAHA_API_KEY", DEFAULT_API_KEY),
        "session": os.getenv("WAHA_SESSION", DEFAULT_SESSION),
        "log_conversations": True,
        "save_contacts": True,
        "use_llm": False
    }
    
    # Tentar carregar do arquivo de configuração
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as file:
                file_config = json.load(file)
                config.update(file_config)
        except Exception as e:
            logger.warning(f"Erro ao carregar arquivo de configuração: {e}")
    
    return config

def setup_chatbot(waha_url: str, api_key: str, session: str) -> ChatbotService:
    """
    Configura o serviço de chatbot
    
    Args:
        waha_url: URL do servidor WAHA
        api_key: Chave API para autenticação
        session: Nome da sessão WhatsApp
        
    Returns:
        ChatbotService: Instância do serviço de chatbot
    """
    # Inicializar adaptador de sistema
    system_adapter = ChatbotSystemAdapter()
    
    # Inicializar serviço de chatbot
    chatbot = ChatbotService(waha_url, api_key, session)
    
    # Iniciar serviço
    chatbot.start()
    
    # Verificar se está conectado
    if not chatbot._check_session_connected():
        # Obter QR code
        qr_code = chatbot.get_qr_code()
        if qr_code:
            show_qr_code(qr_code)
            
            # Aguardar autenticação
            while not chatbot._check_session_connected():
                print(".", end="", flush=True)
                time.sleep(2)
            
            print("\nSessão WhatsApp conectada com sucesso!")
        else:
            logger.error("Não foi possível obter o QR code. Verifique o servidor WAHA.")
            sys.exit(1)
    else:
        logger.info("Sessão WhatsApp já está conectada")
    
    return chatbot


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Iniciar o chatbot WhatsApp')
    
    parser.add_argument('--waha-url', type=str, default=DEFAULT_WAHA_URL,
                        help=f'URL do servidor WAHA (padrão: {DEFAULT_WAHA_URL})')
    parser.add_argument('--api-key', type=str, default=DEFAULT_API_KEY,
                        help=f'Chave API para autenticação (padrão: {DEFAULT_API_KEY})')
    parser.add_argument('--session', type=str, default=DEFAULT_SESSION,
                        help=f'Nome da sessão WhatsApp (padrão: {DEFAULT_SESSION})')
    parser.add_argument('--show-qr', action='store_true',
                        help='Apenas exibir QR code para autenticação e sair')
    
    args = parser.parse_args()
    
    # Carregar configuração
    config = load_chatbot_config()
    
    # Usar argumentos da linha de comando se fornecidos
    waha_url = args.waha_url or config.get("waha_url", DEFAULT_WAHA_URL)
    api_key = args.api_key or config.get("api_key", DEFAULT_API_KEY)
    session = args.session or config.get("session", DEFAULT_SESSION)
    
    # Verificar se o servidor WAHA está configurado
    logger.info("Verificando configuração do servidor WAHA...")
    
    # Configurar o chatbot
    chatbot = setup_chatbot(waha_url, api_key, session)
    
    # Se apenas queremos exibir o QR code
    if args.show_qr:
        qr_code = chatbot.get_qr_code()
        if qr_code:
            show_qr_code(qr_code)
        else:
            logger.info("Sessão já está autenticada ou QR code não disponível")
        sys.exit(0)
    
    # Configurar handler de sinal para encerramento gracioso
    def signal_handler(sig, frame):
        logger.info("Encerrando chatbot graciosamente...")
        chatbot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Mensagem de início
    logger.info(f"""
    Chatbot iniciado com sucesso!
    
    Status: {'Conectado' if chatbot.is_connected else 'Não conectado'}
    URL WAHA: {args.waha_url}
    Sessão: {args.session}
    
    Pressione Ctrl+C para encerrar.
    """)
    
    # Manter aplicação rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        chatbot.stop()
        logger.info("Chatbot encerrado pelo usuário")
    except Exception as e:
        logger.error(f"Erro no chatbot: {e}")
        chatbot.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
