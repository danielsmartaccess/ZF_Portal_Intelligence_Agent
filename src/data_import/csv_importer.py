"""
Módulo responsável pela importação de dados de empresas via CSV.
"""
import csv
import logging
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database.models import Empresa

logger = logging.getLogger(__name__)

class CSVValidationError(Exception):
    """Exceção para erros de validação do CSV"""
    pass

class CSVImporter:
    """
    Classe responsável por importar dados de empresas a partir de arquivos CSV.
    
    Atributos:
        required_fields (List[str]): Campos obrigatórios no CSV
        optional_fields (List[str]): Campos opcionais no CSV
    """
    
    def __init__(self):
        self.required_fields = ['cnpj', 'razao_social']
        self.optional_fields = ['website', 'status']
        
    def validate_cnpj(self, cnpj: str) -> bool:
        """
        Valida o formato do CNPJ.
        
        Args:
            cnpj: String contendo o CNPJ
            
        Returns:
            bool: True se o CNPJ é válido, False caso contrário
        """
        # Remove caracteres não numéricos
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
            
        # Aqui você pode adicionar mais validações específicas do CNPJ
        return True
    
    def validate_headers(self, headers: List[str]) -> None:
        """
        Valida se o cabeçalho do CSV contém todos os campos obrigatórios.
        
        Args:
            headers: Lista de cabeçalhos do CSV
            
        Raises:
            CSVValidationError: Se algum campo obrigatório estiver faltando
        """
        missing_fields = [field for field in self.required_fields if field not in headers]
        if missing_fields:
            raise CSVValidationError(
                f"Campos obrigatórios ausentes no CSV: {', '.join(missing_fields)}"
            )

    def validate_row(self, row: Dict[str, str], line_number: int) -> None:
        """
        Valida uma linha do CSV.
        
        Args:
            row: Dicionário com os dados da linha
            line_number: Número da linha no CSV
            
        Raises:
            CSVValidationError: Se houver erro de validação na linha
        """
        # Valida campos obrigatórios
        for field in self.required_fields:
            if not row.get(field):
                raise CSVValidationError(
                    f"Campo obrigatório '{field}' vazio na linha {line_number}"
                )
        
        # Valida CNPJ
        if not self.validate_cnpj(row['cnpj']):
            raise CSVValidationError(
                f"CNPJ inválido na linha {line_number}: {row['cnpj']}"
            )

    def process_row(self, row: Dict[str, str]) -> Dict:
        """
        Processa uma linha do CSV e retorna um dicionário com os dados formatados.
        
        Args:
            row: Dicionário com os dados da linha
            
        Returns:
            Dict: Dados formatados para inserção no banco
        """
        # Remove espaços em branco e formata o CNPJ
        processed = {
            'cnpj': ''.join(filter(str.isdigit, row['cnpj'])),
            'razao_social': row['razao_social'].strip(),
            'website': row.get('website', '').strip(),
            'status': row.get('status', 'prospecting').strip().lower(),
            'data_cadastro': datetime.now(),
            'ultima_atualizacao': datetime.now()
        }
        return processed

    def import_csv(self, file_path: str, db_session: Session) -> Dict[str, int]:
        """
        Importa dados de empresas de um arquivo CSV para o banco de dados.
        
        Args:
            file_path: Caminho para o arquivo CSV
            db_session: Sessão do SQLAlchemy
            
        Returns:
            Dict[str, int]: Estatísticas da importação (total, sucesso, duplicados, erro)
        """
        stats = {'total': 0, 'success': 0, 'duplicates': 0, 'errors': 0}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                
                # Valida cabeçalhos
                self.validate_headers(reader.fieldnames)
                
                # Processa cada linha
                for line_number, row in enumerate(reader, start=2):
                    stats['total'] += 1
                    
                    try:
                        # Valida a linha
                        self.validate_row(row, line_number)
                        
                        # Processa os dados
                        empresa_data = self.process_row(row)
                        
                        # Tenta inserir no banco
                        empresa = Empresa(**empresa_data)
                        db_session.add(empresa)
                        db_session.commit()
                        
                        stats['success'] += 1
                        logger.info(f"Empresa importada com sucesso: {empresa_data['razao_social']}")
                        
                    except IntegrityError:
                        # Trata duplicatas de CNPJ
                        db_session.rollback()
                        stats['duplicates'] += 1
                        logger.warning(f"CNPJ duplicado na linha {line_number}: {row['cnpj']}")
                        
                    except CSVValidationError as e:
                        stats['errors'] += 1
                        logger.error(f"Erro de validação na linha {line_number}: {str(e)}")
                        
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"Erro ao processar linha {line_number}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Erro ao processar arquivo CSV: {str(e)}")
            raise
            
        return stats
