"""
Rotas para mensagens
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..schemas import Mensagem, MensagemCreate
from ..auth import User, get_current_active_user, get_db

router = APIRouter()

@router.post("/", response_model=Mensagem)
async def create_mensagem(
    mensagem: MensagemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Criar nova mensagem"""
    from ...database.models import Mensagem, Contato
    
    contato = db.query(Contato).filter(Contato.id == mensagem.contato_id).first()
    if not contato:
        raise HTTPException(status_code=404, detail="Contato não encontrado")
    
    db_mensagem = Mensagem(**mensagem.model_dump())
    db.add(db_mensagem)
    db.commit()
    db.refresh(db_mensagem)
    return db_mensagem

@router.get("/", response_model=List[Mensagem])
async def list_mensagens(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Listar mensagens"""
    from ...database.models import Mensagem
    
    mensagens = db.query(Mensagem).offset(skip).limit(limit).all()
    return mensagens
