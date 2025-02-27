"""
Provedor de enriquecimento de dados usando LinkedIn Sales Navigator
"""
from typing import Dict, Optional, List
import requests
import json
import time
from datetime import datetime
import structlog
from ..config.linkedin_config import LinkedInConfig
from .enrichment_service import EnrichmentProvider, EnrichmentError

logger = structlog.get_logger(__name__)

class LinkedInSalesNavigatorProvider(EnrichmentProvider):
    """Provedor de enriquecimento usando LinkedIn Sales Navigator."""
    
    def __init__(self, config: LinkedInConfig):
        self.config = config
        self.base_url = "https://api.linkedin.com/v2"
        
    def enrich_contact(self, contact_data: Dict) -> Dict:
        """
        Enriquece dados do contato usando LinkedIn Sales Navigator.
        
        Args:
            contact_data: Dicionário com dados do contato
                - nome: Nome da pessoa
                - empresa: Nome da empresa
                - cargo: Cargo atual (opcional)
                
        Returns:
            Dict com dados enriquecidos:
                - nome_completo: Nome completo da pessoa
                - cargo_atual: Cargo atual
                - empresa_atual: Empresa atual
                - localizacao: Localização
                - industria: Indústria da empresa
                - tamanho_empresa: Tamanho da empresa
                - linkedin_url: URL do perfil
        """
        try:
            # Busca a empresa
            empresa_info = self._search_company(contact_data.get("empresa"))
            if not empresa_info:
                logger.warning("empresa_nao_encontrada", 
                             empresa=contact_data.get("empresa"))
                return contact_data
            
            # Busca a pessoa na empresa
            pessoa_info = self._search_person(
                nome=contact_data.get("nome"),
                empresa_id=empresa_info.get("id"),
                cargo=contact_data.get("cargo")
            )
            
            if not pessoa_info:
                logger.warning("pessoa_nao_encontrada",
                             nome=contact_data.get("nome"),
                             empresa=contact_data.get("empresa"))
                return contact_data
            
            # Enriquece os dados
            return {
                **contact_data,
                "nome_completo": pessoa_info.get("fullName"),
                "cargo_atual": pessoa_info.get("title"),
                "empresa_atual": empresa_info.get("name"),
                "localizacao": pessoa_info.get("location"),
                "industria": empresa_info.get("industry"),
                "tamanho_empresa": empresa_info.get("companySize"),
                "linkedin_url": f"https://www.linkedin.com/in/{pessoa_info.get('vanityName')}",
                "ultima_atualizacao": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("erro_enriquecimento_linkedin",
                        erro=str(e),
                        contact_data=contact_data)
            raise EnrichmentError(f"Erro ao enriquecer dados via LinkedIn: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica se o serviço do LinkedIn está disponível."""
        try:
            headers = self.config.get_auth_headers()
            response = requests.get(
                f"{self.base_url}/me",
                headers=headers
            )
            return response.status_code == 200
        except:
            return False
            
    def _search_company(self, company_name: str) -> Optional[Dict]:
        """
        Busca informações da empresa no LinkedIn.
        """
        if not company_name:
            return None
            
        headers = self.config.get_auth_headers()
        params = {
            "q": "companiesV2",
            "keywords": company_name,
            "count": 1
        }
        
        response = requests.get(
            f"{self.base_url}/search",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data.get("elements"):
            return None
            
        return data["elements"][0]
        
    def _search_person(self, nome: str, empresa_id: str, cargo: Optional[str] = None) -> Optional[Dict]:
        """
        Busca informações da pessoa no LinkedIn.
        """
        if not nome or not empresa_id:
            return None
            
        headers = self.config.get_auth_headers()
        params = {
            "q": "peopleV2",
            "keywords": nome,
            "filters": [
                f"currentCompany=={empresa_id}"
            ]
        }
        
        if cargo:
            params["filters"].append(f"title=={cargo}")
            
        response = requests.get(
            f"{self.base_url}/search",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        if not data.get("elements"):
            return None
            
        return data["elements"][0]
