#!/usr/bin/env python
"""
Script para inicialização completa do sistema ZF Portal Intelligence Agent
com integração WhatsApp e LLM.

Este script inicializa todos os componentes necessários:
1. Servidor WAHA para WhatsApp
2. Redis para cache e filas
3. Aplicação FastAPI
"""

import os
import sys
import time
import logging
import argparse
import subprocess
import threading
from typing import List, Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zf_portal_startup")

# Importando módulo de configuração WAHA
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from setup_waha import setup_waha, check_container_running

# Configurações padrão
DEFAULT_API_PORT = 8000
DEFAULT_WAHA_PORT = 3000
DEFAULT_REDIS_PORT = 6379
DEFAULT_WAHA_CONTAINER = "zf-portal-waha"
DEFAULT_REDIS_CONTAINER = "zf-portal-redis"


def check_redis_running(container_name: str = DEFAULT_REDIS_CONTAINER) -> bool:
    """
    Verifica se o container Redis está em execução
    
    Args:
        container_name: Nome do container Redis
    
    Returns:
        bool: True se o container estiver em execução
    """
    return check_container_running(container_name)


def start_redis_with_docker_compose() -> bool:
    """
    Inicia o Redis usando docker-compose
    
    Returns:
        bool: True se o Redis for iniciado com sucesso
    """
    logger.info("Iniciando Redis com docker-compose...")
    
    result = subprocess.run(
        ["docker-compose", "up", "-d", "redis"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    if result.returncode != 0:
        logger.error(f"Erro ao iniciar Redis: {result.stderr}")
        return False
    
    logger.info("Redis iniciado com sucesso")
    return True


def initialize_database() -> bool:
    """
    Inicializa o banco de dados, executando migrações pendentes
    
    Returns:
        bool: True se o banco for inicializado com sucesso
    """
    logger.info("Inicializando banco de dados...")
    
    try:
        # Importar módulos do banco de dados
        from src.database.models import init_db
        from src.database.db_upgrade import run_migrations
        
        # Inicializar banco e executar migrações
        Session = init_db()
        run_migrations(Session())
        
        logger.info("Banco de dados inicializado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")
        return False


def start_api_server(port: int = DEFAULT_API_PORT) -> subprocess.Popen:
    """
    Inicia o servidor API
    
    Args:
        port: Porta para o servidor API
    
    Returns:
        subprocess.Popen: Processo do servidor API
    """
    logger.info(f"Iniciando servidor API na porta {port}...")
    
    command = [sys.executable, "run_api.py"]
    
    # Definir variáveis de ambiente para a porta
    env = os.environ.copy()
    env["PORT"] = str(port)
    
    # Iniciar processo
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    logger.info(f"Servidor API iniciado com PID {process.pid}")
    return process


def initialize_message_scheduler() -> threading.Thread:
    """
    Inicializa o agendador de mensagens em uma thread separada
    
    Returns:
        threading.Thread: Thread do agendador
    """
    logger.info("Inicializando agendador de mensagens...")
    
    def scheduler_worker():
        try:
            # Importar módulos necessários
            from src.database.models import init_db
            from src.marketing.message_scheduler import MessageScheduler
            from src.database.marketing_repository import FunnelRepository
            
            # Inicializar sessão do banco
            Session = init_db()
            db_session = Session()
            
            # Criar agendador
            scheduler = MessageScheduler(
                repository=FunnelRepository(db_session),
                check_interval=60  # Verificar a cada 60 segundos
            )
            
            # Iniciar loop do agendador
            logger.info("Agendador de mensagens iniciado")
            scheduler.start()
        except Exception as e:
            logger.error(f"Erro no agendador de mensagens: {e}")
    
    # Criar e iniciar thread
    thread = threading.Thread(target=scheduler_worker, daemon=True)
    thread.start()
    
    return thread


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Iniciar o sistema ZF Portal Intelligence Agent')
    
    parser.add_argument('--api-port', type=int, default=DEFAULT_API_PORT,
                        help=f'Porta para o servidor API (padrão: {DEFAULT_API_PORT})')
    parser.add_argument('--waha-port', type=int, default=DEFAULT_WAHA_PORT,
                        help=f'Porta para o servidor WAHA (padrão: {DEFAULT_WAHA_PORT})')
    parser.add_argument('--redis-port', type=int, default=DEFAULT_REDIS_PORT,
                        help=f'Porta para o Redis (padrão: {DEFAULT_REDIS_PORT})')
    parser.add_argument('--skip-waha', action='store_true',
                        help='Pular inicialização do servidor WAHA')
    parser.add_argument('--skip-redis', action='store_true',
                        help='Pular inicialização do Redis')
    parser.add_argument('--reset-waha', action='store_true',
                        help='Recriar container WAHA')
    
    args = parser.parse_args()
    
    # Verificar se os containers já estão em execução
    if not args.skip_waha and not check_container_running(DEFAULT_WAHA_CONTAINER):
        # Configurar servidor WAHA
        setup_waha(
            port=args.waha_port,
            reset=args.reset_waha
        )
    elif not args.skip_waha:
        logger.info(f"Container WAHA '{DEFAULT_WAHA_CONTAINER}' já está em execução")
    
    if not args.skip_redis and not check_redis_running():
        # Iniciar Redis com docker-compose
        start_redis_with_docker_compose()
    elif not args.skip_redis:
        logger.info(f"Container Redis '{DEFAULT_REDIS_CONTAINER}' já está em execução")
    
    # Inicializar banco de dados
    initialize_database()
    
    # Iniciar agendador de mensagens
    scheduler_thread = initialize_message_scheduler()
    
    # Iniciar servidor API
    api_process = start_api_server(args.api_port)
    
    logger.info(f"""
    Sistema ZF Portal Intelligence Agent iniciado!
    
    API: http://localhost:{args.api_port}/api/v1/docs
    WhatsApp WAHA: http://localhost:{args.waha_port}
    Redis: localhost:{args.redis_port}
    
    Pressione Ctrl+C para encerrar...
    """)
    
    try:
        # Manter processo principal vivo
        while True:
            # Verificar se o processo da API ainda está em execução
            if api_process.poll() is not None:
                logger.error("O servidor API foi encerrado inesperadamente")
                # Ler saída do processo para diagnóstico
                stdout, stderr = api_process.communicate()
                logger.error(f"Erro no servidor API: {stderr}")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Encerrando sistema...")
        # Encerrar o processo da API
        api_process.terminate()


if __name__ == "__main__":
    main()
