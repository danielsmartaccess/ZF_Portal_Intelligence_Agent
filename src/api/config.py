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

    class Config:
        env_file = ".env"
        extra = "allow"  # Permite variáveis extras no .env

@lru_cache()
def get_settings():
    return Settings()
