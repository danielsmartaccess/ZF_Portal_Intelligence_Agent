from fastapi import APIRouter
from . import auth, mensagens, interacoes

# Criar router principal
router = APIRouter()

# Incluir sub-routers
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(mensagens.router, prefix="/mensagens", tags=["mensagens"])
router.include_router(interacoes.router, prefix="/interacoes", tags=["interacoes"])
