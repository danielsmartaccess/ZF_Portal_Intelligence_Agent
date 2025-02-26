from data_enrichment.enrichment_service import (
    EnrichmentService,
    LushaProvider,
    ClearbitProvider
)
from dotenv import load_dotenv
import os

def test_enrichment():
    # Carrega variáveis de ambiente
    load_dotenv()
    
    # Inicializa providers
    lusha = LushaProvider(api_key=os.getenv("LUSHA_API_KEY"))
    clearbit = ClearbitProvider(api_key=os.getenv("CLEARBIT_API_KEY"))
    
    # Cria serviço de enriquecimento com ambos providers
    enrichment_service = EnrichmentService([lusha, clearbit])
    
    # Dados de teste
    contact_data = {
        "nome": "João Silva",
        "empresa": "TechCorp",
        "perfil_linkedin": "https://linkedin.com/in/joaosilva"
    }
    
    # Testa enriquecimento
    enriched_data = enrichment_service.enrich_contact(contact_data)
    print("\nDados Enriquecidos:")
    for key, value in enriched_data.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_enrichment()
