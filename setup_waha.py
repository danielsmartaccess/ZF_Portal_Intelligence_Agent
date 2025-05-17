#!/usr/bin/env python
"""
Script para configuração e inicialização do servidor WAHA (WhatsApp Web API)

Este script gerencia a configuração e inicialização do servidor WAHA usando Docker.
O servidor WAHA é necessário para a comunicação com o WhatsApp Web.
"""

import os
import sys
import time
import json
import logging
import subprocess
import argparse
from typing import Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waha_setup")

# Configurações padrão
DEFAULT_PORT = 3000
DEFAULT_API_KEY = "zf-portal-api-key"
DEFAULT_SESSION_ID = "zf-portal"
DEFAULT_CONTAINER_NAME = "zf-portal-waha"
DEFAULT_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def check_docker_installed() -> bool:
    """
    Verifica se o Docker está instalado
    
    Returns:
        bool: True se o Docker estiver instalado, False caso contrário
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_container_exists(container_name: str) -> bool:
    """
    Verifica se um container Docker existe
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container existir, False caso contrário
    """
    result = subprocess.run(
        ["docker", "container", "ls", "-a", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        return False
    
    return container_name in result.stdout.split('\n')


def check_container_running(container_name: str) -> bool:
    """
    Verifica se um container Docker está em execução
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container estiver em execução, False caso contrário
    """
    result = subprocess.run(
        ["docker", "container", "ls", "--format", "{{.Names}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        return False
    
    return container_name in result.stdout.split('\n')


def create_waha_container(
    container_name: str,
    api_key: str,
    port: int,
    data_dir: str
) -> bool:
    """
    Cria um container WAHA
    
    Args:
        container_name: Nome do container
        api_key: Chave API para autenticação
        port: Porta para expor o servidor
        data_dir: Diretório para armazenar dados
    
    Returns:
        bool: True se a criação for bem-sucedida, False caso contrário
    """
    # Garantir que o diretório de dados existe
    os.makedirs(data_dir, exist_ok=True)
    
    logger.info(f"Criando container WAHA '{container_name}'...")
    
    # Comando para criar o container
    command = [
        "docker", "run", "-d",
        "--name", container_name,
        "-p", f"{port}:{port}",
        "-e", f"PORT={port}",
        "-e", f"API_KEY={api_key}",
        "-e", "ENABLE_WEBHOOK=true",
        "-e", "WEBHOOK_URL=http://host.docker.internal:8000/api/v1/whatsapp/webhook",
        "-e", "WEBHOOK_ALLOWED_EVENTS=*",
        "-v", f"{data_dir}:/app/store",
        "--restart", "unless-stopped",
        "devlikeapro/whatsapp-http-api:latest"
    ]
    
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        logger.error(f"Erro ao criar container: {result.stderr}")
        return False
    
    logger.info(f"Container criado com ID: {result.stdout.strip()}")
    return True


def start_container(container_name: str) -> bool:
    """
    Inicia um container Docker
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container for iniciado com sucesso, False caso contrário
    """
    logger.info(f"Iniciando container '{container_name}'...")
    
    result = subprocess.run(
        ["docker", "container", "start", container_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        logger.error(f"Erro ao iniciar container: {result.stderr}")
        return False
    
    logger.info("Container iniciado com sucesso")
    return True


def stop_container(container_name: str) -> bool:
    """
    Para um container Docker
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container for parado com sucesso, False caso contrário
    """
    logger.info(f"Parando container '{container_name}'...")
    
    result = subprocess.run(
        ["docker", "container", "stop", container_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        logger.error(f"Erro ao parar container: {result.stderr}")
        return False
    
    logger.info("Container parado com sucesso")
    return True


def remove_container(container_name: str) -> bool:
    """
    Remove um container Docker
    
    Args:
        container_name: Nome do container
    
    Returns:
        bool: True se o container for removido com sucesso, False caso contrário
    """
    logger.info(f"Removendo container '{container_name}'...")
    
    result = subprocess.run(
        ["docker", "container", "rm", container_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        logger.error(f"Erro ao remover container: {result.stderr}")
        return False
    
    logger.info("Container removido com sucesso")
    return True


def check_waha_api(port: int, api_key: str) -> bool:
    """
    Verifica se a API WAHA está respondendo
    
    Args:
        port: Porta do servidor WAHA
        api_key: Chave API para autenticação
    
    Returns:
        bool: True se a API estiver respondendo, False caso contrário
    """
    # Importa requests apenas quando necessário
    import requests
    
    api_url = f"http://localhost:{port}/api/sessions"
    headers = {"x-api-key": api_key}
    
    logger.info("Verificando API WAHA...")
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        if response.status_code == 200:
            logger.info("API WAHA está respondendo corretamente")
            return True
        else:
            logger.warning(f"API WAHA respondeu com status code {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.warning(f"Erro ao conectar na API WAHA: {e}")
        return False


def update_env_file(api_key: str, port: int, session_id: str) -> bool:
    """
    Atualiza ou cria o arquivo .env com as configurações WAHA
    
    Args:
        api_key: Chave API para autenticação
        port: Porta do servidor WAHA
        session_id: ID da sessão WhatsApp
    
    Returns:
        bool: True se o arquivo for atualizado com sucesso, False caso contrário
    """
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
    
    # Valores a adicionar/atualizar
    updates = {
        "WAHA_URL": f"http://localhost:{port}",
        "WAHA_API_KEY": api_key,
        "WAHA_SESSION_ID": session_id
    }
    
    # Verifica se o arquivo existe
    try:
        if os.path.exists(env_path):
            # Ler arquivo existente
            with open(env_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # Processar linhas existentes
            env_vars = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
            
            # Atualizar valores
            env_vars.update(updates)
            
            # Escrever arquivo atualizado
            with open(env_path, 'w', encoding='utf-8') as file:
                for key, value in env_vars.items():
                    file.write(f"{key}={value}\n")
        else:
            # Criar novo arquivo
            with open(env_path, 'w', encoding='utf-8') as file:
                for key, value in updates.items():
                    file.write(f"{key}={value}\n")
        
        logger.info(f"Arquivo .env atualizado em {env_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao atualizar arquivo .env: {e}")
        return False


def setup_waha(
    port: int = DEFAULT_PORT,
    api_key: str = DEFAULT_API_KEY,
    session_id: str = DEFAULT_SESSION_ID,
    container_name: str = DEFAULT_CONTAINER_NAME,
    data_dir: str = DEFAULT_DATA_DIR,
    reset: bool = False
) -> bool:
    """
    Configura e inicia o servidor WAHA
    
    Args:
        port: Porta para expor o servidor
        api_key: Chave API para autenticação
        session_id: ID da sessão WhatsApp
        container_name: Nome do container Docker
        data_dir: Diretório para armazenar dados
        reset: Se True, remove o container existente e cria um novo
    
    Returns:
        bool: True se a configuração for bem-sucedida, False caso contrário
    """
    # Verificar se Docker está instalado
    if not check_docker_installed():
        logger.error("Docker não está instalado. Instale o Docker para continuar.")
        return False
    
    # Verificar se o container já existe
    container_exists = check_container_exists(container_name)
    
    if container_exists and reset:
        # Parar e remover o container existente
        if check_container_running(container_name):
            if not stop_container(container_name):
                return False
        if not remove_container(container_name):
            return False
        container_exists = False
    
    if not container_exists:
        # Criar novo container
        if not create_waha_container(container_name, api_key, port, data_dir):
            return False
    elif not check_container_running(container_name):
        # Iniciar container existente que não está rodando
        if not start_container(container_name):
            return False
    else:
        logger.info(f"Container '{container_name}' já está em execução")
    
    # Aguardar um momento para o servidor iniciar
    logger.info("Aguardando servidor WAHA iniciar...")
    time.sleep(5)
    
    # Verificar API
    if not check_waha_api(port, api_key):
        logger.warning("API WAHA não está respondendo corretamente. Verifique os logs do container.")
    
    # Atualizar arquivo .env
    update_env_file(api_key, port, session_id)
    
    logger.info(f"""
    Servidor WAHA configurado com sucesso!
    
    URL: http://localhost:{port}
    API Key: {api_key}
    Session ID: {session_id}
    Container: {container_name}
    
    Para ver os logs do container:
        docker logs {container_name}
        
    Para obter o QR code via API:
        http://localhost:8000/api/v1/whatsapp/sessions/qr-code
    """)
    
    return True


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Configurar e gerenciar servidor WAHA para WhatsApp')
    
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Porta para o servidor WAHA (padrão: {DEFAULT_PORT})')
    parser.add_argument('--api-key', type=str, default=DEFAULT_API_KEY,
                        help=f'Chave API para autenticação (padrão: {DEFAULT_API_KEY})')
    parser.add_argument('--session-id', type=str, default=DEFAULT_SESSION_ID,
                        help=f'ID da sessão WhatsApp (padrão: {DEFAULT_SESSION_ID})')
    parser.add_argument('--container-name', type=str, default=DEFAULT_CONTAINER_NAME,
                        help=f'Nome do container Docker (padrão: {DEFAULT_CONTAINER_NAME})')
    parser.add_argument('--data-dir', type=str, default=DEFAULT_DATA_DIR,
                        help=f'Diretório para dados da sessão (padrão: {DEFAULT_DATA_DIR})')
    parser.add_argument('--reset', action='store_true',
                        help='Remove o container existente e cria um novo')
    parser.add_argument('--stop', action='store_true',
                        help='Para o container WAHA')
    
    args = parser.parse_args()
    
    if args.stop:
        if check_container_running(args.container_name):
            stop_container(args.container_name)
        else:
            logger.info(f"Container '{args.container_name}' não está em execução")
    else:
        setup_waha(
            port=args.port,
            api_key=args.api_key,
            session_id=args.session_id,
            container_name=args.container_name,
            data_dir=args.data_dir,
            reset=args.reset
        )


if __name__ == "__main__":
    main()
