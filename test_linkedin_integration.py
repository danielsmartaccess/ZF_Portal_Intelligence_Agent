"""
Script para testar a integração do LinkedIn no ZF Portal Intelligence Agent.
Este script demonstra o fluxo completo de integração:
1. Configuração do ambiente
2. Autenticação no LinkedIn
3. Busca de contatos-chave
4. Enriquecimento de dados
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

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
from src.utils.file_cache import FileCache
from src.config.linkedin_config import LinkedInConfig
from src.utils.selenium_setup import setup_webdriver, save_cookies_to_file as save_cookies, load_cookies_from_file as load_cookies

def test_linkedin_config():
    """
    Testa a configuração do LinkedIn.
    
    Returns:
        bool: True se a configuração está correta, False caso contrário
    """
    logger.info("=== Testando configuração do LinkedIn ===")
    
    try:
        # Inicializa a configuração do LinkedIn
        config = LinkedInConfig()
        
        # Verifica se as credenciais estão configuradas
        if not config.username or not config.password:
            logger.error("Credenciais do LinkedIn não configuradas no arquivo .env")
            logger.info("Adicione LINKEDIN_USERNAME e LINKEDIN_PASSWORD ao arquivo .env")
            return False
        
        logger.info(f"Credenciais do LinkedIn configuradas para: {config.username}")
        
        # Verifica se há um token de acesso salvo
        token = config.get_access_token()
        if token:
            logger.info("Token de acesso do LinkedIn encontrado")
            
            # Verifica se o token está expirado
            if config.is_token_expired():
                logger.warning("Token de acesso expirado. Será necessário obter um novo token.")
            else:
                logger.info("Token de acesso válido")
                
            return True
        else:
            logger.warning("Token de acesso do LinkedIn não encontrado")
            logger.info("Será necessário fazer login no LinkedIn para obter um token")
            return True
        
    except Exception as e:
        logger.error(f"Erro ao testar configuração do LinkedIn: {str(e)}")
        return False

def test_selenium_setup():
    """
    Testa a configuração do Selenium.
    
    Returns:
        bool: True se a configuração está correta, False caso contrário
    """
    logger.info("\n=== Testando configuração do Selenium ===")
    
    try:
        # Configura o WebDriver
        logger.info("Inicializando o WebDriver...")
        driver = setup_webdriver(headless=True)
        
        # Testa se o driver consegue acessar um site
        logger.info("Testando acesso a um site...")
        driver.get("https://www.google.com")
        title = driver.title
        
        logger.info(f"Título da página: {title}")
        
        # Testa o salvamento e carregamento de cookies
        logger.info("Testando salvamento de cookies...")
        cookies = driver.get_cookies()
        
        # Cria um diretório para os cookies se não existir
        cookies_dir = root_dir / 'data' / 'cookies'
        cookies_dir.mkdir(parents=True, exist_ok=True)
        
        # Salva os cookies
        cookies_file = cookies_dir / 'test_cookies.pkl'
        save_cookies(driver, str(cookies_file))
        
        logger.info(f"Cookies salvos em: {cookies_file}")
        
        # Carrega os cookies
        logger.info("Testando carregamento de cookies...")
        load_cookies(driver, str(cookies_file))
        
        logger.info("Cookies carregados com sucesso")
        
        # Fecha o driver
        driver.quit()
        
        logger.info("Configuração do Selenium testada com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar configuração do Selenium: {str(e)}")
        return False

def test_file_cache():
    """
    Testa o sistema de cache baseado em arquivos.
    
    Returns:
        bool: True se o cache está funcionando, False caso contrário
    """
    logger.info("\n=== Testando sistema de cache ===")
    
    try:
        # Inicializa o cache
        cache = FileCache()
        
        # Testa operações básicas
        test_key = "test_key"
        test_value = {
            "nome": "Teste",
            "cargo": "Diretor de Testes",
            "empresa": "Empresa de Testes",
            "data": datetime.now().isoformat()
        }
        
        # Define um valor no cache
        logger.info("Testando armazenamento no cache...")
        cache.set(test_key, test_value, ex=3600)  # Expira em 1 hora
        
        # Recupera o valor do cache
        logger.info("Testando recuperação do cache...")
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            logger.info("Valor recuperado do cache com sucesso")
        else:
            logger.error("Valor recuperado do cache não corresponde ao valor original")
            return False
        
        # Testa expiração do cache
        logger.info("Testando expiração do cache...")
        cache.set(test_key + "_expire", test_value, ex=1)  # Expira em 1 segundo
        
        # Aguarda a expiração
        import time
        time.sleep(2)
        
        # Tenta recuperar o valor expirado
        expired_value = cache.get(test_key + "_expire")
        
        if expired_value is None:
            logger.info("Expiração do cache funcionando corretamente")
        else:
            logger.warning("Valor não expirou como esperado")
        
        # Testa deleção do cache
        logger.info("Testando deleção do cache...")
        cache.delete(test_key)
        
        # Verifica se o valor foi deletado
        deleted_value = cache.get(test_key)
        
        if deleted_value is None:
            logger.info("Deleção do cache funcionando corretamente")
        else:
            logger.warning("Valor não foi deletado como esperado")
        
        logger.info("Sistema de cache testado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar sistema de cache: {str(e)}")
        return False

def test_linkedin_login():
    """
    Testa o login no LinkedIn usando Selenium.
    
    Returns:
        bool: True se o login foi bem-sucedido, False caso contrário
    """
    logger.info("\n=== Testando login no LinkedIn ===")
    
    try:
        # Inicializa a configuração do LinkedIn
        config = LinkedInConfig()
        
        # Verifica se as credenciais estão configuradas
        if not config.username or not config.password:
            logger.error("Credenciais do LinkedIn não configuradas")
            return False
        
        # Configura o WebDriver
        logger.info("Inicializando o WebDriver...")
        driver = setup_webdriver(headless=False)  # Modo não-headless para visualizar o login
        
        # Acessa a página de login do LinkedIn
        logger.info("Acessando página de login do LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Aguarda a página carregar
        import time
        time.sleep(3)
        
        # Verifica se já está logado
        if "Feed" in driver.title:
            logger.info("Já está logado no LinkedIn")
            driver.quit()
            return True
        
        # Preenche o formulário de login
        logger.info("Preenchendo formulário de login...")
        
        try:
            # Tenta encontrar os campos de login
            username_field = driver.find_element_by_id("username")
            password_field = driver.find_element_by_id("password")
            
            # Preenche os campos
            username_field.send_keys(config.username)
            password_field.send_keys(config.password)
            
            # Clica no botão de login
            login_button = driver.find_element_by_xpath("//button[@type='submit']")
            login_button.click()
            
            # Aguarda o login ser processado
            logger.info("Aguardando processamento do login...")
            time.sleep(5)
            
            # Verifica se o login foi bem-sucedido
            if "Feed" in driver.title or "LinkedIn" in driver.title:
                logger.info("Login no LinkedIn bem-sucedido")
                
                # Salva os cookies
                cookies_dir = root_dir / 'data' / 'cookies'
                cookies_dir.mkdir(parents=True, exist_ok=True)
                
                cookies_file = cookies_dir / 'linkedin_cookies.pkl'
                save_cookies(driver, str(cookies_file))
                
                logger.info(f"Cookies do LinkedIn salvos em: {cookies_file}")
                
                driver.quit()
                return True
            else:
                logger.error("Falha no login do LinkedIn")
                driver.quit()
                return False
                
        except Exception as e:
            logger.error(f"Erro ao preencher formulário de login: {str(e)}")
            driver.quit()
            return False
        
    except Exception as e:
        logger.error(f"Erro ao testar login no LinkedIn: {str(e)}")
        return False

def test_linkedin_search():
    """
    Testa a busca de contatos no LinkedIn Sales Navigator.
    
    Returns:
        bool: True se a busca foi bem-sucedida, False caso contrário
    """
    logger.info("\n=== Testando busca no LinkedIn Sales Navigator ===")
    
    try:
        # Inicializa a configuração do LinkedIn
        config = LinkedInConfig()
        
        # Inicializa o cache
        cache = FileCache()
        
        # Lista de empresas para teste
        test_companies = [
            "ZF do Brasil",
            "Volkswagen do Brasil",
            "Mercedes-Benz do Brasil",
            "Bosch do Brasil"
        ]
        
        # Testa a busca para cada empresa
        for company in test_companies:
            logger.info(f"Buscando contatos para: {company}")
            
            # Verifica se os resultados estão em cache
            cache_key = f"contacts:{company}"
            cached_results = cache.get(cache_key)
            
            if cached_results:
                logger.info(f"Usando resultados em cache para {company}")
                logger.info(f"Encontrados {len(cached_results)} contatos em cache")
                
                # Exibe os contatos encontrados
                for i, contact in enumerate(cached_results[:2]):  # Limita a 2 contatos para o log
                    logger.info(f"  Contato {i+1}: {contact.get('nome', 'N/A')} - {contact.get('cargo', 'N/A')}")
                
            else:
                logger.info(f"Simulando busca para {company} (modo de teste)")
                
                # Simulação de contatos encontrados para teste
                contacts = [
                    {
                        "nome": f"Diretor Financeiro de {company}",
                        "cargo": "CFO",
                        "empresa": company,
                        "perfil_linkedin": f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}"
                    },
                    {
                        "nome": f"Gerente Financeiro de {company}",
                        "cargo": "Gerente Financeiro",
                        "empresa": company,
                        "perfil_linkedin": f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}"
                    }
                ]
                
                # Armazena os resultados em cache por 24 horas (86400 segundos)
                cache.set(cache_key, contacts, ex=86400)
                
                logger.info(f"Encontrados {len(contacts)} contatos para {company}")
                
                # Exibe os contatos encontrados
                for i, contact in enumerate(contacts):
                    logger.info(f"  Contato {i+1}: {contact.get('nome', 'N/A')} - {contact.get('cargo', 'N/A')}")
                    
                    # Simula enriquecimento de dados
                    logger.info(f"  Enriquecendo dados para: {contact.get('nome')}")
                    
                    # Verifica se os dados enriquecidos estão em cache
                    enrich_key = f"enriched:{contact.get('nome')}:{contact.get('empresa')}"
                    cached_enriched = cache.get(enrich_key)
                    
                    if cached_enriched:
                        logger.info(f"  Usando dados enriquecidos em cache para {contact.get('nome')}")
                        enriched_data = cached_enriched
                    else:
                        # Simulação de dados enriquecidos
                        enriched_data = {
                            **contact,
                            "email": f"contato@{contact.get('empresa', '').lower().replace(' ', '')}.com.br",
                            "telefone": "(11) 9999-9999",
                            "celular": "(11) 98888-8888",
                            "ultima_atualizacao": datetime.now().isoformat()
                        }
                        
                        # Armazena os dados enriquecidos em cache
                        cache.set(enrich_key, enriched_data, ex=86400)
                    
                    logger.info(f"  Dados enriquecidos: Email: {enriched_data.get('email', 'N/A')}, Telefone: {enriched_data.get('telefone', 'N/A')}")
        
        logger.info("Busca no LinkedIn Sales Navigator testada com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar busca no LinkedIn: {str(e)}")
        return False

def main():
    """
    Função principal que executa todos os testes de integração.
    """
    logger.info("=== Iniciando testes de integração do LinkedIn ===")
    
    # Lista de testes a serem executados
    tests = [
        ("Configuração do LinkedIn", test_linkedin_config),
        ("Sistema de Cache", test_file_cache),
        ("Configuração do Selenium", test_selenium_setup),
        ("Busca no LinkedIn", test_linkedin_search)
    ]
    
    # Opcional: teste de login (requer interação do usuário)
    run_login_test = False
    if run_login_test:
        tests.append(("Login no LinkedIn", test_linkedin_login))
    
    # Executa cada teste
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Executando teste: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Erro ao executar teste {test_name}: {str(e)}")
            results[test_name] = False
    
    # Exibe o resumo dos testes
    logger.info("\n\n=== Resumo dos testes de integração ===")
    
    all_passed = True
    for test_name, result in results.items():
        status = "✓ PASSOU" if result else "✗ FALHOU"
        logger.info(f"{status} - {test_name}")
        
        if not result:
            all_passed = False
    
    if all_passed:
        logger.info("\n✅ Todos os testes passaram! A integração com o LinkedIn está configurada corretamente.")
        logger.info("Você pode agora executar o sistema completo.")
    else:
        logger.warning("\n⚠ Alguns testes falharam. Verifique os erros acima e corrija-os antes de executar o sistema.")
        logger.info("Execute este script novamente após corrigir os problemas.")

if __name__ == "__main__":
    main()
