"""
Aplicação principal FastAPI
"""
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from .config import get_settings
from .deps import get_db
from . import schemas
from .auth import get_current_active_user, User

# Criar instância do FastAPI
settings = get_settings()
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
)

# Rotas para Empresas
@app.post(f"{settings.api_v1_prefix}/empresas/", response_model=schemas.Empresa)
async def create_empresa(
    empresa: schemas.EmpresaCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar nova empresa"""
    from ..database.models import Empresa
    
    db_empresa = Empresa(**empresa.model_dump())
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa

@app.get(f"{settings.api_v1_prefix}/empresas/", response_model=List[schemas.Empresa])
async def list_empresas(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar empresas"""
    from ..database.models import Empresa
    
    empresas = db.query(Empresa).offset(skip).limit(limit).all()
    return empresas

@app.get(f"{settings.api_v1_prefix}/empresas/{{empresa_id}}", response_model=schemas.Empresa)
async def get_empresa(
    empresa_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Obter empresa por ID"""
    from ..database.models import Empresa
    
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa is None:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return empresa

# Incluir rotas de autenticação
from .routes import auth
app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["auth"]
)

# Incluir rotas de mensagens
from .routes import mensagens
app.include_router(
    mensagens.router,
    prefix=f"{settings.api_v1_prefix}/mensagens",
    tags=["mensagens"]
)

# Incluir rotas de interações
from .routes import interacoes
app.include_router(
    interacoes.router,
    prefix=f"{settings.api_v1_prefix}/interacoes",
    tags=["interacoes"]
)

# Incluir rotas de WhatsApp
from .routes import whatsapp
app.include_router(
    whatsapp.router,
    prefix=f"{settings.api_v1_prefix}/whatsapp",
    tags=["whatsapp"]
)

# Incluir rotas de funil de marketing
from .routes import funnel
app.include_router(
    funnel.router,
    prefix=f"{settings.api_v1_prefix}/funnel",
    tags=["funnel"]
)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
