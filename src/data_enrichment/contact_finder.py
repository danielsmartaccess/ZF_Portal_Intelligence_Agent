"""
Módulo responsável por identificar e enriquecer dados de contatos-chave usando LinkedIn Sales Navigator.
Inclui sistema de cache e tratamento avançado de erros.
"""
from typing import Dict, List, Optional
import requests
from datetime import datetime, timedelta
import redis
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from ..config.linkedin_config import LinkedInConfig

# Configuração do logger
logger = logging.getLogger(__name__)

class LinkedInError(Exception):
    """Classe base para erros específicos do LinkedIn."""
    pass

class RateLimitError(LinkedInError):
    """Erro quando atingimos limite de requisições."""
    pass

class AuthenticationError(LinkedInError):
    """Erro de autenticação com LinkedIn."""
    pass

class ContactFinder:
    def __init__(self, linkedin_credentials: Dict[str, str]):
        self.linkedin_config = LinkedInConfig()
        self.base_url = "https://api.linkedin.com/v2/salesNavigator"
        
        # Configuração do Redis para cache
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        self.cache_ttl = 86400  # 24 horas em segundos
        
        # Configuração do Selenium para scraping avançado
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        
    def _get_from_cache(self, key: str) -> Optional[List[Dict]]:
        """Recupera dados do cache."""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.info(f"Cache hit for key: {key}")
                return eval(cached_data)  # Converte string para lista de dicionários
            return None
        except redis.RedisError as e:
            logger.warning(f"Erro ao acessar cache: {str(e)}")
            return None

    def _save_to_cache(self, key: str, data: List[Dict]) -> None:
        """Salva dados no cache."""
        try:
            self.redis_client.setex(key, self.cache_ttl, str(data))
            logger.info(f"Dados salvos no cache para key: {key}")
        except redis.RedisError as e:
            logger.warning(f"Erro ao salvar no cache: {str(e)}")

    def _handle_linkedin_error(self, response: requests.Response) -> None:
        """Trata erros da API do LinkedIn."""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            raise RateLimitError(f"Rate limit atingido. Tente novamente em {retry_after} segundos.")
        elif response.status_code == 401:
            raise AuthenticationError("Erro de autenticação com LinkedIn")
        else:
            response.raise_for_status()

    def _scrape_contact_details(self, profile_url: str) -> Dict:
        """Realiza scraping avançado do perfil do LinkedIn."""
        driver = webdriver.Chrome(options=self.chrome_options)
        try:
            driver.get(profile_url)
            wait = WebDriverWait(driver, 10)
            
            # Espera elementos carregarem
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "profile-info")))
            
            # Extrai informações detalhadas
            details = {
                'email': self._extract_email(driver),
                'phone': self._extract_phone(driver),
                'experience': self._extract_experience(driver),
                'education': self._extract_education(driver)
            }
            
            return details
        except TimeoutException:
            logger.error(f"Timeout ao carregar perfil: {profile_url}")
            return {}
        except Exception as e:
            logger.error(f"Erro no scraping: {str(e)}")
            return {}
        finally:
            driver.quit()

    def find_key_contacts(self, company_name: str) -> List[Dict]:
        """
        Busca contatos-chave em uma empresa usando Sales Navigator com cache e tratamento de erros.
        """
        cache_key = f"contacts:{company_name}"
        
        # Tenta recuperar do cache primeiro
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            return cached_results

        target_positions = [
            "CFO", "Chief Financial Officer",
            "Gerente Financeiro", "Financial Manager",
            "Tesoureiro", "Treasurer",
            "Gerente de Tesouraria", "Treasury Manager"
        ]
        
        contacts = []
        headers = self.linkedin_config.get_auth_headers()
        
        for position in target_positions:
            try:
                params = {
                    "query": position,
                    "company": company_name,
                    "location": "Brasil"
                }
                
                response = requests.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params
                )
                
                self._handle_linkedin_error(response)
                data = response.json()
                
                if 'elements' in data:
                    for element in data['elements']:
                        contact = {
                            'nome': f"{element.get('firstName', '')} {element.get('lastName', '')}",
                            'cargo': element.get('title', ''),
                            'empresa': element.get('company', ''),
                            'perfil_linkedin': element.get('linkedinProfile', ''),
                            'data_captura': datetime.now().isoformat()
                        }
                        
                        # Adiciona detalhes via scraping se perfil disponível
                        if contact['perfil_linkedin']:
                            details = self._scrape_contact_details(contact['perfil_linkedin'])
                            contact.update(details)
                        
                        contacts.append(contact)
                
                # Respeita rate limiting
                time.sleep(1)
                
            except RateLimitError as e:
                logger.error(f"Rate limit atingido: {str(e)}")
                time.sleep(int(e.args[0].split()[6]))  # Espera o tempo sugerido
                continue
            except AuthenticationError as e:
                logger.error(f"Erro de autenticação: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"Erro ao buscar contatos para posição {position}: {str(e)}")
                continue
        
        # Salva resultados no cache
        if contacts:
            self._save_to_cache(cache_key, contacts)
        
        return contacts

    def _extract_email(self, driver: webdriver.Chrome) -> str:
        """Extrai email do perfil."""
        try:
            email_element = driver.find_element(By.CLASS_NAME, "email-address")
            return email_element.text
        except NoSuchElementException:
            return ""

    def _extract_phone(self, driver: webdriver.Chrome) -> str:
        """Extrai telefone do perfil."""
        try:
            phone_element = driver.find_element(By.CLASS_NAME, "phone-number")
            return phone_element.text
        except NoSuchElementException:
            return ""

    def _extract_experience(self, driver: webdriver.Chrome) -> List[Dict]:
        """Extrai experiência profissional."""
        try:
            experience_elements = driver.find_elements(By.CLASS_NAME, "experience-item")
            experiences = []
            for element in experience_elements:
                exp = {
                    'cargo': element.find_element(By.CLASS_NAME, "title").text,
                    'empresa': element.find_element(By.CLASS_NAME, "company").text,
                    'periodo': element.find_element(By.CLASS_NAME, "date-range").text
                }
                experiences.append(exp)
            return experiences
        except NoSuchElementException:
            return []

    def _extract_education(self, driver: webdriver.Chrome) -> List[Dict]:
        """Extrai informações educacionais."""
        try:
            education_elements = driver.find_elements(By.CLASS_NAME, "education-item")
            education = []
            for element in education_elements:
                edu = {
                    'instituicao': element.find_element(By.CLASS_NAME, "school-name").text,
                    'curso': element.find_element(By.CLASS_NAME, "degree-name").text,
                    'periodo': element.find_element(By.CLASS_NAME, "date-range").text
                }
                education.append(edu)
            return education
        except NoSuchElementException:
            return []

    def enrich_contact_data(self, contact: Dict) -> Dict:
        """
        Enriquece os dados do contato com informações adicionais do LinkedIn.
        """
        if not contact.get('perfil_linkedin'):
            return contact
            
        try:
            headers = self.linkedin_config.get_auth_headers()
            profile_id = contact['perfil_linkedin'].split('/')[-1]
            
            response = requests.get(
                f"{self.base_url}/people/{profile_id}",
                headers=headers
            )
            self._handle_linkedin_error(response)
            profile_data = response.json()
            
            # Enriquece o contato com dados adicionais
            contact.update({
                'email': profile_data.get('email', ''),
                'telefone': profile_data.get('phone', ''),
                'localizacao': profile_data.get('location', ''),
                'experiencia': profile_data.get('experience', []),
                'educacao': profile_data.get('education', []),
                'ultima_atualizacao': datetime.now().isoformat()
            })
            
        except RateLimitError as e:
            logger.error(f"Rate limit atingido: {str(e)}")
            time.sleep(int(e.args[0].split()[6]))  # Espera o tempo sugerido
        except AuthenticationError as e:
            logger.error(f"Erro de autenticação: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enriquecer dados do contato {contact['nome']}: {str(e)}")
            
        return contact

    def send_inmail(self, contact: Dict, subject: str, message: str) -> bool:
        """
        Envia uma mensagem InMail para o contato via LinkedIn Sales Navigator.
        """
        if not contact.get('perfil_linkedin'):
            return False
            
        try:
            headers = self.linkedin_config.get_auth_headers()
            profile_id = contact['perfil_linkedin'].split('/')[-1]
            
            payload = {
                "recipients": [f"urn:li:person:{profile_id}"],
                "subject": subject,
                "body": message
            }
            
            response = requests.post(
                f"{self.base_url}/messaging/conversations",
                headers=headers,
                json=payload
            )
            self._handle_linkedin_error(response)
            
            return True
            
        except RateLimitError as e:
            logger.error(f"Rate limit atingido: {str(e)}")
            time.sleep(int(e.args[0].split()[6]))  # Espera o tempo sugerido
            return False
        except AuthenticationError as e:
            logger.error(f"Erro de autenticação: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar InMail para {contact['nome']}: {str(e)}")
            return False
