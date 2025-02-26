"""
Rotas para interações
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..schemas import Interacao, InteracaoCreate
from ..auth import User, get_current_active_user, get_db

router = APIRouter()

@router.post("/", response_model=Interacao)
async def create_interacao(
    interacao: InteracaoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar nova interação"""
    from ...database.models import Interacao, Contato
    
    contato = db.query(Contato).filter(Contato.id == interacao.contato_id).first()
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    db_interacao = Interacao(**interacao.model_dump())
    db.add(db_interacao)
    db.commit()
    db.refresh(db_interacao)
    return db_interacao

@router.get("/", response_model=List[Interacao])
async def list_interacoes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar interações"""
    from ...database.models import Interacao
    
    interacoes = db.query(Interacao).offset(skip).limit(limit).all()
    return interacoes

@router.get("/contatos/{contato_id}/", response_model=List[Interacao])
async def list_interacoes_by_contato(
    contato_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar interações de um contato"""
    from ...database.models import Interacao
    
    interacoes = db.query(Interacao).filter(Interacao.contato_id == contato_id).all()
    return interacoes
