#!/usr/bin/env python
"""
Script completo para configuração WAHA baseado na documentação oficial

Este script implementa o processo completo conforme a documentação:
1. Verificação do servidor WAHA
2. Criação/inicialização da sessão 
3. Obtenção do QR code
4. Monitoramento do status até WORKING
5. Teste de envio de mensagem

Documentação de referência: https://waha.devlike.pro/docs/overview/quick-start/
"""

import os
import sys
import json
import time
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waha_setup_complete")


class WAHASetup:
    """Classe para configuração completa do WAHA seguindo a documentação oficial"""
    
    def __init__(self, 
                 base_url: str = "http://localhost:3000",
                 api_key: str = "zf-portal-api-key",
                 session_name: str = "default"):
        """
        Inicializa a configuração WAHA
        
        Args:
            base_url: URL base do servidor WAHA
            api_key: Chave API (pode ser None para versão Core)
            session_name: Nome da sessão
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session_name = session_name
        self.headers = {
            "Content-Type": "application/json"
        }
        
        # Adiciona API key se fornecida
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
    
    def check_server_health(self) -> bool:
        """
        Verifica se o servidor WAHA está funcionando
        
        Returns:
            bool: True se o servidor estiver disponível
        """
        try:
            # Tenta acessar a página principal
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Servidor WAHA está disponível")
                return True
                
            # Se falhar, tenta a API diretamente
            response = requests.get(f"{self.base_url}/api/sessions", 
                                  headers=self.headers, timeout=10)
            if response.status_code == 200:
                logger.info("✅ API WAHA está disponível")
                return True
                
            logger.error(f"❌ Servidor WAHA não responde: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao conectar com servidor WAHA: {e}")
            return False
    
    def list_sessions(self) -> List[Dict]:
        """
        Lista todas as sessões existentes
        
        Returns:
            List[Dict]: Lista de sessões
        """
        try:
            response = requests.get(f"{self.base_url}/api/sessions", 
                                  headers=self.headers)
            response.raise_for_status()
            
            sessions = response.json()
            logger.info(f"📋 Encontradas {len(sessions)} sessão(ões)")
            
            for session in sessions:
                name = session.get('name', 'unknown')
                status = session.get('status', 'unknown')
                logger.info(f"  - {name}: {status}")
            
            return sessions
            
        except Exception as e:
            logger.error(f"❌ Erro ao listar sessões: {e}")
            return []
    
    def get_session_info(self, session_name: str = None) -> Optional[Dict]:
        """
        Obtém informações de uma sessão específica
        
        Args:
            session_name: Nome da sessão (usa self.session_name se None)
            
        Returns:
            Dict: Informações da sessão ou None se não encontrada
        """
        if session_name is None:
            session_name = self.session_name
            
        try:
            response = requests.get(f"{self.base_url}/api/sessions/{session_name}", 
                                  headers=self.headers)
            
            if response.status_code == 404:
                logger.info(f"📭 Sessão '{session_name}' não existe")
                return None
                
            response.raise_for_status()
            session_info = response.json()
            
            status = session_info.get('status', 'unknown')
            logger.info(f"📱 Sessão '{session_name}': {status}")
            
            return session_info
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações da sessão: {e}")
            return None
    
    def create_session(self, config: Dict = None) -> bool:
        """
        Cria uma nova sessão
        
        Args:
            config: Configuração da sessão (opcional)
            
        Returns:
            bool: True se a sessão foi criada com sucesso
        """
        try:
            # Configuração padrão para o Portal ZF
            default_config = {
                "name": self.session_name,
                "config": {
                    "webhooks": [
                        {
                            "url": "http://host.docker.internal:8000/api/v1/whatsapp/webhook",
                            "events": ["message", "session.status"]
                        }
                    ],
                    "debug": True,
                    "metadata": {
                        "project": "ZF Portal",
                        "environment": "development"
                    }
                }
            }
            
            # Usa a configuração fornecida ou a padrão
            session_config = config or default_config
            
            logger.info(f"🔧 Criando sessão '{self.session_name}'...")
            
            response = requests.post(f"{self.base_url}/api/sessions", 
                                   headers=self.headers, 
                                   json=session_config)
            response.raise_for_status()
            
            result = response.json()
            status = result.get('status', 'unknown')
            
            logger.info(f"✅ Sessão criada com sucesso. Status: {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar sessão: {e}")
            return False
    
    def start_session(self) -> bool:
        """
        Inicia uma sessão existente
        
        Returns:
            bool: True se a sessão foi iniciada com sucesso
        """
        try:
            logger.info(f"▶️ Iniciando sessão '{self.session_name}'...")
            
            response = requests.post(f"{self.base_url}/api/sessions/{self.session_name}/start", 
                                   headers=self.headers)
            response.raise_for_status()
            
            logger.info("✅ Sessão iniciada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sessão: {e}")
            return False
    
    def get_qr_code(self, save_path: str = None) -> bool:
        """
        Obtém e salva o QR code para autenticação
        
        Args:
            save_path: Caminho para salvar o QR code (opcional)
            
        Returns:
            bool: True se o QR code foi obtido com sucesso
        """
        try:
            logger.info("📱 Obtendo QR code para autenticação...")
            
            # Endpoint correto conforme documentação
            response = requests.get(f"{self.base_url}/api/{self.session_name}/auth/qr", 
                                  headers=self.headers)
            
            if response.status_code == 200:
                # Define o nome do arquivo se não fornecido
                if save_path is None:
                    timestamp = int(time.time())
                    save_path = f"qr_code_{self.session_name}_{timestamp}.png"
                
                # Salva o QR code
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"💾 QR Code salvo como: {save_path}")
                self._print_qr_instructions(save_path)
                return True
                
            elif response.status_code == 400:
                logger.warning("⚠️ QR code não disponível. Sessão pode já estar autenticada.")
                return False
                
            else:
                logger.error(f"❌ Erro ao obter QR code: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter QR code: {e}")
            return False
    
    def _print_qr_instructions(self, qr_path: str):
        """Imprime instruções para usar o QR code"""
        print("\n" + "="*60)
        print("📱 INSTRUÇÕES PARA AUTENTICAÇÃO WHATSAPP")
        print("="*60)
        print("1. Abra o WhatsApp no seu celular")
        print("2. Vá em Configurações > Dispositivos conectados")
        print("3. Toque em 'Conectar um dispositivo'")
        print(f"4. Escaneie o QR code no arquivo: {qr_path}")
        print("5. Aguarde a confirmação no terminal...")
        print("="*60)
    
    def wait_for_authentication(self, timeout: int = 120) -> bool:
        """
        Aguarda a autenticação ser concluída
        
        Args:
            timeout: Tempo limite em segundos
            
        Returns:
            bool: True se a autenticação foi bem-sucedida
        """
        logger.info(f"⏳ Aguardando autenticação (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            session_info = self.get_session_info()
            
            if session_info:
                status = session_info.get('status', 'UNKNOWN')
                
                if status == 'WORKING':
                    me_info = session_info.get('me')
                    if me_info:
                        phone = me_info.get('id', 'N/A')
                        name = me_info.get('pushName', 'N/A')
                        logger.info(f"🎉 Autenticação concluída!")
                        logger.info(f"📞 Telefone: {phone}")
                        logger.info(f"👤 Nome: {name}")
                    else:
                        logger.info("✅ Autenticação concluída!")
                    return True
                    
                elif status == 'FAILED':
                    logger.error("❌ Falha na autenticação")
                    return False
                    
                elif status == 'SCAN_QR_CODE':
                    logger.info("📱 Aguardando escaneamento do QR code...")
                    
                elif status == 'STARTING':
                    logger.info("🔄 Inicializando sessão...")
                    
                else:
                    logger.info(f"📊 Status atual: {status}")
            
            time.sleep(5)
        
        logger.warning("⏰ Timeout na autenticação")
        return False
    
    def send_test_message(self, phone_number: str = None, message: str = None) -> bool:
        """
        Envia uma mensagem de teste
        
        Args:
            phone_number: Número de telefone (formato: 5511999999999)
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        if not phone_number:
            phone_number = input("📞 Digite o número de telefone (formato: 5511999999999): ").strip()
        
        if not message:
            message = ("🤖 Teste de integração WAHA - Portal ZF\n\n"
                      "Esta é uma mensagem de teste para verificar se a integração "
                      "está funcionando corretamente.\n\n"
                      f"Enviada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        try:
            logger.info(f"💬 Enviando mensagem de teste para {phone_number}...")
            
            # Formato correto do chatId conforme documentação
            chat_id = f"{phone_number}@c.us"
            
            data = {
                "chatId": chat_id,
                "text": message,
                "session": self.session_name
            }
            
            response = requests.post(f"{self.base_url}/api/sendText",
                                   headers=self.headers,
                                   json=data)
            response.raise_for_status()
            
            result = response.json()
            message_id = result.get('id', 'N/A')
            
            logger.info(f"✅ Mensagem enviada com sucesso!")
            logger.info(f"📧 ID da mensagem: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def run_complete_setup(self) -> bool:
        """
        Executa o processo completo de configuração
        
        Returns:
            bool: True se todo o processo foi bem-sucedido
        """
        print("🚀 CONFIGURAÇÃO COMPLETA WAHA - PORTAL ZF")
        print("=" * 50)
        
        # 1. Verificar servidor
        print("\n🔍 1. Verificando servidor WAHA...")
        if not self.check_server_health():
            print("❌ Servidor WAHA não está disponível!")
            print("   Certifique-se de que o container está rodando:")
            print("   docker ps | findstr waha")
            return False
        
        # 2. Verificar sessões existentes
        print("\n📋 2. Verificando sessões existentes...")
        sessions = self.list_sessions()
        
        # 3. Verificar se a sessão padrão existe
        print(f"\n🔍 3. Verificando sessão '{self.session_name}'...")
        session_info = self.get_session_info()
        
        if session_info is None:
            # Sessão não existe, criar uma nova
            print(f"\n🔧 4. Criando nova sessão '{self.session_name}'...")
            if not self.create_session():
                return False
        else:
            status = session_info.get('status', 'UNKNOWN')
            if status == 'WORKING':
                logger.info("✅ Sessão já está autenticada e funcionando!")
                return self._test_authenticated_session()
            elif status == 'STOPPED':
                logger.info("🔄 Sessão existe mas está parada. Iniciando...")
                if not self.start_session():
                    return False
        
        # 4. Aguardar status SCAN_QR_CODE e obter QR
        print("\n📱 4. Aguardando QR code...")
        max_attempts = 10
        for attempt in range(max_attempts):
            session_info = self.get_session_info()
            if session_info:
                status = session_info.get('status', 'UNKNOWN')
                
                if status == 'SCAN_QR_CODE':
                    logger.info("📱 Status SCAN_QR_CODE detectado. Obtendo QR code...")
                    if self.get_qr_code():
                        break
                    else:
                        logger.warning("Falha ao obter QR code, tentando novamente...")
                        
                elif status == 'WORKING':
                    logger.info("✅ Sessão já está autenticada!")
                    return self._test_authenticated_session()
                    
                else:
                    logger.info(f"⏳ Aguardando status SCAN_QR_CODE... (atual: {status})")
            
            time.sleep(3)
        else:
            logger.error("❌ Timeout aguardando QR code")
            return False
        
        # 5. Aguardar autenticação
        print("\n🔐 5. Aguardando autenticação...")
        if not self.wait_for_authentication():
            logger.error("❌ Falha na autenticação")
            return False
        
        # 6. Teste de funcionalidade
        return self._test_authenticated_session()
    
    def _test_authenticated_session(self) -> bool:
        """Testa a sessão autenticada"""
        print("\n✅ 6. Sessão autenticada com sucesso!")
        
        # Teste opcional de envio de mensagem
        print("\n💬 7. Teste de envio de mensagem (opcional)")
        test_message = input("Deseja testar o envio de uma mensagem? (s/N): ").strip().lower()
        
        if test_message == 's':
            return self.send_test_message()
        else:
            print("⏭️ Teste de mensagem pulado")
            
        print("\n🎉 Configuração concluída com sucesso!")
        print("🔗 O Portal ZF agora está integrado com o WhatsApp via WAHA")
        self._print_next_steps()
        return True
    
    def _print_next_steps(self):
        """Imprime os próximos passos"""
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. ✅ Configure webhooks para recebimento de mensagens")
        print("2. ✅ Implemente os fluxos de chatbot específicos")
        print("3. ✅ Configure templates de mensagens para campanhas")
        print("4. ✅ Teste a integração completa com o Portal ZF")
        print("\n🔗 URLs úteis:")
        print(f"   Dashboard: {self.base_url}/dashboard")
        print(f"   Swagger API: {self.base_url}/")


def main():
    """Função principal"""
    try:
        # Configuração baseada no ambiente atual
        setup = WAHASetup(
            base_url="http://localhost:3000",
            api_key="zf-portal-api-key",  # API key do container atual
            session_name="default"
        )
        
        success = setup.run_complete_setup()
        
        if not success:
            print("\n❌ Configuração falhou. Verifique os logs para mais detalhes.")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Configuração cancelada pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
