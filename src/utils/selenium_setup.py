"""
Módulo para configuração do Selenium WebDriver.
"""
import os
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def setup_webdriver(headless=True):
    """
    Configura e retorna uma instância do WebDriver do Chrome.
    
    Args:
        headless: Se True, executa o navegador em modo headless (sem interface gráfica)
        
    Returns:
        Uma instância do WebDriver do Chrome
    """
    try:
        # Configura as opções do Chrome
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        # Configurações adicionais para melhorar a estabilidade
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-extensions')
        
        # Configura o User-Agent para evitar bloqueios
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Instala e configura o ChromeDriver automaticamente
        service = Service(ChromeDriverManager().install())
        
        # Cria e retorna o WebDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Define um timeout padrão para operações
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        logger.info("WebDriver configurado com sucesso")
        return driver
    
    except Exception as e:
        logger.error(f"Erro ao configurar o WebDriver: {str(e)}")
        raise

def save_cookies_to_file(driver, file_path):
    """
    Salva os cookies do navegador em um arquivo.
    
    Args:
        driver: Instância do WebDriver
        file_path: Caminho para o arquivo onde os cookies serão salvos
    """
    import pickle
    
    try:
        # Cria o diretório se não existir
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Salva os cookies
        pickle.dump(driver.get_cookies(), open(file_path, "wb"))
        logger.info(f"Cookies salvos em {file_path}")
    
    except Exception as e:
        logger.error(f"Erro ao salvar cookies: {str(e)}")

def load_cookies_from_file(driver, file_path):
    """
    Carrega os cookies de um arquivo para o navegador.
    
    Args:
        driver: Instância do WebDriver
        file_path: Caminho para o arquivo de cookies
        
    Returns:
        True se os cookies foram carregados com sucesso, False caso contrário
    """
    import pickle
    
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            logger.warning(f"Arquivo de cookies não encontrado: {file_path}")
            return False
        
        # Carrega os cookies
        cookies = pickle.load(open(file_path, "rb"))
        
        # Adiciona cada cookie ao navegador
        for cookie in cookies:
            # Alguns cookies podem causar erros, então tratamos cada um individualmente
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Erro ao adicionar cookie: {str(e)}")
        
        logger.info(f"Cookies carregados de {file_path}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao carregar cookies: {str(e)}")
        return False
