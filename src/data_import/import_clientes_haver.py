"""
Script para importar dados de clientes do arquivo CSV para o banco de dados.
Este script demonstra como usar o CSVImporter para processar arquivos CSV e 
inserir os dados no banco de dados SQLite.
"""
import os
import sys
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

# Adiciona o diretório raiz ao path para importar módulos do projeto
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

# Importa os módulos necessários
from src.data_import.csv_importer import CSVImporter
from src.database.models import init_db, Empresa

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Função principal que importa os dados do CSV para o banco de dados.
    
    Passos:
    1. Inicializa a conexão com o banco de dados
    2. Cria uma instância do CSVImporter
    3. Define o caminho para o arquivo CSV
    4. Importa os dados para o banco
    5. Exibe estatísticas da importação
    """
    # Caminho para o arquivo CSV
    csv_path = root_dir / 'data' / 'clientes-haver.csv'
    
    if not csv_path.exists():
        logger.error(f"Arquivo não encontrado: {csv_path}")
        return
    
    logger.info(f"Iniciando importação do arquivo: {csv_path}")
    
    # Inicializa o banco de dados
    database_path = 'sqlite:///' + str(root_dir / 'database.db')
    SessionLocal = init_db(database_path)
    
    # Cria uma sessão do banco de dados
    db_session = SessionLocal()
    
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
                    raise CSVValidationError(
                        f"Campo obrigatório '{field}' ausente ou vazio na linha {line_number}"
                    )
            
            # Valida CNPJ (stcd1)
            cnpj = row['stcd1']
            if not cnpj.isdigit() or len(cnpj) < 8:  # Validação básica
                raise CSVValidationError(
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
        from src.data_import.csv_importer import CSVValidationError
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
        
    except Exception as e:
        logger.error(f"Erro durante a importação: {str(e)}")
    finally:
        db_session.close()

if __name__ == "__main__":
    main()
