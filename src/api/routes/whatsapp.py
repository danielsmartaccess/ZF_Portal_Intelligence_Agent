"""
Rotas para interação com WhatsApp
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..deps import get_db
from ..auth import get_current_active_user, User
from ... import schemas
from ...database.marketing_repository import WhatsAppRepository
from ...whatsapp.whatsapp_session_manager import WhatsAppSessionManager
from ...whatsapp.whatsapp_message_handler import WhatsAppMessageHandler
from ...whatsapp.whatsapp_webhook_handler import WhatsAppWebhookHandler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_whatsapp")

router = APIRouter()

# Instância do gerenciador de sessão
whatsapp_session_manager = None


def get_whatsapp_session_manager():
    """
    Obtém a instância do gerenciador de sessão WhatsApp
    """
    global whatsapp_session_manager
    if whatsapp_session_manager is None:
        from ...config import get_settings  # Importação local para evitar circularidade
        settings = get_settings()
        whatsapp_session_manager = WhatsAppSessionManager(
            waha_url=settings.waha_url,
            api_key=settings.waha_api_key,
            session_id=settings.waha_session_id
        )
    return whatsapp_session_manager


# Rotas para gerenciamento de sessão WhatsApp
@router.post("/sessions", response_model=Dict[str, Any])
async def start_session(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Inicia uma sessão WhatsApp e retorna o código QR para autenticação
    """
    try:
        # Iniciar a sessão em background
        background_tasks.add_task(session_manager.start_session)
        
        # Retornar informações iniciais da sessão
        return {
            "message": "Sessão WhatsApp sendo iniciada, use a rota /qr-code para obter o QR Code",
            "session_id": session_manager.session_id,
            "status": "initializing"
        }
    except Exception as e:
        logger.error(f"Erro ao iniciar sessão WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar sessão WhatsApp: {str(e)}"
        )


@router.get("/sessions/qr-code", response_model=Dict[str, Any])
async def get_qr_code(
    current_user: User = Depends(get_current_active_user),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Obtém o código QR para autenticação WhatsApp
    """
    try:
        qr_code = session_manager.get_qr_code()
        return {
            "qr_code": qr_code,
            "session_id": session_manager.session_id,
            "status": session_manager.get_session_status()
        }
    except Exception as e:
        logger.error(f"Erro ao obter QR code: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter QR code: {str(e)}"
        )


@router.get("/sessions/status", response_model=Dict[str, Any])
async def get_session_status(
    current_user: User = Depends(get_current_active_user),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Verifica o status da sessão WhatsApp
    """
    try:
        status = session_manager.get_session_status()
        return {
            "session_id": session_manager.session_id,
            "status": status
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status da sessão: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar status da sessão: {str(e)}"
        )


@router.post("/sessions/restart", response_model=Dict[str, Any])
async def restart_session(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Reinicia a sessão WhatsApp
    """
    try:
        # Reiniciar a sessão em background
        background_tasks.add_task(session_manager.restart_session)
        
        return {
            "message": "Sessão WhatsApp sendo reiniciada",
            "session_id": session_manager.session_id,
            "status": "restarting"
        }
    except Exception as e:
        logger.error(f"Erro ao reiniciar sessão WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao reiniciar sessão WhatsApp: {str(e)}"
        )


# Rotas para envio de mensagens
@router.post("/messages/send", response_model=Dict[str, Any])
async def send_message(
    message_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Envia uma mensagem pelo WhatsApp
    
    Parâmetros:
    - recipient: Número do destinatário (formato: 5511999999999)
    - message: Conteúdo da mensagem
    - message_type: Tipo da mensagem (text, image, document, etc.)
    - media_url: URL do arquivo de mídia (opcional)
    - metadata: Metadados adicionais (opcional)
    """
    try:
        # Criar handler de mensagens
        message_handler = WhatsAppMessageHandler(
            connector=session_manager.connector,
            repository=WhatsAppRepository(db)
        )
        
        # Processar e enviar mensagem
        result = message_handler.send_message(
            recipient=message_data.get("recipient"),
            message_type=message_data.get("message_type", "text"),
            content=message_data.get("message"),
            media_url=message_data.get("media_url"),
            metadata=message_data.get("metadata")
        )
        
        return {
            "success": True,
            "message_id": result.get("id"),
            "status": "sent"
        }
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar mensagem WhatsApp: {str(e)}"
        )


# Rota para webhook
@router.post("/webhook", response_model=Dict[str, Any])
async def webhook_handler(
    background_tasks: BackgroundTasks,
    webhook_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Recebe notificações de webhook do WhatsApp
    """
    try:
        # Criar handler de webhook
        webhook_handler = WhatsAppWebhookHandler(
            message_handler=WhatsAppMessageHandler(
                connector=session_manager.connector,
                repository=WhatsAppRepository(db)
            ),
            repository=WhatsAppRepository(db)
        )
        
        # Processar webhook em background para responder rapidamente
        background_tasks.add_task(webhook_handler.process_webhook, webhook_data)
        
        return {"success": True, "message": "Webhook recebido e sendo processado"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook WhatsApp: {e}")
        # Retornamos 200 mesmo com erro para evitar reenvio pelo WAHA
        return {"success": False, "message": f"Erro: {str(e)}"}


# Rota para verificação de número
@router.post("/check-number", response_model=Dict[str, Any])
async def check_number(
    number_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    session_manager: WhatsAppSessionManager = Depends(get_whatsapp_session_manager)
):
    """
    Verifica se um número está disponível no WhatsApp
    
    Parâmetros:
    - number: Número a verificar (formato: 5511999999999)
    """
    try:
        result = session_manager.check_number_exists(number_data.get("number"))
        return {
            "number": number_data.get("number"),
            "exists": result.get("exists", False),
            "status": result.get("status")
        }
    except Exception as e:
        logger.error(f"Erro ao verificar número no WhatsApp: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao verificar número no WhatsApp: {str(e)}"
        )
