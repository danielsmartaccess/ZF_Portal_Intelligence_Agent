"""
Rotas para gerenciamento do funil de marketing
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

from ..deps import get_db
from ..auth import get_current_active_user, User
from ... import schemas
from ...database.marketing_repository import FunnelRepository
from ...marketing.funnel_manager import FunnelManager
from ...marketing.message_scheduler import MessageScheduler
from ...templates.templates_manager import FunnelTemplatesManager
from ...llm.llm_interface import get_llm_interface

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("api_funnel")

router = APIRouter()

# Instâncias globais
funnel_manager = None
message_scheduler = None


def get_funnel_manager(db: Session = Depends(get_db)):
    """
    Obtém a instância do gerenciador de funil
    """
    global funnel_manager
    if funnel_manager is None:
        from ...config import get_settings  # Importação local para evitar circularidade
        settings = get_settings()
        
        # Obter interface LLM
        llm_interface = get_llm_interface()
        
        # Criar repositório de funil
        funnel_repo = FunnelRepository(db)
        
        # Criar gerenciador de templates
        templates_manager = FunnelTemplatesManager(db)
        
        # Inicializar gerenciador de funil
        funnel_manager = FunnelManager(
            repository=funnel_repo,
            llm_interface=llm_interface,
            templates_manager=templates_manager
        )
    
    return funnel_manager


def get_message_scheduler(db: Session = Depends(get_db)):
    """
    Obtém a instância do agendador de mensagens
    """
    global message_scheduler
    if message_scheduler is None:
        from ...config import get_settings  # Importação local para evitar circularidade
        settings = get_settings()
        
        # Criar repositório de funil
        funnel_repo = FunnelRepository(db)
        
        # Inicializar agendador
        message_scheduler = MessageScheduler(
            repository=funnel_repo,
            funnel_manager=get_funnel_manager(db),
            business_hours_start=settings.business_hours_start,
            business_hours_end=settings.business_hours_end,
            business_days=settings.business_days
        )
    
    return message_scheduler


# Rotas para estágios do funil
@router.get("/stages", response_model=List[Dict[str, Any]])
async def list_funnel_stages(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Lista todos os estágios do funil de marketing
    """
    try:
        stages = funnel_manager.get_all_stages()
        return stages
    except Exception as e:
        logger.error(f"Erro ao listar estágios do funil: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar estágios do funil: {str(e)}"
        )


