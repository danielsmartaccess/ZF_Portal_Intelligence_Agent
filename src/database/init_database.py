"""
Script para inicializar o banco de dados SQLite3
"""
from models import init_db, Empresa, Contato
from datetime import datetime

def create_sample_data(Session):
    """
    Cria alguns dados de exemplo para testar o banco
    """
    session = Session()
    
    # Criar uma empresa de exemplo
    empresa = Empresa(
        cnpj="12345678901234",
        razao_social="Empresa Exemplo LTDA",
        website="https://exemplo.com.br",
        status="prospecting"
    )
    session.add(empresa)
    session.commit()
    
    # Criar um contato de exemplo
    contato = Contato(
        empresa_id=empresa.id,
        nome="João Silva",
        cargo="CFO",
        perfil_linkedin="https://linkedin.com/in/joaosilva",
        email="joao.silva@exemplo.com.br",
        telefone="11999999999",
        status="identified"
    )
    session.add(contato)
    session.commit()
    
    print("Banco de dados inicializado com dados de exemplo!")
    session.close()

if __name__ == "__main__":
    # Inicializar o banco de dados
    Session = init_db()
    create_sample_data(Session)
