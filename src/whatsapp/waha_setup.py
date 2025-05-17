"""
Script para configuração do servidor WAHA (WhatsApp Web API)

Este script instala e configura o servidor WAHA para integração com WhatsApp
no ZF Portal Intelligence Agent.
"""

import os
import subprocess
import json
import logging
from typing import Dict, Any

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waha_setup")

# Diretório para armazenar configurações WAHA
WAHA_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'waha_config')
WAHA_DOCKER_COMPOSE = os.path.join(WAHA_CONFIG_DIR, 'docker-compose.yml')

class WAHASetup:
    """Classe para configuração do ambiente WAHA para WhatsApp"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o setup do WAHA
        
        Args:
            config: Configurações personalizadas para o WAHA
        """
        self.config = config or {}
        self._ensure_config_dir()
    
    def _ensure_config_dir(self) -> None:
        """Garante que o diretório de configuração existe"""
        if not os.path.exists(WAHA_CONFIG_DIR):
            os.makedirs(WAHA_CONFIG_DIR)
            logger.info(f"Diretório de configuração criado: {WAHA_CONFIG_DIR}")
    
    def create_docker_compose(self) -> None:
        """Cria o arquivo docker-compose.yml para o WAHA"""
        # Configurações padrão para o servidor WAHA
        waha_port = self.config.get('port', 3000)
        waha_webhook_url = self.config.get('webhook_url', 'http://host.docker.internal:8000/webhook/whatsapp')
        waha_webhook_allowed_events = self.config.get('webhook_allowed_events', 'message,message-ack')
        
        docker_compose_content = f"""version: '3'

services:
  waha:
    image: devlikeapro/whatsapp-http-api
    container_name: zf_portal_waha
    restart: unless-stopped
    ports:
      - "{waha_port}:3000"
    environment:
      - WHATSAPP_HOOK_URL={waha_webhook_url}
      - WHATSAPP_HOOK_EVENTS={waha_webhook_allowed_events}
      - WHATSAPP_API_KEY={self.config.get('api_key', 'your_secret_api_key')}
      - WHATSAPP_SAVE_CHATS={self.config.get('save_chats', 'true')}
    volumes:
      - ./waha_data:/app/store
"""
        
        with open(WAHA_DOCKER_COMPOSE, 'w') as file:
            file.write(docker_compose_content)
        
        logger.info(f"Arquivo docker-compose criado: {WAHA_DOCKER_COMPOSE}")
    
    def start_waha_server(self) -> bool:
        """
        Inicia o servidor WAHA via Docker Compose
        
        Returns:
            bool: True se o servidor iniciou com sucesso
        """
        if not os.path.exists(WAHA_DOCKER_COMPOSE):
            logger.error("Arquivo docker-compose não encontrado. Execute create_docker_compose() primeiro.")
            return False
        
        try:
            # Muda para o diretório de configuração
            cwd = os.getcwd()
            os.chdir(WAHA_CONFIG_DIR)
            
            # Inicia o servidor WAHA
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Servidor WAHA iniciado com sucesso")
            logger.debug(result.stdout)
            
            # Retorna ao diretório original
            os.chdir(cwd)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao iniciar servidor WAHA: {e}")
            logger.error(e.stderr)
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao iniciar servidor WAHA: {e}")
            return False
    
    def stop_waha_server(self) -> bool:
        """
        Para o servidor WAHA
        
        Returns:
            bool: True se o servidor foi parado com sucesso
        """
        if not os.path.exists(WAHA_DOCKER_COMPOSE):
            logger.error("Arquivo docker-compose não encontrado. Execute create_docker_compose() primeiro.")
            return False
        
        try:
            # Muda para o diretório de configuração
            cwd = os.getcwd()
            os.chdir(WAHA_CONFIG_DIR)
            
            # Para o servidor WAHA
            result = subprocess.run(
                ["docker-compose", "down"],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info("Servidor WAHA parado com sucesso")
            logger.debug(result.stdout)
            
            # Retorna ao diretório original
            os.chdir(cwd)
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao parar servidor WAHA: {e}")
            logger.error(e.stderr)
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao parar servidor WAHA: {e}")
            return False
    
    def save_config_to_file(self, config_file: str = None) -> bool:
        """
        Salva a configuração em um arquivo JSON
        
        Args:
            config_file: Caminho para o arquivo de configuração (opcional)
            
        Returns:
            bool: True se a configuração foi salva com sucesso
        """
        if not config_file:
            config_file = os.path.join(WAHA_CONFIG_DIR, 'waha_config.json')
            
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuração salva em: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            return False
    
    def load_config_from_file(self, config_file: str = None) -> bool:
        """
        Carrega a configuração de um arquivo JSON
        
        Args:
            config_file: Caminho para o arquivo de configuração (opcional)
            
        Returns:
            bool: True se a configuração foi carregada com sucesso
        """
        if not config_file:
            config_file = os.path.join(WAHA_CONFIG_DIR, 'waha_config.json')
        
        if not os.path.exists(config_file):
            logger.warning(f"Arquivo de configuração não encontrado: {config_file}")
            return False
            
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Configuração carregada de: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return False


# Função principal para iniciar a configuração
def main():
    """Função principal para setup do WAHA"""
    # Exemplo de configuração
    config = {
        'port': 3000,
        'webhook_url': 'http://host.docker.internal:8000/api/webhooks/whatsapp',
        'webhook_allowed_events': 'message,message-ack',
        'api_key': 'zf_portal_waha_key',
        'save_chats': 'true'
    }
    
    # Inicializa o setup
    setup = WAHASetup(config)
    
    # Cria o arquivo docker-compose
    setup.create_docker_compose()
    
    # Salva a configuração
    setup.save_config_to_file()
    
    # Inicia o servidor
    if setup.start_waha_server():
        print("Servidor WAHA configurado e iniciado com sucesso!")
    else:
        print("Falha ao iniciar servidor WAHA.")


if __name__ == "__main__":
    main()
