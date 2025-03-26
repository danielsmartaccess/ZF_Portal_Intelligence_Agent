"""
Script para testar a configuração completa do ambiente.
Este script verifica se todas as dependências estão instaladas corretamente
e se as credenciais do LinkedIn estão configuradas adequadamente.
"""
import os
import sys
import logging
import importlib
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona o diretório raiz ao path para importar módulos do projeto
root_dir = Path(__file__).resolve().parent
sys.path.append(str(root_dir))

def check_dependency(module_name, package_name=None):
    """
    Verifica se uma dependência está instalada.
    
    Args:
        module_name: Nome do módulo a ser importado
        package_name: Nome do pacote pip (se diferente do module_name)
    
    Returns:
        bool: True se a dependência está instalada, False caso contrário
    """
    if package_name is None:
        package_name = module_name
        
    try:
        importlib.import_module(module_name)
        logger.info(f"✓ {package_name} está instalado")
        return True
    except ImportError:
        logger.error(f"✗ {package_name} não está instalado")
        return False

def check_file_cache():
    """
    Verifica se o sistema de cache baseado em arquivos está funcionando.
    
    Returns:
        bool: True se o cache está funcionando, False caso contrário
    """
    try:
        from src.utils.file_cache import FileCache
        
        cache = FileCache()
        test_key = "test_key"
        test_value = "test_value"
        
        # Testa as operações básicas do cache
        cache.set(test_key, test_value)
        retrieved_value = cache.get(test_key)
        cache.delete(test_key)
        
        if retrieved_value == test_value:
            logger.info("✓ Sistema de cache baseado em arquivos está funcionando")
            return True
        else:
            logger.error("✗ Sistema de cache baseado em arquivos não está funcionando corretamente")
            return False
    except Exception as e:
        logger.error(f"✗ Erro ao testar o sistema de cache: {str(e)}")
        return False

def check_selenium_setup():
    """
    Verifica se o Selenium está configurado corretamente.
    
    Returns:
        bool: True se o Selenium está configurado, False caso contrário
    """
    try:
        from src.utils.selenium_setup import setup_webdriver
        
        logger.info("Testando configuração do Selenium...")
        driver = setup_webdriver(headless=True)
        
        # Testa se o driver consegue acessar um site
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        
        logger.info(f"✓ Selenium está configurado corretamente (acessou: {title})")
        return True
    except Exception as e:
        logger.error(f"✗ Erro na configuração do Selenium: {str(e)}")
        return False

def check_linkedin_config():
    """
    Verifica se as credenciais do LinkedIn estão configuradas.
    
    Returns:
        bool: True se as credenciais estão configuradas, False caso contrário
    """
    try:
        from src.config.linkedin_config import LinkedInConfig
        
        config = LinkedInConfig()
        
        # Verifica se as credenciais básicas estão configuradas
        if not config.username or not config.password:
            logger.error("✗ Credenciais do LinkedIn não configuradas")
            return False
        
        logger.info(f"✓ Credenciais do LinkedIn configuradas para: {config.username}")
        
        # Testa a conexão com o LinkedIn (opcional)
        try:
            logger.info("Testando conexão com o LinkedIn...")
            if config.test_connection():
                logger.info("✓ Conexão com o LinkedIn estabelecida com sucesso")
            else:
                logger.warning("⚠ Não foi possível estabelecer conexão com o LinkedIn")
        except Exception as e:
            logger.warning(f"⚠ Erro ao testar conexão com o LinkedIn: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Erro ao verificar configuração do LinkedIn: {str(e)}")
        return False

def check_database():
    """
    Verifica se o banco de dados está configurado corretamente.
    
    Returns:
        bool: True se o banco de dados está configurado, False caso contrário
    """
    try:
        from src.database.models import init_db, Empresa
        
        # Inicializa o banco de dados
        database_path = 'sqlite:///' + str(root_dir / 'database.db')
        SessionLocal = init_db(database_path)
        
        # Cria uma sessão do banco de dados
        db_session = SessionLocal()
        
        # Verifica se consegue consultar a tabela de empresas
        empresas_count = db_session.query(Empresa).count()
        
        db_session.close()
        
        logger.info(f"✓ Banco de dados configurado corretamente ({empresas_count} empresas encontradas)")
        return True
    except Exception as e:
        logger.error(f"✗ Erro na configuração do banco de dados: {str(e)}")
        return False

