"""
Testes unitários para o módulo de importação CSV.
"""
import pytest
import tempfile
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, Empresa
from .csv_importer import CSVImporter, CSVValidationError

@pytest.fixture
def db_session():
    """Fixture que cria um banco de dados temporário para testes"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def csv_importer():
    """Fixture que retorna uma instância do CSVImporter"""
    return CSVImporter()

@pytest.fixture
def valid_csv_file():
    """Fixture que cria um arquivo CSV válido para testes"""
    content = '''cnpj,razao_social,website,status
12345678901234,Empresa Teste,www.teste.com,prospecting
98765432109876,Outra Empresa,www.outra.com,contacted'''
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write(content)
        return f.name

def test_validate_cnpj(csv_importer):
    """Testa a validação de CNPJ"""
    assert csv_importer.validate_cnpj('12345678901234')
    assert not csv_importer.validate_cnpj('123456')
    assert not csv_importer.validate_cnpj('123456789012345')

def test_validate_headers(csv_importer):
    """Testa a validação de cabeçalhos do CSV"""
    valid_headers = ['cnpj', 'razao_social', 'website']
    csv_importer.validate_headers(valid_headers)
    
    invalid_headers = ['cnpj']
    with pytest.raises(CSVValidationError):
        csv_importer.validate_headers(invalid_headers)

def test_validate_row(csv_importer):
    """Testa a validação de uma linha do CSV"""
    valid_row = {
        'cnpj': '12345678901234',
        'razao_social': 'Empresa Teste',
        'website': 'www.teste.com'
    }
    csv_importer.validate_row(valid_row, 1)
    
    invalid_row = {
        'cnpj': '123',  # CNPJ inválido
        'razao_social': 'Empresa Teste'
    }
    with pytest.raises(CSVValidationError):
        csv_importer.validate_row(invalid_row, 1)

def test_process_row(csv_importer):
    """Testa o processamento de uma linha do CSV"""
    row = {
        'cnpj': '12.345.678/9012-34',
        'razao_social': ' Empresa Teste ',
        'website': ' www.teste.com ',
        'status': ' PROSPECTING '
    }
    processed = csv_importer.process_row(row)
    
    assert processed['cnpj'] == '12345678901234'
    assert processed['razao_social'] == 'Empresa Teste'
    assert processed['website'] == 'www.teste.com'
    assert processed['status'] == 'prospecting'
    assert isinstance(processed['data_cadastro'], datetime)

def test_import_csv(csv_importer, db_session, valid_csv_file):
    """Testa a importação completa de um arquivo CSV"""
    try:
        stats = csv_importer.import_csv(valid_csv_file, db_session)
        
        assert stats['total'] == 2
        assert stats['success'] == 2
        assert stats['duplicates'] == 0
        assert stats['errors'] == 0
        
        # Verifica se as empresas foram salvas no banco
        empresas = db_session.query(Empresa).all()
        assert len(empresas) == 2
        
    finally:
        # Limpa o arquivo temporário
        os.unlink(valid_csv_file)

def test_duplicate_cnpj(csv_importer, db_session, valid_csv_file):
    """Testa o tratamento de CNPJs duplicados"""
    content = '''cnpj,razao_social,website,status
12345678901234,Empresa Teste 1,www.teste1.com,prospecting
12345678901234,Empresa Teste 2,www.teste2.com,contacted'''
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write(content)
        duplicate_file = f.name
    
    try:
        stats = csv_importer.import_csv(duplicate_file, db_session)
        
        assert stats['total'] == 2
        assert stats['success'] == 1
        assert stats['duplicates'] == 1
        assert stats['errors'] == 0
        
        # Verifica se apenas uma empresa foi salva
        empresas = db_session.query(Empresa).all()
        assert len(empresas) == 1
        
    finally:
        os.unlink(duplicate_file)
