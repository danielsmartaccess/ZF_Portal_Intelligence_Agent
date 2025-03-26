"""
Configurações para integração com LinkedIn Sales Navigator
"""
from typing import Dict
import os
import json
import time
import requests
import logging
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Importa o módulo de configuração do Selenium
from ..utils.selenium_setup import setup_webdriver, save_cookies_to_file, load_cookies_from_file
# Importa o módulo de cache baseado em arquivos
from ..utils.file_cache import FileCache

logger = logging.getLogger(__name__)

class LinkedInConfig:
    """
    Gerencia as configurações e autenticação para o LinkedIn Sales Navigator.
    """
    def __init__(self):
        # Carrega as variáveis de ambiente
        load_dotenv()
        
        # Configurações básicas
        self.username = os.getenv('LINKEDIN_USERNAME')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = os.getenv('LINKEDIN_REDIRECT_URI')
        
        # Token de acesso
        self.access_token = None
        self.token_expiry = None
        
        # Diretório para armazenar cookies e tokens
        root_dir = Path(__file__).parent.parent.parent
        self.auth_dir = os.path.join(root_dir, 'auth')
        os.makedirs(self.auth_dir, exist_ok=True)
        
        # Caminhos para arquivos de autenticação
        self.cookies_file = os.path.join(self.auth_dir, 'linkedin_cookies.pkl')
        self.token_file = os.path.join(self.auth_dir, 'linkedin_token.json')
        
        # Inicializa o cache
        self.cache = FileCache()
        
        # Carrega o token salvo, se existir
        self._load_saved_token()

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Retorna os headers de autenticação para as requisições à API
        """
        if not self.access_token or self._is_token_expired():
            self.access_token = self._get_access_token()
            
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }

    def _is_token_expired(self) -> bool:
        """
        Verifica se o token de acesso expirou
        """
        if not self.token_expiry:
            return True
        
        # Considera o token expirado se faltar menos de 5 minutos para expirar
        return time.time() >= (self.token_expiry - 300)

    def _get_access_token(self) -> str:
        """
        Obtém um novo access token usando as credenciais OAuth2 ou login direto
        """
        # Tenta usar OAuth2 se as credenciais estiverem configuradas
        if self.client_id and self.client_secret and self.redirect_uri:
            try:
                return self._get_token_via_oauth()
            except Exception as e:
                logger.error(f"Erro ao obter token via OAuth: {str(e)}")
        
        # Tenta usar o token estático do .env como fallback
        env_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        if env_token:
            logger.info("Usando token de acesso do arquivo .env")
            return env_token
        
        # Se não conseguir obter o token via OAuth ou .env, tenta login via Selenium
        try:
            return self._get_token_via_selenium()
        except Exception as e:
            logger.error(f"Erro ao obter token via Selenium: {str(e)}")
            raise ValueError("Não foi possível obter token de acesso para o LinkedIn")

    def _get_token_via_oauth(self) -> str:
        """
        Obtém um token de acesso usando o fluxo OAuth2
        """
        # TODO: Implementar fluxo completo de OAuth2
        # Por enquanto, apenas verifica se há um token salvo
        if os.path.exists(self.token_file):
            with open(self.token_file, 'r') as f:
                token_data = json.load(f)
                
                # Verifica se o token ainda é válido
                if token_data.get('expires_at', 0) > time.time():
                    logger.info("Usando token OAuth2 salvo")
                    self.token_expiry = token_data.get('expires_at')
                    return token_data.get('access_token')
        
        raise ValueError("Fluxo OAuth2 não implementado completamente")

    def _get_token_via_selenium(self) -> str:
        """
        Obtém um token de acesso fazendo login via Selenium
        """
        if not self.username or not self.password:
            raise ValueError("Credenciais do LinkedIn não configuradas")
        
        logger.info("Iniciando login no LinkedIn via Selenium")
        
        # Configura o WebDriver
        driver = setup_webdriver(headless=True)
        
        try:
            # Tenta carregar cookies salvos
            cookies_loaded = False
            if os.path.exists(self.cookies_file):
                driver.get('https://www.linkedin.com')
                cookies_loaded = load_cookies_from_file(driver, self.cookies_file)
                
                if cookies_loaded:
                    logger.info("Cookies carregados com sucesso")
                    driver.get('https://www.linkedin.com/feed/')
                    
                    # Verifica se ainda está logado
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
                        )
                        logger.info("Sessão ativa encontrada")
                    except:
                        logger.info("Cookies expirados, fazendo login novamente")
                        cookies_loaded = False
            
            # Se não conseguiu usar cookies, faz login normalmente
            if not cookies_loaded:
                # Acessa a página de login
                driver.get('https://www.linkedin.com/login')
                
                # Preenche o formulário de login
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                
                driver.find_element(By.ID, "username").send_keys(self.username)
                driver.find_element(By.ID, "password").send_keys(self.password)
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                
                # Espera o login ser concluído
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".feed-identity-module"))
                )
                
                logger.info("Login realizado com sucesso")
                
                # Salva os cookies para uso futuro
                save_cookies_to_file(driver, self.cookies_file)
            
            # Navega para o Sales Navigator (se disponível)
            try:
                driver.get('https://www.linkedin.com/sales')
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav__me"))
                )
                logger.info("Acesso ao Sales Navigator confirmado")
            except:
                logger.warning("Não foi possível acessar o Sales Navigator, talvez a conta não tenha acesso")
            
            # Extrai o token de acesso do localStorage
            # Nota: Este método pode não funcionar para todos os usuários
            # e depende da implementação atual do LinkedIn
            try:
                token_data = driver.execute_script(
                    "return JSON.parse(localStorage.getItem('voyager-frontend:voyagerToken'))"
                )
                
                if token_data and 'value' in token_data:
                    # Salva o token para uso futuro
                    expires_at = time.time() + 3600  # Assume 1 hora de validade
                    
                    with open(self.token_file, 'w') as f:
                        json.dump({
                            'access_token': token_data['value'],
                            'expires_at': expires_at
                        }, f)
                    
                    self.token_expiry = expires_at
                    logger.info("Token de acesso extraído com sucesso")
                    return token_data['value']
            except Exception as e:
                logger.error(f"Erro ao extrair token: {str(e)}")
            
            # Se não conseguiu extrair o token, usa um token alternativo do .env
            alt_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
            if alt_token:
                logger.info("Usando token alternativo do .env")
                return alt_token
            
            raise ValueError("Não foi possível obter token de acesso")
            
        finally:
            # Fecha o navegador
            driver.quit()

    def _load_saved_token(self):
        """
        Carrega um token salvo do arquivo
        """
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                    
                    self.access_token = token_data.get('access_token')
                    self.token_expiry = token_data.get('expires_at')
                    
                    logger.info("Token carregado do arquivo")
            except Exception as e:
                logger.error(f"Erro ao carregar token do arquivo: {str(e)}")

    def get_sales_navigator_url(self) -> str:
        """
        Retorna a URL base do Sales Navigator
        """
        return "https://www.linkedin.com/sales"

    def test_connection(self) -> bool:
        """
        Testa a conexão com a API do LinkedIn
        """
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                "https://api.linkedin.com/v2/me",
                headers=headers
            )
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {str(e)}")
            return False
