"""
Dependências comuns da API
"""
from typing import Generator
from sqlalchemy.orm import Session

from .config import get_settings
from ..database.models import init_db

settings = get_settings()

def get_db() -> Generator[Session, None, None]:
    """Obtém uma sessão do banco de dados"""
    db = init_db(settings.database_url)()
    try:
        yield db
    finally:
        db.close()
