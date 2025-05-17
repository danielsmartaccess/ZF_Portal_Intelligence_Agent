"""
Configurações da API
"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Configurações do banco de dados
    database_url: str = "sqlite:///./database.db"
    
    # Configurações da API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "ZF Portal Intelligence Agent"
    version: str = "1.0.0"
    
    # Configurações de segurança
    secret_key: str = "your-secret-key-here"  # Deve ser substituído por uma chave segura
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Configurações do WhatsApp
    waha_url: str = "http://localhost:3000"  # URL da API WAHA
    waha_api_key: str = "your-waha-api-key"  # Chave API para autenticação
    waha_session_id: str = "zf-portal"  # ID da sessão WhatsApp
    
    # Configurações do LLM
    llm_provider: str = "openai"  # Provedor do modelo (openai, azure)
    llm_api_key: str = "your-openai-api-key"  # Chave API do provedor
    llm_model: str = "gpt-4o"  # Modelo a ser utilizado
    llm_temperature: float = 0.7  # Temperatura para geração de texto
    
    # Configurações do funil de marketing
    business_hours_start: int = 9  # Hora de início do horário comercial (0-23)
    business_hours_end: int = 18  # Hora de fim do horário comercial (0-23)
    business_days: list = [0, 1, 2, 3, 4]  # Dias úteis (0=segunda, 6=domingo)

    class Config:
        env_file = ".env"
        extra = "allow"  # Permite variáveis extras no .env

@lru_cache()
def get_settings():
    return Settings()
