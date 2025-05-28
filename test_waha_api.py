#!/usr/bin/env python
"""
Script para testar diretamente a API WAHA
"""

import requests
import json
import logging
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_waha_api")

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WAHA_URL = os.getenv("WAHA_URL", "http://localhost:3000")
WAHA_API_KEY = os.getenv("WAHA_API_KEY", "zf-portal-api-key")
WAHA_SESSION = os.getenv("WAHA_SESSION", "default")

def test_api_request(method, endpoint, data=None):
    """
    Testa uma requisição para a API WAHA
    
    Args:
        method: Método HTTP (GET, POST)
        endpoint: Endpoint da API
        data: Dados para envio (opcional)
    """
    url = f"{WAHA_URL}/{endpoint.lstrip('/')}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": WAHA_API_KEY
    }
    
    print(f"\nTestando requisição {method} para {url}")
    print(f"Headers: {headers}")
    if data:
        print(f"Data: {data}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.content:
            try:
                print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Response text: {response.text}")
        else:
            print("No response content")
        
    except Exception as e:
        print(f"Erro na requisição: {e}")

def test_waha_api():
    """Testa os principais endpoints da API WAHA"""
    
    print("\n=== Testando API WAHA ===")
    print(f"URL base: {WAHA_URL}")
    print(f"API Key: {WAHA_API_KEY}")
    print(f"Sessão: {WAHA_SESSION}")
    
    # Verificar disponibilidade da API
    test_api_request("GET", "api/")
    
    # Listar sessões existentes
    test_api_request("GET", "api/sessions")
    
    # Iniciar sessão
    test_api_request("POST", f"api/sessions/{WAHA_SESSION}/start")
    
    # Verificar status da sessão
    test_api_request("GET", f"api/sessions/{WAHA_SESSION}/status")
    
    # Obter QR code
    test_api_request("GET", f"api/sessions/{WAHA_SESSION}/qr")
    
    print("\n=== Teste da API WAHA concluído ===")

if __name__ == "__main__":
    test_waha_api()
