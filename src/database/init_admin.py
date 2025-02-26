"""
Script para criar usuário admin inicial
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.models import init_db, Usuario
from src.api.auth import get_password_hash

def create_admin_user(Session):
    """
    Cria um usuário admin se não existir
    """
    session = Session()
    
    # Verificar se já existe um admin
    admin = session.query(Usuario).filter(Usuario.username == "admin").first()
    if admin:
        print("Usuário admin já existe!")
        return
    
    # Criar usuário admin
    admin = Usuario(
        username="admin",
        email="admin@example.com",
        full_name="Administrator",
        hashed_password=get_password_hash("admin123"),  # Altere esta senha em produção!
        is_active=True
    )
    session.add(admin)
    session.commit()
    
    print("Usuário admin criado com sucesso!")
    print("Username: admin")
    print("Password: admin123")
    session.close()

if __name__ == "__main__":
    # Inicializar o banco de dados
    Session = init_db()
    create_admin_user(Session)
