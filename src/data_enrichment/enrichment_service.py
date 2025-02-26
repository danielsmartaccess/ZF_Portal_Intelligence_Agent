"""
Serviço de enriquecimento de dados que integra múltiplas APIs (Lusha, Clearbit)
com sistema de fallback e cache.
"""
from typing import Dict, Optional, List
import requests
import redis
from datetime import datetime, timedelta
import logging
import structlog
from abc import ABC, abstractmethod

logger = structlog.get_logger(__name__)

class EnrichmentError(Exception):
    """Erro base para falhas no enriquecimento de dados."""
    pass

class EnrichmentProvider(ABC):
    """Classe base para provedores de enriquecimento de dados."""
    
    @abstractmethod
    def enrich_contact(self, contact_data: Dict) -> Dict:
        """Enriquece dados de contato usando o provedor específico."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o serviço está disponível."""
        pass

class LushaProvider(EnrichmentProvider):
    """Provedor de enriquecimento usando a API da Lusha."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.lusha.com/v1"
        
    def enrich_contact(self, contact_data: Dict) -> Dict:
        """Enriquece dados usando a API da Lusha."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "name": contact_data.get("nome"),
                "company": contact_data.get("empresa"),
                "linkedin_url": contact_data.get("perfil_linkedin")
            }
            
            response = requests.get(
                f"{self.base_url}/person",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "email": data.get("email"),
                "telefone": data.get("phone"),
                "cargo_atual": data.get("current_position"),
                "departamento": data.get("department"),
                "fonte": "Lusha",
                "confiabilidade": data.get("confidence_score", 0)
            }
            
        except requests.RequestException as e:
            logger.error("erro_lusha", erro=str(e), contact=contact_data.get("nome"))
            raise EnrichmentError(f"Erro na API Lusha: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica se a API da Lusha está acessível."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except:
            return False

class ClearbitProvider(EnrichmentProvider):
    """Provedor de enriquecimento usando a API do Clearbit."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://person.clearbit.com/v2"
        
    def enrich_contact(self, contact_data: Dict) -> Dict:
        """Enriquece dados usando a API do Clearbit."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Tenta enriquecer primeiro pelo LinkedIn
            linkedin_url = contact_data.get("perfil_linkedin")
            if linkedin_url:
                params = {"linkedin": linkedin_url}
            else:
                # Fallback para busca por nome e empresa
                params = {
                    "name": contact_data.get("nome"),
                    "company": contact_data.get("empresa")
                }
            
            response = requests.get(
                f"{self.base_url}/people/find",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return {
                "email": data.get("email"),
                "telefone": data.get("phone"),
                "cargo_atual": data.get("employment", {}).get("title"),
                "departamento": data.get("employment", {}).get("role"),
                "fonte": "Clearbit",
                "confiabilidade": 0.9 if linkedin_url else 0.7
            }
            
        except requests.RequestException as e:
            logger.error("erro_clearbit", erro=str(e), contact=contact_data.get("nome"))
            raise EnrichmentError(f"Erro na API Clearbit: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica se a API do Clearbit está acessível."""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.status_code == 200
        except:
            return False

class EnrichmentService:
    """Serviço principal de enriquecimento com fallback entre provedores."""
    
    def __init__(self, providers: List[EnrichmentProvider]):
        self.providers = providers
        
        # Configuração do Redis para cache
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.cache_ttl = 604800  # 7 dias em segundos
    
    def _get_from_cache(self, contact_id: str) -> Optional[Dict]:
        """Recupera dados enriquecidos do cache."""
        try:
            cached_data = self.redis_client.get(f"enriched:{contact_id}")
            if cached_data:
                logger.info("cache_hit", contact_id=contact_id)
                return eval(cached_data)
            return None
        except redis.RedisError as e:
            logger.warning("erro_cache", erro=str(e))
            return None
    
    def _save_to_cache(self, contact_id: str, data: Dict) -> None:
        """Salva dados enriquecidos no cache."""
        try:
            self.redis_client.setex(
                f"enriched:{contact_id}",
                self.cache_ttl,
                str(data)
            )
            logger.info("cache_save", contact_id=contact_id)
        except redis.RedisError as e:
            logger.warning("erro_cache_save", erro=str(e))
    
    def enrich_contact(self, contact_data: Dict) -> Dict:
        """
        Enriquece dados do contato usando múltiplos provedores com fallback.
        Implementa cache para evitar chamadas repetidas.
        """
        contact_id = (
            contact_data.get("perfil_linkedin") or 
            f"{contact_data.get('nome')}:{contact_data.get('empresa')}"
        )
        
        # Verifica cache primeiro
        cached_data = self._get_from_cache(contact_id)
        if cached_data:
            return cached_data
        
        enriched_data = {}
        errors = []
        
        # Tenta cada provedor em sequência
        for provider in self.providers:
            if not provider.is_available():
                continue
                
            try:
                enriched_data = provider.enrich_contact(contact_data)
                if enriched_data:
                    enriched_data["data_enriquecimento"] = datetime.now().isoformat()
                    self._save_to_cache(contact_id, enriched_data)
                    return enriched_data
            except EnrichmentError as e:
                errors.append(str(e))
                continue
        
        if errors:
            logger.error(
                "falha_enriquecimento",
                contact=contact_data.get("nome"),
                errors=errors
            )
            
        return contact_data  # Retorna dados originais se nenhum enriquecimento funcionar
