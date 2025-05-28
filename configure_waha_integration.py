#!/usr/bin/env python
"""
Script para configurar e testar a integração WAHA com o Portal ZF

Este script realiza:
1. Verificação da configuração do WAHA
2. Teste de conectividade com a API
3. Configuração da sessão WhatsApp
4. Teste de envio de mensagens (após autenticação)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any

# Adiciona o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from whatsapp.whatsapp_connector import WhatsAppConnector
from whatsapp.whatsapp_session_manager import WhatsAppSessionManager, SessionStatus

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waha_integration_setup")


class WAHAIntegrationSetup:
    """Classe para configuração e teste da integração WAHA"""
    
    def __init__(self):
        """Inicializa a configuração da integração"""
        self.base_url = "http://localhost:3000"
        self.api_key = "zf-portal-api-key"
        self.session_id = "default"
        self.connector = None
        self.session_manager = None
        
    def check_waha_server(self) -> bool:
        """
        Verifica se o servidor WAHA está disponível
        
        Returns:
            bool: True se o servidor estiver disponível
        """
        try:
            import requests
            response = requests.get(f"{self.base_url}/health", timeout=5)
            logger.info(f"Servidor WAHA disponível: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            # Tenta verificar se a API básica está funcionando
            try:
                headers = {"X-API-Key": self.api_key}
                response = requests.get(f"{self.base_url}/api/sessions", headers=headers, timeout=5)
                logger.info(f"API WAHA disponível: {response.status_code}")
                return response.status_code == 200
            except Exception as e2:
                logger.error(f"Servidor WAHA não disponível: {e2}")
                return False
    
    def initialize_connector(self) -> bool:
        """
        Inicializa o conector WhatsApp
        
        Returns:
            bool: True se a inicialização for bem-sucedida
        """
        try:
            self.connector = WhatsAppConnector(
                base_url=self.base_url,
                api_key=self.api_key,
                session_name=self.session_id
            )
            logger.info("Conector WhatsApp inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar conector: {e}")
            return False
    
    def check_session_status(self) -> Dict[str, Any]:
        """
        Verifica o status da sessão WhatsApp
        
        Returns:
            Dict: Status da sessão
        """
        try:
            # Corrige o endpoint para usar a API correta
            import requests
            headers = {"X-API-Key": self.api_key}
            response = requests.get(f"{self.base_url}/api/sessions", headers=headers)
            response.raise_for_status()
            
            sessions = response.json()
            if isinstance(sessions, list) and len(sessions) > 0:
                session = sessions[0]
                status_info = {
                    "name": session.get("name", "unknown"),
                    "status": session.get("status", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
                logger.info(f"Status da sessão: {status_info}")
                return status_info
            else:
                logger.warning("Nenhuma sessão encontrada")
                return {"status": "NO_SESSION", "timestamp": datetime.now().isoformat()}
                
        except Exception as e:
            logger.error(f"Erro ao verificar status da sessão: {e}")
            return {"status": "ERROR", "error": str(e), "timestamp": datetime.now().isoformat()}
    
    def get_qr_code(self) -> bool:
        """
        Obtém e salva o código QR para autenticação
        
        Returns:
            bool: True se o QR code foi obtido com sucesso
        """
        try:
            import requests
            headers = {"X-API-Key": self.api_key}
            response = requests.get(f"{self.base_url}/api/{self.session_id}/auth/qr", headers=headers)
            
            if response.status_code == 200:
                # Salva o QR code como imagem
                qr_filename = f"qr_code_{self.session_id}_{int(time.time())}.png"
                with open(qr_filename, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"QR Code salvo como: {qr_filename}")
                logger.info("Para autenticar:")
                logger.info("1. Abra o WhatsApp no seu celular")
                logger.info("2. Vá em Configurações > Dispositivos conectados")
                logger.info("3. Toque em 'Conectar um dispositivo'")
                logger.info(f"4. Escaneie o QR code no arquivo: {qr_filename}")
                return True
            else:
                logger.error(f"Erro ao obter QR code: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao obter QR code: {e}")
            return False
    
    def wait_for_authentication(self, timeout: int = 120) -> bool:
        """
        Aguarda a autenticação ser concluída
        
        Args:
            timeout: Tempo limite em segundos
            
        Returns:
            bool: True se a autenticação foi bem-sucedida
        """
        logger.info(f"Aguardando autenticação (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_info = self.check_session_status()
            current_status = status_info.get("status", "UNKNOWN")
            
            if current_status == "WORKING":
                logger.info("✅ Autenticação bem-sucedida! WhatsApp conectado.")
                return True
            elif current_status == "FAILED":
                logger.error("❌ Falha na autenticação")
                return False
            elif current_status == "SCAN_QR_CODE":
                logger.info("⏳ Aguardando escaneamento do QR code...")
            else:
                logger.info(f"⏳ Status atual: {current_status}")
            
            time.sleep(5)
        
        logger.warning("⏰ Timeout na autenticação")
        return False
    
    def test_send_message(self, phone_number: str = None, message: str = None) -> bool:
        """
        Testa o envio de uma mensagem
        
        Args:
            phone_number: Número de telefone (formato: 5511999999999)
            message: Mensagem a ser enviada
            
        Returns:
            bool: True se a mensagem foi enviada com sucesso
        """
        if not phone_number:
            phone_number = input("Digite o número de telefone (formato: 5511999999999): ").strip()
        
        if not message:
            message = "🤖 Teste de integração WAHA - Portal ZF\n\nEsta é uma mensagem de teste para verificar se a integração está funcionando corretamente."
        
        try:
            import requests
            headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
            
            data = {
                "chatId": f"{phone_number}@c.us",
                "text": message,
                "session": self.session_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/sendText",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Mensagem enviada com sucesso! ID: {result.get('id', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Erro ao enviar mensagem: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def run_setup_wizard(self):
        """Executa o assistente de configuração completo"""
        print("=" * 60)
        print("🚀 CONFIGURAÇÃO DA INTEGRAÇÃO WAHA - PORTAL ZF")
        print("=" * 60)
        
        # 1. Verificar servidor WAHA
        print("\n📡 1. Verificando servidor WAHA...")
        if not self.check_waha_server():
            print("❌ Servidor WAHA não está disponível!")
            print("Certifique-se de que o container Docker está rodando:")
            print("   docker ps | grep waha")
            return False
        print("✅ Servidor WAHA disponível")
        
        # 2. Inicializar conector
        print("\n🔌 2. Inicializando conector...")
        if not self.initialize_connector():
            print("❌ Falha ao inicializar conector")
            return False
        print("✅ Conector inicializado")
        
        # 3. Verificar status da sessão
        print("\n📱 3. Verificando status da sessão...")
        status_info = self.check_session_status()
        current_status = status_info.get("status", "UNKNOWN")
        print(f"📊 Status atual: {current_status}")
        
        # 4. Se não estiver conectado, iniciar processo de autenticação
        if current_status != "WORKING":
            print("\n🔐 4. Iniciando processo de autenticação...")
            
            if current_status == "SCAN_QR_CODE" or current_status == "STARTING":
                print("📱 Obtendo QR code...")
                if self.get_qr_code():
                    if self.wait_for_authentication():
                        print("✅ Autenticação concluída com sucesso!")
                    else:
                        print("❌ Falha na autenticação")
                        return False
                else:
                    print("❌ Erro ao obter QR code")
                    return False
            else:
                print(f"⚠️  Status inesperado: {current_status}")
                return False
        else:
            print("✅ WhatsApp já está conectado!")
        
        # 5. Teste opcional de envio de mensagem
        print("\n💬 5. Teste de envio de mensagem (opcional)")
        test_message = input("Deseja testar o envio de uma mensagem? (s/n): ").strip().lower()
        
        if test_message == 's':
            self.test_send_message()
        
        print("\n🎉 Configuração concluída!")
        print("🔗 O Portal ZF agora está integrado com o WhatsApp via WAHA")
        return True


def main():
    """Função principal"""
    setup = WAHAIntegrationSetup()
    success = setup.run_setup_wizard()
    
    if success:
        print("\n📋 Próximos passos:")
        print("1. Configure webhooks para recebimento de mensagens")
        print("2. Implemente os fluxos de chatbot específicos")
        print("3. Configure templates de mensagens para campanhas")
        print("4. Teste a integração completa com o Portal ZF")
    else:
        print("\n❌ Configuração falhou. Verifique os logs para mais detalhes.")


if __name__ == "__main__":
    main()