@router.post("/stages", response_model=Dict[str, Any])
async def create_funnel_stage(
    stage_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Cria um novo estágio de funil
    
    Parâmetros:
    - name: Nome do estágio
    - description: Descrição do estágio
    - order: Ordem no funil (inteiro)
    """
    try:
        new_stage = funnel_manager.create_stage(
            name=stage_data.get("name"),
            description=stage_data.get("description"),
            order=stage_data.get("order")
        )
        return new_stage
    except Exception as e:
        logger.error(f"Erro ao criar estágio do funil: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar estágio do funil: {str(e)}"
        )


# Rotas para contatos no funil
@router.get("/contacts", response_model=List[Dict[str, Any]])
async def list_funnel_contacts(
    stage: Optional[str] = Query(None, description="Filtrar por estágio do funil"),
    qualification: Optional[str] = Query(None, description="Filtrar por qualificação (cold, warm, hot, sales_ready)"),
    min_score: Optional[int] = Query(None, description="Pontuação mínima"),
    max_score: Optional[int] = Query(None, description="Pontuação máxima"),
    skip: int = Query(0, description="Quantidade de registros para pular (paginação)"),
    limit: int = Query(100, description="Limite de registros a retornar (paginação)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Lista contatos no funil de marketing com filtros
    """
    try:
        filters = {}
        if stage:
            filters["stage"] = stage
        if qualification:
            filters["qualification"] = qualification
        if min_score is not None:
            filters["min_score"] = min_score
        if max_score is not None:
            filters["max_score"] = max_score
        
        contacts = funnel_manager.get_contacts(
            filters=filters,
            skip=skip,
            limit=limit
        )
        return contacts
    except Exception as e:
        logger.error(f"Erro ao listar contatos do funil: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar contatos do funil: {str(e)}"
        )


@router.post("/contacts", response_model=Dict[str, Any])
async def add_contact_to_funnel(
    contact_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Adiciona um contato ao funil de marketing
    
    Parâmetros:
    - contato_id: ID do contato
    - stage_id: ID do estágio inicial (opcional)
    - score: Pontuação inicial (opcional)
    - qualification: Qualificação inicial (opcional)
    - notes: Observações (opcional)
    """
    try:
        new_funnel_contact = funnel_manager.add_contact(
            contato_id=contact_data.get("contato_id"),
            stage_id=contact_data.get("stage_id"),
            score=contact_data.get("score"),
            qualification=contact_data.get("qualification"),
            notes=contact_data.get("notes")
        )
        return new_funnel_contact
    except Exception as e:
        logger.error(f"Erro ao adicionar contato ao funil: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar contato ao funil: {str(e)}"
        )


@router.put("/contacts/{contact_id}", response_model=Dict[str, Any])
async def update_funnel_contact(
    contact_id: int,
    contact_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Atualiza as informações de um contato no funil
    
    Parâmetros:
    - stage_id: ID do novo estágio (opcional)
    - score: Nova pontuação (opcional)
    - qualification: Nova qualificação (opcional)
    - notes: Novas observações (opcional)
    """
    try:
        updated_contact = funnel_manager.update_contact(
            funnel_contact_id=contact_id,
            stage_id=contact_data.get("stage_id"),
            score=contact_data.get("score"),
            qualification=contact_data.get("qualification"),
            notes=contact_data.get("notes")
        )
        return updated_contact
    except Exception as e:
        logger.error(f"Erro ao atualizar contato no funil: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao atualizar contato no funil: {str(e)}"
        )


# Rotas para classificação de leads
@router.post("/classify", response_model=Dict[str, Any])
async def classify_lead(
    lead_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Classifica um lead com base nas interações e perfil
    
    Parâmetros:
    - contato_id: ID do contato
    - analyze_messages: Analisar mensagens trocadas (opcional, padrão: True)
    - analyze_interactions: Analisar interações registradas (opcional, padrão: True)
    """
    try:
        classification_result = funnel_manager.classify_lead(
            contato_id=lead_data.get("contato_id"),
            analyze_messages=lead_data.get("analyze_messages", True),
            analyze_interactions=lead_data.get("analyze_interactions", True)
        )
        return classification_result
    except Exception as e:
        logger.error(f"Erro ao classificar lead: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao classificar lead: {str(e)}"
        )


# Rotas para mensagens agendadas
@router.post("/schedule", response_model=Dict[str, Any])
async def schedule_message(
    schedule_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    scheduler: MessageScheduler = Depends(get_message_scheduler)
):
    """
    Agenda uma mensagem para envio futuro
    
    Parâmetros:
    - contato_id: ID do contato
    - message_type: Tipo de mensagem (text, image, document, etc.)
    - content: Conteúdo da mensagem
    - media_url: URL da mídia (opcional)
    - scheduled_time: Horário de envio (formato ISO)
    - template_id: ID do template (opcional)
    - template_data: Dados para processamento do template (opcional)
    """
    try:
        scheduled = scheduler.schedule_message(
            contato_id=schedule_data.get("contato_id"),
            message_type=schedule_data.get("message_type", "text"),
            content=schedule_data.get("content"),
            media_url=schedule_data.get("media_url"),
            scheduled_time=schedule_data.get("scheduled_time"),
            template_id=schedule_data.get("template_id"),
            template_data=schedule_data.get("template_data")
        )
        return scheduled
    except Exception as e:
        logger.error(f"Erro ao agendar mensagem: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao agendar mensagem: {str(e)}"
        )


@router.get("/schedule", response_model=List[Dict[str, Any]])
async def list_scheduled_messages(
    status: Optional[str] = Query(None, description="Filtrar por status (pending, sent, failed)"),
    contato_id: Optional[int] = Query(None, description="Filtrar por contato"),
    skip: int = Query(0, description="Quantidade de registros para pular (paginação)"),
    limit: int = Query(100, description="Limite de registros a retornar (paginação)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    scheduler: MessageScheduler = Depends(get_message_scheduler)
):
    """
    Lista mensagens agendadas
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if contato_id:
            filters["contato_id"] = contato_id
        
        scheduled_messages = scheduler.get_scheduled_messages(
            filters=filters,
            skip=skip,
            limit=limit
        )
        return scheduled_messages
    except Exception as e:
        logger.error(f"Erro ao listar mensagens agendadas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar mensagens agendadas: {str(e)}"
        )


@router.post("/process-queue", response_model=Dict[str, Any])
async def process_message_queue(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    scheduler: MessageScheduler = Depends(get_message_scheduler)
):
    """
    Processa a fila de mensagens pendentes para envio
    """
    try:
        # Processar fila em background
        background_tasks.add_task(scheduler.process_queue)
        
        return {
            "success": True,
            "message": "Processamento da fila de mensagens iniciado"
        }
    except Exception as e:
        logger.error(f"Erro ao processar fila de mensagens: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar fila de mensagens: {str(e)}"
        )


# Rotas para templates de funil
@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_funnel_templates(
    stage: Optional[str] = Query(None, description="Filtrar por estágio do funil"),
    skip: int = Query(0, description="Quantidade de registros para pular (paginação)"),
    limit: int = Query(100, description="Limite de registros a retornar (paginação)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Lista templates disponíveis para o funil
    """
    try:
        filters = {}
        if stage:
            filters["stage"] = stage
        
        templates = funnel_manager.get_templates(
            filters=filters,
            skip=skip,
            limit=limit
        )
        return templates
    except Exception as e:
        logger.error(f"Erro ao listar templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao listar templates: {str(e)}"
        )


@router.post("/templates", response_model=Dict[str, Any])
async def create_funnel_template(
    template_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    funnel_manager: FunnelManager = Depends(get_funnel_manager)
):
    """
    Cria um novo template para o funil
    
    Parâmetros:
    - name: Nome do template
    - description: Descrição do template
    - stage_id: ID do estágio associado
    - content: Conteúdo do template (com variáveis Jinja)
    - message_type: Tipo de mensagem (text, image, document, etc.)
    - variables: Variáveis disponíveis no template
    """
    try:
        new_template = funnel_manager.create_template(
            name=template_data.get("name"),
            description=template_data.get("description"),
            stage_id=template_data.get("stage_id"),
            content=template_data.get("content"),
            message_type=template_data.get("message_type", "text"),
            variables=template_data.get("variables")
        )
        return new_template
    except Exception as e:
        logger.error(f"Erro ao criar template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar template: {str(e)}"
        )