def main():
    """
    Função principal que verifica a configuração completa do ambiente.
    """
    logger.info("=== Verificando configuração do ambiente ===")
    
    # Verifica as dependências
    dependencies = [
        ("selenium", None),
        ("requests", None),
        ("dotenv", "python-dotenv"),
        ("sqlalchemy", None),
        ("pathlib", None),
        ("json", None),
        ("time", None),
        ("logging", None),
        ("os", None),
        ("sys", None),
    ]
    
    all_dependencies_installed = True
    for module_name, package_name in dependencies:
        if not check_dependency(module_name, package_name):
            all_dependencies_installed = False
    
    # Verifica a estrutura de diretórios
    required_dirs = [
        "src/config",
        "src/database",
        "src/data_import",
        "src/data_enrichment",
        "src/utils",
        "data"
    ]
    
    all_dirs_exist = True
    for dir_path in required_dirs:
        full_path = os.path.join(root_dir, dir_path)
        if os.path.exists(full_path):
            logger.info(f"✓ Diretório {dir_path} existe")
        else:
            logger.error(f"✗ Diretório {dir_path} não existe")
            all_dirs_exist = False
    
    # Verifica o arquivo .env
    env_file = os.path.join(root_dir, ".env")
    if os.path.exists(env_file):
        logger.info("✓ Arquivo .env encontrado")
    else:
        logger.error("✗ Arquivo .env não encontrado")
        logger.info("Criando arquivo .env de exemplo...")
        
        with open(env_file, "w") as f:
            f.write("""# Configurações do LinkedIn
LINKEDIN_USERNAME=seu_email@exemplo.com
LINKEDIN_PASSWORD=sua_senha
LINKEDIN_ACCESS_TOKEN=seu_token_de_acesso

# Configurações do banco de dados
DATABASE_URL=sqlite:///database.db

# Configurações de APIs externas
LUSHA_API_KEY=sua_chave_api_lusha
CLEARBIT_API_KEY=sua_chave_api_clearbit
""")
        
        logger.info("✓ Arquivo .env de exemplo criado")
    
    # Verifica o sistema de cache
    cache_working = check_file_cache()
    
    # Verifica a configuração do Selenium
    selenium_working = check_selenium_setup()
    
    # Verifica a configuração do LinkedIn
    linkedin_configured = check_linkedin_config()
    
    # Verifica a configuração do banco de dados
    database_configured = check_database()
    
    # Resumo da verificação
    logger.info("\n=== Resumo da verificação do ambiente ===")
    logger.info(f"Dependências instaladas: {'✓' if all_dependencies_installed else '✗'}")
    logger.info(f"Estrutura de diretórios: {'✓' if all_dirs_exist else '✗'}")
    logger.info(f"Sistema de cache: {'✓' if cache_working else '✗'}")
    logger.info(f"Configuração do Selenium: {'✓' if selenium_working else '✗'}")
    logger.info(f"Configuração do LinkedIn: {'✓' if linkedin_configured else '✗'}")
    logger.info(f"Configuração do banco de dados: {'✓' if database_configured else '✗'}")
    
    # Verifica se tudo está configurado corretamente
    if (all_dependencies_installed and all_dirs_exist and cache_working and 
        selenium_working and linkedin_configured and database_configured):
        logger.info("\n✅ Ambiente configurado com sucesso!")
        logger.info("Você pode executar o sistema completo com o comando:")
        logger.info("python test_system.py")
    else:
        logger.warning("\n⚠ Algumas configurações precisam ser ajustadas.")
        logger.info("Verifique os erros acima e corrija-os antes de executar o sistema.")

if __name__ == "__main__":
    main()
