"""
Script para testar a conexão WhatsApp e verificar o número conectado
"""

import requests
import json
import time
from datetime import datetime

# Configurações
WAHA_URL = "http://localhost:3000"
API_KEY = "zf-portal-api-key"
SESSION_NAME = "default"
YOUR_NUMBER = "5551981418383"  # Seu número no formato internacional

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

def check_session_status():
    """Verifica o status da sessão"""
    try:
        response = requests.get(f"{WAHA_URL}/api/sessions/{SESSION_NAME}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"Status da sessão: {data.get('status')}")
            if data.get('me'):
                print(f"Número conectado: {data.get('me')}")
            return data
        else:
            print(f"Erro ao verificar status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def send_test_message():
    """Envia mensagem de teste"""
    chat_id = f"{YOUR_NUMBER}@c.us"
    message_data = {
        "session": SESSION_NAME,
        "chatId": chat_id,
        "text": f"🤖 Teste do chatbot ZF Portal - {datetime.now().strftime('%H:%M:%S')}"
    }
    
    try:
        response = requests.post(f"{WAHA_URL}/api/sendText", headers=headers, json=message_data)
        if response.status_code == 200:
            print("✅ Mensagem enviada com sucesso!")
            return response.json()
        else:
            print(f"❌ Erro ao enviar mensagem: {response.status_code}")
            print(f"Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def main():
    print("=== Teste de Conexão WhatsApp ===")
    print(f"Testando conexão para o número: {YOUR_NUMBER}")
    print()
    
    # Verificar status da sessão
    print("1. Verificando status da sessão...")
    session_data = check_session_status()
    
    if not session_data:
        print("❌ Não foi possível verificar o status da sessão")
        return
    
    status = session_data.get('status')
    
    if status == 'SCAN_QR_CODE':
        print("📱 A sessão está aguardando escaneamento do QR code")
        print("Por favor, escaneie o QR code com seu WhatsApp e execute o script novamente")
        return
    elif status == 'WORKING':
        print("✅ Sessão ativa e funcionando!")
        me = session_data.get('me')
        if me:
            print(f"📞 Número conectado: {me}")
        
        # Tentar enviar mensagem de teste
        print("\n2. Enviando mensagem de teste...")
        result = send_test_message()
        
        if result:
            print("✅ Teste concluído com sucesso!")
        else:
            print("❌ Falha no teste de envio")
    else:
        print(f"⚠️  Status da sessão: {status}")

if __name__ == "__main__":
    main()
