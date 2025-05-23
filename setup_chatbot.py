"""
Script para configuração do ambiente WAHA para o chatbot WhatsApp

Este script prepara o ambiente necessário para o chatbot WhatsApp,
verificando e configurando o servidor WAHA através de Docker.
"""

import os
import sys
import subprocess
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import time
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("setup_chatbot")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações padrão
DEFAULT_WAHA_PORT = os.getenv("WAHA_PORT", "3000")
DEFAULT_WAHA_API_KEY = os.getenv("WAHA_API_KEY", "zf-portal-api-key")
DEFAULT_WAHA_SESSION = os.getenv("WAHA_SESSION", "zf-portal")
DEFAULT_WAHA_CONTAINER = os.getenv("WAHA_CONTAINER", "zf-portal-waha")
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "waha-data")


def check_docker_running() -> bool:
    """
    Verifica se o Docker está em execução
    
    Returns:
        bool: True se o Docker estiver em execução, False caso contrário
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Erro ao verificar Docker: {e}")
        return False


def check_waha_container(container_name: str) -> bool:
    """
    Verifica se o container WAHA existe
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container existir, False caso contrário
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            return False
        
        return container_name in result.stdout.strip().split('\n')
    except Exception as e:
        logger.error(f"Erro ao verificar container WAHA: {e}")
        return False


def run_setup_waha(port: str, api_key: str, session: str, container_name: str, data_dir: str) -> bool:
    """
    Executa o script setup_waha.py para configurar o servidor WAHA
    
    Args:
        port: Porta do servidor WAHA
        api_key: Chave API para autenticação
        session: Nome da sessão WhatsApp
        container_name: Nome do container Docker
        data_dir: Diretório para armazenar dados
        
    Returns:
        bool: True se a configuração foi bem-sucedida, False caso contrário
    """
    try:
        # Construir comando para executar setup_waha.py
        cmd = [
            sys.executable,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "setup_waha.py"),
            "--port", port,
            "--api-key", api_key,
            "--session-id", session,
            "--container-name", container_name,
            "--data-dir", data_dir
        ]
        
        # Executar comando
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            logger.error(f"Erro ao executar setup_waha.py: {result.stderr}")
            return False
        
        logger.info("Servidor WAHA configurado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao executar setup_waha.py: {e}")
        return False


def create_config_file(config: Dict[str, Any], config_file: str) -> bool:
    """
    Cria ou atualiza arquivo de configuração para o chatbot
    
    Args:
        config: Configuração a ser salva
        config_file: Caminho do arquivo de configuração
        
    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        # Garantir que o diretório exista
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Salvar configuração
        with open(config_file, 'w', encoding='utf-8') as file:
            json.dump(config, file, indent=4)
        
        logger.info(f"Arquivo de configuração criado: {config_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar arquivo de configuração: {e}")
        return False


def setup_chatbot_environment(waha_port: str, waha_api_key: str, waha_session: str, 
                            waha_container: str, data_dir: str) -> bool:
    """
    Configura o ambiente para o chatbot WhatsApp
    
    Args:
        waha_port: Porta do servidor WAHA
        waha_api_key: Chave API para autenticação
        waha_session: Nome da sessão WhatsApp
        waha_container: Nome do container Docker
        data_dir: Diretório para armazenar dados
        
    Returns:
        bool: True se a configuração foi bem-sucedida, False caso contrário
    """
    # Verificar se Docker está em execução
    if not check_docker_running():
        logger.error("Docker não está em execução. Inicie o Docker e tente novamente.")
        return False
    
    # Verificar se container WAHA já existe
    if check_waha_container(waha_container):
        logger.info(f"Container WAHA '{waha_container}' já existe")
    else:
        # Executar setup_waha.py para criar container
        if not run_setup_waha(waha_port, waha_api_key, waha_session, waha_container, data_dir):
            logger.error("Falha ao configurar servidor WAHA")
            return False
    
    # Criar arquivo de configuração para o chatbot
    config = {
        "waha_url": f"http://localhost:{waha_port}",
        "api_key": waha_api_key,
        "session": waha_session,
        "log_conversations": True,
        "save_contacts": True,
        "use_llm": False  # Será implementado no futuro
    }
    
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "chatbot", "config")
    config_file = os.path.join(config_dir, "chatbot_config.json")
    
    if not create_config_file(config, config_file):
        logger.warning("Falha ao criar arquivo de configuração")
    
    logger.info(f"""
    Ambiente para chatbot WhatsApp configurado com sucesso!
    
    Servidor WAHA:
    - URL: http://localhost:{waha_port}
    - API Key: {waha_api_key}
    - Sessão: {waha_session}
    - Container: {waha_container}
    
    Para iniciar o chatbot, execute:
    python run_chatbot.py
    
    Para obter o QR code para autenticação:
    python run_chatbot.py --show-qr
    """)
    
    return True


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Configurar ambiente para chatbot WhatsApp')
    
    parser.add_argument('--waha-port', type=str, default=DEFAULT_WAHA_PORT,
                        help=f'Porta do servidor WAHA (padrão: {DEFAULT_WAHA_PORT})')
    parser.add_argument('--waha-api-key', type=str, default=DEFAULT_WAHA_API_KEY,
                        help=f'Chave API para autenticação (padrão: {DEFAULT_WAHA_API_KEY})')
    parser.add_argument('--waha-session', type=str, default=DEFAULT_WAHA_SESSION,
                        help=f'Nome da sessão WhatsApp (padrão: {DEFAULT_WAHA_SESSION})')
    parser.add_argument('--waha-container', type=str, default=DEFAULT_WAHA_CONTAINER,
                        help=f'Nome do container Docker (padrão: {DEFAULT_WAHA_CONTAINER})')
    parser.add_argument('--data-dir', type=str, default=DEFAULT_DATA_DIR,
                        help=f'Diretório para armazenar dados (padrão: {DEFAULT_DATA_DIR})')
    
    args = parser.parse_args()
    
    # Configurar ambiente
    setup_chatbot_environment(
        args.waha_port,
        args.waha_api_key,
        args.waha_session,
        args.waha_container,
        args.data_dir
    )


if __name__ == "__main__":
    main()
