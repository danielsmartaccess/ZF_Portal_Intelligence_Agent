#!/usr/bin/env python
"""
Script de teste para validar a integração de WhatsApp e LLM

Este script executa testes básicos para verificar se a configuração
está funcionando corretamente, incluindo:
1. Verificar conexão com servidor WAHA
2. Testar autenticação WhatsApp
3. Enviar mensagem de teste
4. Testar integração com LLM
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_integration")

# Carregar variáveis de ambiente
load_dotenv()

# Definir configurações padrão
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "zf-portal-api-key")
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "admin")
TEST_NUMBER = os.getenv("TEST_WHATSAPP_NUMBER")


def get_api_token() -> str:
    """
    Obtém token de autenticação da API
    
    Returns:
        str: Token JWT ou None se falhar
    """
    logger.info("Obtendo token de API...")
    
    try:
        response = requests.post(
            f"{API_URL}/auth/token",
            data={
                "username": API_USERNAME,
                "password": API_PASSWORD
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            logger.info("Token obtido com sucesso")
            return token
        else:
            logger.error(f"Erro ao obter token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exceção ao obter token: {e}")
        return None


def test_whatsapp_connection(token: str) -> bool:
    """
    Testa a conexão com o servidor WhatsApp
    
    Args:
        token: Token JWT para autenticação
    
    Returns:
        bool: True se a conexão estiver funcionando
    """
    logger.info("Testando conexão com WhatsApp...")
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"{API_URL}/whatsapp/sessions/status",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            logger.info(f"Status da sessão WhatsApp: {status}")
            return status == "CONNECTED"
        else:
            logger.error(f"Erro ao verificar status: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao verificar conexão WhatsApp: {e}")
        return False


def start_whatsapp_session(token: str) -> bool:
    """
    Inicia uma sessão WhatsApp
    
    Args:
        token: Token JWT para autenticação
    
    Returns:
        bool: True se a sessão foi iniciada
    """
    logger.info("Iniciando sessão WhatsApp...")
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{API_URL}/whatsapp/sessions",
            headers=headers
        )
        
        if response.status_code == 200:
            logger.info("Sessão iniciada com sucesso")
            return True
        else:
            logger.error(f"Erro ao iniciar sessão: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao iniciar sessão WhatsApp: {e}")
        return False


def get_qr_code(token: str) -> str:
    """
    Obtém o QR Code para autenticação WhatsApp
    
    Args:
        token: Token JWT para autenticação
    
    Returns:
        str: QR Code ou None se falhar
    """
    logger.info("Obtendo QR Code...")
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"{API_URL}/whatsapp/sessions/qr-code",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            qr_code = data.get("qr_code")
            
            if qr_code:
                logger.info("QR Code obtido com sucesso")
                logger.info("\nPara escanear o QR Code:")
                logger.info(f"1. Acesse: {API_URL}/whatsapp/sessions/qr-code no navegador")
                logger.info("2. Ou use este QR Code em ASCII:")
                print("\n" + qr_code + "\n")
                return qr_code
            else:
                logger.warning("QR Code não disponível ou sessão já conectada")
                return None
        else:
            logger.error(f"Erro ao obter QR Code: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Exceção ao obter QR Code: {e}")
        return None


def wait_for_whatsapp_connection(token: str, max_attempts: int = 5) -> bool:
    """
    Aguarda a conexão do WhatsApp ser estabelecida
    
    Args:
        token: Token JWT para autenticação
        max_attempts: Número máximo de tentativas
    
    Returns:
        bool: True se a conexão foi estabelecida
    """
    logger.info(f"Aguardando conexão WhatsApp (máximo {max_attempts} tentativas)...")
    
    for i in range(max_attempts):
        if test_whatsapp_connection(token):
            return True
        
        logger.info(f"Tentativa {i+1}/{max_attempts}: Aguardando 10 segundos...")
        time.sleep(10)
    
    logger.error("Tempo esgotado aguardando conexão WhatsApp")
    return False


def send_test_message(token: str, recipient: str) -> bool:
    """
    Envia uma mensagem de teste
    
    Args:
        token: Token JWT para autenticação
        recipient: Número de telefone do destinatário
    
    Returns:
        bool: True se a mensagem foi enviada com sucesso
    """
    if not recipient:
        logger.error("Número de teste não fornecido")
        return False
    
    logger.info(f"Enviando mensagem de teste para {recipient}...")
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            "recipient": recipient,
            "message_type": "text",
            "message": f"Esta é uma mensagem de teste da integração ZF Portal - {timestamp}"
        }
        
        response = requests.post(
            f"{API_URL}/whatsapp/messages/send",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Mensagem enviada com sucesso: {result}")
            return True
        else:
            logger.error(f"Erro ao enviar mensagem: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção ao enviar mensagem: {e}")
        return False


def test_llm_integration(token: str) -> bool:
    """
    Testa a integração com LLM
    
    Args:
        token: Token JWT para autenticação
    
    Returns:
        bool: True se a integração está funcionando
    """
    logger.info("Testando integração com LLM...")
    
    try:
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Tenta classificar um texto simples
        data = {
            "text": "Olá, gostaria de saber mais sobre o ZF Portal de Antecipações",
            "context": {"test": True}
        }
        
        response = requests.post(
            f"{API_URL}/llm/analyze",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Análise LLM bem-sucedida: {json.dumps(result, indent=2)}")
            return True
        else:
            logger.error(f"Erro na integração LLM: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exceção na integração LLM: {e}")
        return False


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description='Testar integração WhatsApp e LLM'
    )
    
    parser.add_argument('--api-url', type=str, default=API_URL,
                        help='URL da API')
    parser.add_argument('--test-number', type=str, default=TEST_NUMBER,
                        help='Número WhatsApp para teste (formato: 5511999999999)')
    parser.add_argument('--username', type=str, default=API_USERNAME,
                        help='Nome de usuário para API')
    parser.add_argument('--password', type=str, default=API_PASSWORD,
                        help='Senha para API')
      args = parser.parse_args()
    
    # Definir URL da API
    API_URL = args.api_url
    
    # Obter token de autenticação
    token = get_api_token()
    if not token:
        logger.error("Não foi possível obter token de autenticação. Encerrando.")
        sys.exit(1)
    
    # Verificar conexão com WhatsApp
    if not test_whatsapp_connection(token):
        # Iniciar sessão e mostrar QR code
        if start_whatsapp_session(token):
            qr_code = get_qr_code(token)
            if qr_code:
                logger.info("Escaneie o QR Code com o WhatsApp para autenticar.")
                logger.info("Aguardando conexão...")
                wait_for_whatsapp_connection(token)
        else:
            logger.error("Não foi possível iniciar sessão WhatsApp. Encerrando.")
            sys.exit(1)
    
    # Testar envio de mensagem
    if args.test_number:
        if send_test_message(token, args.test_number):
            logger.info("Teste de mensagem enviado com sucesso!")
        else:
            logger.error("Falha no envio de mensagem de teste.")
    else:
        logger.warning("Número de teste não fornecido. Pulando teste de mensagem.")
    
    # Testar integração com LLM
    test_llm_integration(token)
    
    logger.info("Testes de integração concluídos!")


if __name__ == "__main__":
    main()
