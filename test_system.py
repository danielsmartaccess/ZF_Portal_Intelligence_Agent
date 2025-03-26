"""
Script para testar o sistema completo do ZF Portal Intelligence Agent.
Este script demonstra o fluxo completo do sistema:
1. Importação de dados do CSV
2. Busca de contatos-chave no LinkedIn
3. Enriquecimento de dados dos contatos
4. Preparação para comunicação
"""
import os
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import Session
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
from src.database.models import init_db, Empresa, Contato
from src.data_import.csv_importer import CSVImporter
from src.utils.file_cache import FileCache
from src.config.linkedin_config import LinkedInConfig

class SimplifiedContactFinder:
    """
    Versão simplificada do ContactFinder que usa a configuração do LinkedIn
    e o sistema de cache baseado em arquivos.
    """
    def __init__(self, linkedin_config):
        self.linkedin_config = linkedin_config
        self.cache = FileCache()
        
    def find_key_contacts(self, company_name):
        """
        Busca contatos-chave em uma empresa usando LinkedIn.
        Versão simplificada para teste.
        """
        logger.info(f"Buscando contatos para: {company_name}")
        
        # Verifica se os resultados estão em cache
        cache_key = f"contacts:{company_name}"
        cached_results = self.cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Usando resultados em cache para {company_name}")
            return cached_results
        
        # Simulação de contatos encontrados para teste
        contacts = [
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
        
        # Armazena os resultados em cache por 24 horas (86400 segundos)
        self.cache.set(cache_key, contacts, ex=86400)
        
        return contacts
    
    def enrich_contact_data(self, contact):
        """
        Enriquece os dados do contato com informações adicionais.
        Versão simplificada para teste.
        """
        logger.info(f"Enriquecendo dados para: {contact.get('nome')}")
        
        # Verifica se os resultados estão em cache
        cache_key = f"enriched:{contact.get('nome')}:{contact.get('empresa')}"
        cached_results = self.cache.get(cache_key)
        
        if cached_results:
            logger.info(f"Usando dados enriquecidos em cache para {contact.get('nome')}")
            return cached_results
        
        # Simulação de dados enriquecidos para teste
        enriched_data = {
            **contact,
            "email": f"contato@{contact.get('empresa', '').lower().replace(' ', '')}.com.br",
            "telefone": "(11) 9999-9999",
            "celular": "(11) 98888-8888",
            "ultima_atualizacao": datetime.now().isoformat()
        }
        
        # Armazena os resultados em cache por 24 horas (86400 segundos)
        self.cache.set(cache_key, enriched_data, ex=86400)
        
        return enriched_data

def import_data_from_csv(db_session):
    """
    Importa dados do arquivo CSV para o banco de dados.
    
    Args:
        db_session: Sessão do banco de dados
        
    Returns:
        dict: Estatísticas da importação
    """
    logger.info("=== Etapa 1: Importação de dados do CSV ===")
    
    # Caminho para o arquivo CSV
    csv_path = root_dir / 'data' / 'clientes-haver.csv'
    
    if not csv_path.exists():
        logger.error(f"Arquivo não encontrado: {csv_path}")
        return None
    
    logger.info(f"Importando dados do arquivo: {csv_path}")
    
    try:
        # Cria uma instância do importador CSV
        importer = CSVImporter()
        
        # Modifica os campos esperados para corresponder ao CSV
        # No CSV temos 'stcd1' (CNPJ) e 'fornecedor_name' (Razão Social)
        importer.required_fields = ['stcd1', 'fornecedor_name']
        
        # Sobrescreve o método validate_row para validar os campos do CSV
        def custom_validate_row(self, row, line_number):
            """
            Valida uma linha do CSV específico clientes-haver.csv
            
            Args:
                row: Dicionário com os dados da linha
                line_number: Número da linha no CSV
            """
            # Valida campos obrigatórios
            for field in self.required_fields:
                if field not in row or not row.get(field):
                    raise Exception(
                        f"Campo obrigatório '{field}' ausente ou vazio na linha {line_number}"
                    )
            
            # Valida CNPJ (stcd1)
            cnpj = row['stcd1']
            if not cnpj.isdigit() or len(cnpj) < 8:  # Validação básica
                raise Exception(
                    f"CNPJ inválido na linha {line_number}: {cnpj}"
                )
        
        # Sobrescreve o método process_row para mapear os campos do CSV para os campos do banco
        def custom_process_row(self, row):
            """
            Processa uma linha do CSV específico clientes-haver.csv
            Mapeia os campos do CSV para os campos do banco de dados
            
            Args:
                row: Dicionário com os dados da linha do CSV
                
            Returns:
                Dict: Dados formatados para inserção no banco
            """
            # Mapeia 'stcd1' para 'cnpj' e 'fornecedor_name' para 'razao_social'
            processed = {
                'cnpj': row['stcd1'].strip(),
                'razao_social': row['fornecedor_name'].strip(),
                'website': '',  # Campo não presente no CSV
                'status': 'prospecting',  # Status padrão para novos registros
                'data_cadastro': datetime.now(),
                'ultima_atualizacao': datetime.now()
            }
            return processed
        
        # Substitui os métodos originais pelos customizados
        import types
        importer.validate_row = types.MethodType(custom_validate_row, importer)
        importer.process_row = types.MethodType(custom_process_row, importer)
        
        # Importa os dados
        stats = importer.import_csv(str(csv_path), db_session)
        
        # Exibe estatísticas
        logger.info("Importação concluída. Estatísticas:")
        logger.info(f"Total de registros: {stats['total']}")
        logger.info(f"Registros importados com sucesso: {stats['success']}")
        logger.info(f"Registros duplicados: {stats['duplicates']}")
        logger.info(f"Registros com erro: {stats['errors']}")
        
        return stats
    
    except Exception as e:
        logger.error(f"Erro durante a importação: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def find_key_contacts(db_session, contact_finder):
    """
    Busca contatos-chave para as empresas no banco de dados.
    
    Args:
        db_session: Sessão do banco de dados
        contact_finder: Instância do SimplifiedContactFinder
        
    Returns:
        dict: Estatísticas da busca de contatos
    """
    logger.info("\n=== Etapa 2: Busca de contatos-chave no LinkedIn ===")
    
    try:
        # Consulta as empresas no banco de dados
        empresas = db_session.query(Empresa).all()
        
        if not empresas:
            logger.warning("Nenhuma empresa encontrada no banco de dados.")
            return None
        
        logger.info(f"Encontradas {len(empresas)} empresas no banco de dados.")
        
        # Estatísticas
        stats = {
            'total_empresas': len(empresas),
            'empresas_processadas': 0,
            'contatos_encontrados': 0,
            'contatos_enriquecidos': 0,
            'erros': 0
        }
        
        # Processa cada empresa (limitado a 5 para teste)
        max_empresas = min(5, len(empresas))
        for i, empresa in enumerate(empresas[:max_empresas]):
            logger.info(f"Processando empresa {i+1}/{max_empresas}: {empresa.razao_social}")
            
            try:
                # Busca contatos-chave para a empresa
                contacts = contact_finder.find_key_contacts(empresa.razao_social)
                
                if contacts:
                    logger.info(f"Encontrados {len(contacts)} contatos para {empresa.razao_social}")
                    stats['contatos_encontrados'] += len(contacts)
                    
                    # Processa cada contato encontrado
                    for j, contact_data in enumerate(contacts):
                        logger.info(f"  Contato {j+1}: {contact_data.get('nome', 'N/A')} - {contact_data.get('cargo', 'N/A')}")
                        
                        # Tenta enriquecer os dados do contato
                        try:
                            enriched_data = contact_finder.enrich_contact_data(contact_data)
                            logger.info(f"  Dados enriquecidos: Email: {enriched_data.get('email', 'N/A')}, Telefone: {enriched_data.get('telefone', 'N/A')}")
                            stats['contatos_enriquecidos'] += 1
                            
                            # Salva o contato no banco de dados
                            contato = Contato(
                                nome=enriched_data.get('nome', ''),
                                cargo=enriched_data.get('cargo', ''),
                                email=enriched_data.get('email', ''),
                                telefone=enriched_data.get('telefone', ''),
                                celular=enriched_data.get('celular', ''),
                                linkedin_url=enriched_data.get('perfil_linkedin', ''),
                                empresa_id=empresa.id,
                                status='prospecting',
                                data_cadastro=datetime.now(),
                                ultima_atualizacao=datetime.now()
                            )
                            
                            db_session.add(contato)
                            db_session.commit()
                            
                        except Exception as e:
                            logger.error(f"  Erro ao enriquecer dados: {str(e)}")
                            stats['erros'] += 1
                else:
                    logger.warning(f"Nenhum contato encontrado para {empresa.razao_social}")
                
                stats['empresas_processadas'] += 1
                    
            except Exception as e:
                logger.error(f"Erro ao buscar contatos para {empresa.razao_social}: {str(e)}")
                stats['erros'] += 1
        
        return stats
    
    except Exception as e:
        logger.error(f"Erro durante a busca de contatos: {str(e)}")
        return None

def prepare_communication(db_session):
    """
    Prepara a comunicação com os contatos encontrados.
    
    Args:
        db_session: Sessão do banco de dados
        
    Returns:
        dict: Estatísticas da preparação para comunicação
    """
    logger.info("\n=== Etapa 3: Preparação para comunicação ===")
    
    try:
        # Consulta os contatos no banco de dados
        contatos = db_session.query(Contato).filter(Contato.status == 'prospecting').all()
        
        if not contatos:
            logger.warning("Nenhum contato encontrado para comunicação.")
            return None
        
        logger.info(f"Encontrados {len(contatos)} contatos para comunicação.")
        
        # Estatísticas
        stats = {
            'total_contatos': len(contatos),
            'contatos_processados': 0,
            'mensagens_preparadas': 0,
            'erros': 0
        }
        
        # Processa cada contato (limitado a 5 para teste)
        max_contatos = min(5, len(contatos))
        for i, contato in enumerate(contatos[:max_contatos]):
            logger.info(f"Processando contato {i+1}/{max_contatos}: {contato.nome}")
            
            try:
                # Busca a empresa do contato
                empresa = db_session.query(Empresa).filter(Empresa.id == contato.empresa_id).first()
                
                if not empresa:
                    logger.warning(f"Empresa não encontrada para o contato {contato.nome}")
                    stats['erros'] += 1
                    continue
                
                # Prepara a mensagem personalizada
                mensagem = f"""
Olá {contato.nome},

Espero que esteja bem. Sou Daniel Steinbruch, Diretor de Antecipações da ZF do Brasil.

Notei que a {empresa.razao_social} é uma fornecedora importante para nós e gostaria de apresentar o Portal de Antecipações da ZF, uma plataforma que permite aos nossos fornecedores antecipar seus recebíveis com taxas muito competitivas.

Podemos conversar sobre como isso pode beneficiar sua empresa?

Atenciosamente,
Daniel Steinbruch
Diretor de Antecipações
ZF do Brasil
                """
                
                logger.info(f"  Mensagem personalizada preparada para {contato.nome}")
                logger.info(f"  Será enviada para: {contato.email}")
                
                # Atualiza o status do contato
                contato.status = 'message_prepared'
                contato.ultima_atualizacao = datetime.now()
                db_session.commit()
                
                stats['mensagens_preparadas'] += 1
                stats['contatos_processados'] += 1
                
            except Exception as e:
                logger.error(f"Erro ao preparar comunicação para {contato.nome}: {str(e)}")
                stats['erros'] += 1
        
        return stats
    
    except Exception as e:
        logger.error(f"Erro durante a preparação para comunicação: {str(e)}")
        return None

def main():
    """
    Função principal que executa o fluxo completo do sistema.
    """
    logger.info("=== Iniciando teste do sistema completo ===")
    
    # Inicializa o banco de dados
    database_path = 'sqlite:///' + str(root_dir / 'database.db')
    SessionLocal = init_db(database_path)
    
    # Cria uma sessão do banco de dados
    db_session = SessionLocal()
    
    try:
        # Etapa 1: Importação de dados do CSV
        import_stats = import_data_from_csv(db_session)
        
        if not import_stats:
            logger.error("Falha na importação de dados. Abortando teste.")
            return
        
        # Etapa 2: Busca de contatos-chave no LinkedIn
        # Inicializa a configuração do LinkedIn
        linkedin_config = LinkedInConfig()
        
        # Inicializa o SimplifiedContactFinder
        contact_finder = SimplifiedContactFinder(linkedin_config)
        
        # Busca contatos-chave
        contact_stats = find_key_contacts(db_session, contact_finder)
        
        if not contact_stats:
            logger.error("Falha na busca de contatos. Abortando teste.")
            return
        
        # Etapa 3: Preparação para comunicação
        communication_stats = prepare_communication(db_session)
        
        # Resumo do teste
        logger.info("\n=== Resumo do teste do sistema ===")
        logger.info("Etapa 1: Importação de dados")
        logger.info(f"  Total de registros: {import_stats['total']}")
        logger.info(f"  Registros importados com sucesso: {import_stats['success']}")
        
        logger.info("Etapa 2: Busca de contatos-chave")
        logger.info(f"  Empresas processadas: {contact_stats['empresas_processadas']}/{contact_stats['total_empresas']}")
        logger.info(f"  Contatos encontrados: {contact_stats['contatos_encontrados']}")
        logger.info(f"  Contatos enriquecidos: {contact_stats['contatos_enriquecidos']}")
        
        if communication_stats:
            logger.info("Etapa 3: Preparação para comunicação")
            logger.info(f"  Contatos processados: {communication_stats['contatos_processados']}/{communication_stats['total_contatos']}")
            logger.info(f"  Mensagens preparadas: {communication_stats['mensagens_preparadas']}")
        
        logger.info("\n✅ Teste do sistema concluído com sucesso!")
        
    except Exception as e:
        logger.error(f"Erro durante o teste do sistema: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db_session.close()

if __name__ == "__main__":
    main()
