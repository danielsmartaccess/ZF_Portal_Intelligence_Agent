"""
Script para testar a funcionalidade de busca de contatos no LinkedIn.
Este script demonstra como o sistema busca contatos-chave nas empresas
importadas do arquivo CSV, usando uma abordagem simplificada sem Redis.
"""
import os
import sys
import logging
import requests
from pathlib import Path
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao path para importar módulos do projeto
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

# Importa os módulos necessários
from src.database.models import init_db, Empresa

class SimplifiedContactFinder:
    """
    Versão simplificada do ContactFinder que não depende do Redis
    e usa diretamente o Selenium para buscar contatos no LinkedIn.
    """
    def __init__(self, credentials):
        self.username = credentials.get('username')
        self.password = credentials.get('password')
        
        # Configuração do Selenium para scraping
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
    def find_key_contacts(self, company_name):
        """
        Busca contatos-chave em uma empresa usando LinkedIn.
        Versão simplificada para teste.
        """
        logger.info(f"Buscando contatos para: {company_name}")
        
        # Nesta versão simplificada, apenas simulamos a busca
        # Em um ambiente real, aqui usaríamos o Selenium para acessar o LinkedIn
        
        # Simulação de contatos encontrados para teste
        return [
            {
                "nome": f"Diretor Financeiro de {company_name}",
                "cargo": "CFO",
                "empresa": company_name,
                "perfil_linkedin": f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"
            },
            {
                "nome": f"Gerente Financeiro de {company_name}",
                "cargo": "Gerente Financeiro",
                "empresa": company_name,
                "perfil_linkedin": f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"
            }
        ]
    
    def enrich_contact_data(self, contact):
        """
        Enriquece os dados do contato com informações adicionais.
        Versão simplificada para teste.
        """
        logger.info(f"Enriquecendo dados para: {contact.get('nome')}")
        
        # Simulação de dados enriquecidos para teste
        return {
            **contact,
            "email": f"contato@{contact.get('empresa', '').lower().replace(' ', '')}.com.br",
            "telefone": "(11) 9999-9999",
            "celular": "(11) 98888-8888",
            "ultima_atualizacao": datetime.now().isoformat()
        }

def main():
    """
    Função principal que testa a busca de contatos no LinkedIn.
    
    Passos:
    1. Inicializa a conexão com o banco de dados
    2. Consulta as empresas importadas
    3. Inicializa o SimplifiedContactFinder
    4. Busca contatos-chave para cada empresa
    """
    # Verifica se as credenciais do LinkedIn estão configuradas
    linkedin_username = os.getenv('LINKEDIN_USERNAME')
    linkedin_password = os.getenv('LINKEDIN_PASSWORD')
    
    if not linkedin_username or not linkedin_password:
        logger.error("Credenciais do LinkedIn não configuradas. Verifique o arquivo .env")
        return
    
    logger.info(f"Usando credenciais do LinkedIn: {linkedin_username}")
    
    # Inicializa o banco de dados
    database_path = 'sqlite:///' + str(root_dir / 'database.db')
    SessionLocal = init_db(database_path)
    
    # Cria uma sessão do banco de dados
    db_session = SessionLocal()
    
    try:
        # Consulta as empresas no banco de dados
        empresas = db_session.query(Empresa).all()
        
        if not empresas:
            logger.warning("Nenhuma empresa encontrada no banco de dados.")
            logger.info("Execute primeiro o script de importação: python src/data_import/import_clientes_haver.py")
            return
        
        logger.info(f"Encontradas {len(empresas)} empresas no banco de dados.")
        
        # Inicializa o SimplifiedContactFinder
        contact_finder = SimplifiedContactFinder({
            'username': linkedin_username,
            'password': linkedin_password
        })
        
        # Processa cada empresa (limitado a 3 para teste)
        max_empresas = min(3, len(empresas))
        for i, empresa in enumerate(empresas[:max_empresas]):
            logger.info(f"Processando empresa {i+1}/{max_empresas}: {empresa.razao_social}")
            
            try:
                # Busca contatos-chave para a empresa
                contacts = contact_finder.find_key_contacts(empresa.razao_social)
                
                if contacts:
                    logger.info(f"Encontrados {len(contacts)} contatos para {empresa.razao_social}")
                    
                    # Exibe informações básicas dos contatos encontrados
                    for j, contact in enumerate(contacts):
                        logger.info(f"  Contato {j+1}: {contact.get('nome', 'N/A')} - {contact.get('cargo', 'N/A')}")
                        
                        # Tenta enriquecer os dados do contato
                        try:
                            enriched_contact = contact_finder.enrich_contact_data(contact)
                            logger.info(f"  Dados enriquecidos: Email: {enriched_contact.get('email', 'N/A')}, Telefone: {enriched_contact.get('telefone', 'N/A')}")
                        except Exception as e:
                            logger.error(f"  Erro ao enriquecer dados: {str(e)}")
                else:
                    logger.warning(f"Nenhum contato encontrado para {empresa.razao_social}")
                    
            except Exception as e:
                logger.error(f"Erro ao buscar contatos para {empresa.razao_social}: {str(e)}")
        
        logger.info("Teste concluído com sucesso!")
        logger.info("Nota: Esta é uma versão simplificada que simula a busca no LinkedIn.")
        logger.info("Em um ambiente de produção, seria necessário configurar:")
        logger.info("1. Um servidor Redis para cache")
        logger.info("2. Credenciais válidas para a API do LinkedIn Sales Navigator")
        logger.info("3. Webdriver configurado corretamente para o Selenium")
        
    except Exception as e:
        logger.error(f"Erro durante a execução do teste: {str(e)}")
    finally:
        db_session.close()

if __name__ == "__main__":
    main()
