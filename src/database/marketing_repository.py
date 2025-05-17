"""
Módulo de repositório para operações com WhatsApp e funil de marketing

Este módulo implementa métodos para armazenar e recuperar dados relacionados
à integração com WhatsApp e ao gerenciamento do funil de marketing.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from sqlalchemy import desc, asc, and_, or_, func
from sqlalchemy.orm import Session

from .models import Contato, Mensagem, Interacao
from .db_upgrade import (
    WhatsAppSession, 
    WhatsAppMessage, 
    FunnelStage, 
    FunnelContact, 
    FunnelActivity,
    FunnelTemplate,
    ScheduledMessage
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("marketing_repository")


class WhatsAppRepository:
    """
    Repositório para operações relacionadas ao WhatsApp
    """
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
    
    def get_contact_by_whatsapp(self, whatsapp_number: str) -> Optional[Contato]:
        """
        Busca um contato pelo número de WhatsApp
        
        Args:
            whatsapp_number: Número WhatsApp (formato internacional sem +)
        
        Returns:
            Contato: Objeto contato ou None se não encontrado
        """
        return self.session.query(Contato).filter_by(whatsapp_number=whatsapp_number).first()
    
    def create_whatsapp_session(self, session_data: Dict[str, Any]) -> WhatsAppSession:
        """
        Cria ou atualiza uma sessão WhatsApp
        
        Args:
            session_data: Dados da sessão
        
        Returns:
            WhatsAppSession: Objeto da sessão criada/atualizada
        """
        session_id = session_data.get("session_id")
        
        # Verifica se a sessão já existe
        existing_session = self.session.query(WhatsAppSession).filter_by(session_id=session_id).first()
        
        if existing_session:
            # Atualiza sessão existente
            for key, value in session_data.items():
                setattr(existing_session, key, value)
            session_obj = existing_session
        else:
            # Cria nova sessão
            session_obj = WhatsAppSession(**session_data)
            self.session.add(session_obj)
        
        self.session.commit()
        return session_obj
    
    def update_session_status(self, session_id: str, status: str) -> WhatsAppSession:
        """
        Atualiza o status de uma sessão WhatsApp
        
        Args:
            session_id: ID da sessão
            status: Novo status
        
        Returns:
            WhatsAppSession: Sessão atualizada ou None se não encontrada
        """
        session_obj = self.session.query(WhatsAppSession).filter_by(session_id=session_id).first()
        
        if session_obj:
            session_obj.status = status
            session_obj.last_activity = datetime.now()
            
            if status == "CONNECTED":
                session_obj.connected_at = datetime.now()
            
            self.session.commit()
        
        return session_obj
    
    def save_whatsapp_message(self, message_data: Dict[str, Any]) -> WhatsAppMessage:
        """
        Salva uma mensagem WhatsApp
        
        Args:
            message_data: Dados da mensagem
        
        Returns:
            WhatsAppMessage: Objeto da mensagem salva
        """
        # Verifica se a mensagem já existe pelo message_id
        message_id = message_data.get("message_id")
        existing_message = None
        
        if message_id:
            existing_message = self.session.query(WhatsAppMessage).filter_by(message_id=message_id).first()
        
        if existing_message:
            # Atualiza mensagem existente
            for key, value in message_data.items():
                setattr(existing_message, key, value)
            message = existing_message
        else:
            # Cria nova mensagem
            message = WhatsAppMessage(**message_data)
            self.session.add(message)
        
        # Se a mensagem tem um contato associado, atualiza última interação do contato
        if message.contato_id:
            contato = self.session.query(Contato).get(message.contato_id)
            if contato:
                contato.last_whatsapp_interaction = datetime.now()
        
        self.session.commit()
        return message
    
    def get_whatsapp_messages(
        self, 
        whatsapp_number: str = None, 
        contato_id: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WhatsAppMessage]:
        """
        Obtém mensagens de WhatsApp
        
        Args:
            whatsapp_number: Filtrar por número WhatsApp
            contato_id: Filtrar por ID de contato
            limit: Limite de mensagens
            offset: Deslocamento para paginação
        
        Returns:
            List[WhatsAppMessage]: Lista de mensagens
        """
        query = self.session.query(WhatsAppMessage)
        
        if whatsapp_number:
            query = query.filter_by(whatsapp_number=whatsapp_number)
        if contato_id:
            query = query.filter_by(contato_id=contato_id)
        
        return query.order_by(desc(WhatsAppMessage.timestamp)).limit(limit).offset(offset).all()
    
    def update_message_status(self, message_id: str, status: str) -> Optional[WhatsAppMessage]:
        """
        Atualiza o status de uma mensagem
        
        Args:
            message_id: ID da mensagem
            status: Novo status (sent, delivered, read, failed)
        
        Returns:
            WhatsAppMessage: Mensagem atualizada ou None se não encontrada
        """
        message = self.session.query(WhatsAppMessage).filter_by(message_id=message_id).first()
        
        if message:
            message.status = status
            self.session.commit()
        
        return message
    
    def link_contact_to_whatsapp(self, contato_id: int, whatsapp_number: str) -> Optional[Contato]:
        """
        Vincula um número de WhatsApp a um contato existente
        
        Args:
            contato_id: ID do contato
            whatsapp_number: Número de WhatsApp
        
        Returns:
            Contato: Contato atualizado ou None se não encontrado
        """
        contato = self.session.query(Contato).get(contato_id)
        
        if contato:
            contato.whatsapp_number = whatsapp_number
            contato.whatsapp_status = "LINKED"
            self.session.commit()
        
        return contato
    
    def create_contact_from_whatsapp(
        self,
        whatsapp_number: str,
        name: str = None,
        empresa_id: int = None
    ) -> Contato:
        """
        Cria um novo contato a partir de um número de WhatsApp
        
        Args:
            whatsapp_number: Número de WhatsApp
            name: Nome do contato (opcional)
            empresa_id: ID da empresa (opcional)
        
        Returns:
            Contato: Novo contato criado
        """
        # Criar dados do contato
        contact_data = {
            "whatsapp_number": whatsapp_number,
            "nome": name or f"WhatsApp: {whatsapp_number}",
            "cargo": "Não informado",
            "status": "identified",
            "whatsapp_status": "ACTIVE",
            "funnel_stage": "attraction",
            "lead_score": 10,
            "lead_source": "whatsapp"
        }
        
        if empresa_id:
            contact_data["empresa_id"] = empresa_id
        
        # Criar contato
        new_contact = Contato(**contact_data)
        self.session.add(new_contact)
        self.session.commit()
        
        return new_contact


class FunnelRepository:
    """
    Repositório para operações relacionadas ao funil de marketing
    """
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
    
    def get_funnel_stages(self) -> List[FunnelStage]:
        """
        Retorna todos os estágios do funil ordenados
        
        Returns:
            List[FunnelStage]: Lista de estágios
        """
        return self.session.query(FunnelStage).order_by(asc(FunnelStage.order)).all()
    
    def get_stage_by_name(self, stage_name: str) -> Optional[FunnelStage]:
        """
        Obtém um estágio pelo nome
        
        Args:
            stage_name: Nome do estágio
        
        Returns:
            FunnelStage: Estágio encontrado ou None
        """
        return self.session.query(FunnelStage).filter_by(name=stage_name).first()
    
    def get_funnel_contact(self, contato_id: int) -> Optional[FunnelContact]:
        """
        Obtém os dados de funil para um contato
        
        Args:
            contato_id: ID do contato
        
        Returns:
            FunnelContact: Dados de funil ou None se não existir
        """
        return self.session.query(FunnelContact).filter_by(contato_id=contato_id).first()
    
    def create_or_update_funnel_contact(
        self,
        contato_id: int,
        stage_name: str,
        score: int = None,
        qualification: str = None
    ) -> FunnelContact:
        """
        Cria ou atualiza os dados de funil para um contato
        
        Args:
            contato_id: ID do contato
            stage_name: Nome do estágio
            score: Pontuação do lead (opcional)
            qualification: Qualificação do lead (opcional)
        
        Returns:
            FunnelContact: Objeto atualizado ou criado
        """
        # Obtém o estágio
        stage = self.get_stage_by_name(stage_name)
        if not stage:
            raise ValueError(f"Estágio não encontrado: {stage_name}")
        
        # Verifica se já existe
        funnel_contact = self.get_funnel_contact(contato_id)
        
        if funnel_contact:
            # Guarda valores anteriores para registro de atividade
            previous_stage_id = funnel_contact.stage_id
            previous_score = funnel_contact.score
            
            # Atualiza
            if stage.id != previous_stage_id:
                funnel_contact.stage_id = stage.id
                funnel_contact.entered_at = datetime.now()
                funnel_contact.days_in_stage = 0
            else:
                # Calcula dias no estágio
                days = (datetime.now() - funnel_contact.entered_at).days
                funnel_contact.days_in_stage = days
            
            if score is not None:
                funnel_contact.score = score
            
            if qualification:
                funnel_contact.qualification = qualification
            
            funnel_contact.last_updated = datetime.now()
            
            # Registra atividades
            if stage.id != previous_stage_id:
                previous_stage = self.session.query(FunnelStage).get(previous_stage_id)
                self._create_funnel_activity(
                    funnel_contact.id,
                    "stage_change",
                    f"Alteração de estágio: {previous_stage.name} -> {stage.name}",
                    previous_stage.name,
                    stage.name
                )
            
            if score is not None and score != previous_score:
                self._create_funnel_activity(
                    funnel_contact.id,
                    "score_update",
                    f"Atualização de pontuação: {previous_score} -> {score}",
                    str(previous_score),
                    str(score)
                )
            
        else:
            # Cria novo
            funnel_contact = FunnelContact(
                contato_id=contato_id,
                stage_id=stage.id,
                score=score or 0,
                qualification=qualification or "cold",
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            self.session.add(funnel_contact)
            
            # Registra atividade de criação
            self.session.flush()  # Garante que o ID é gerado
            self._create_funnel_activity(
                funnel_contact.id,
                "stage_change",
                f"Entrada no funil: {stage.name}",
                None,
                stage.name
            )
        
        # Atualiza a informação no modelo de Contato também
        contato = self.session.query(Contato).get(contato_id)
        if contato:
            contato.funnel_stage = stage_name
            if score is not None:
                contato.lead_score = score
        
        self.session.commit()
        return funnel_contact
    
    def _create_funnel_activity(
        self,
        funnel_contact_id: int,
        activity_type: str,
        description: str,
        previous_value: str = None,
        new_value: str = None,
        metadata: Dict = None
    ) -> FunnelActivity:
        """
        Cria um registro de atividade no funil
        
        Args:
            funnel_contact_id: ID do contato no funil
            activity_type: Tipo de atividade
            description: Descrição
            previous_value: Valor anterior
            new_value: Novo valor
            metadata: Metadados adicionais
        
        Returns:
            FunnelActivity: Atividade criada
        """
        activity = FunnelActivity(
            funnel_contact_id=funnel_contact_id,
            activity_type=activity_type,
            description=description,
            previous_value=previous_value,
            new_value=new_value,
            metadata=metadata or {}
        )
        
        self.session.add(activity)
        return activity
    
    def get_leads_by_stage(
        self,
        stage_name: str,
        min_score: int = None,
        max_score: int = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Obtém leads em um determinado estágio do funil
        
        Args:
            stage_name: Nome do estágio
            min_score: Pontuação mínima
            max_score: Pontuação máxima
            limit: Limite de resultados
            offset: Deslocamento para paginação
        
        Returns:
            List[Dict]: Lista de leads com dados de contato e funil
        """
        # Obtém o estágio
        stage = self.get_stage_by_name(stage_name)
        if not stage:
            return []
        
        # Consulta base
        query = (self.session.query(Contato, FunnelContact)
                 .join(FunnelContact, Contato.id == FunnelContact.contato_id)
                 .filter(FunnelContact.stage_id == stage.id))
        
        # Filtros adicionais
        if min_score is not None:
            query = query.filter(FunnelContact.score >= min_score)
        if max_score is not None:
            query = query.filter(FunnelContact.score <= max_score)
        
        # Executa a consulta
        results = query.limit(limit).offset(offset).all()
        
        # Formata os resultados
        leads = []
        for contato, funnel_data in results:
            leads.append({
                "id": contato.id,
                "nome": contato.nome,
                "cargo": contato.cargo,
                "empresa_id": contato.empresa_id,
                "email": contato.email,
                "telefone": contato.telefone,
                "whatsapp_number": contato.whatsapp_number,
                "funnel_stage": stage_name,
                "lead_score": funnel_data.score,
                "qualification": funnel_data.qualification,
                "days_in_stage": funnel_data.days_in_stage,
                "last_updated": funnel_data.last_updated
            })
        
        return leads
    
    def create_template(self, template_data: Dict[str, Any]) -> FunnelTemplate:
        """
        Cria ou atualiza um template para o funil
        
        Args:
            template_data: Dados do template
        
        Returns:
            FunnelTemplate: Template criado ou atualizado
        """
        template_id = template_data.get("id")
        
        if template_id:
            # Atualiza template existente
            template = self.session.query(FunnelTemplate).get(template_id)
            if template:
                for key, value in template_data.items():
                    setattr(template, key, value)
                
                template.last_updated = datetime.now()
            else:
                # ID fornecido mas não encontrado
                template = FunnelTemplate(**template_data)
                self.session.add(template)
        else:
            # Cria novo template
            template = FunnelTemplate(**template_data)
            self.session.add(template)
        
        self.session.commit()
        return template
    
    def get_templates_by_stage(self, stage_name: str) -> List[FunnelTemplate]:
        """
        Obtém templates para um estágio específico
        
        Args:
            stage_name: Nome do estágio
        
        Returns:
            List[FunnelTemplate]: Lista de templates
        """
        stage = self.get_stage_by_name(stage_name)
        if not stage:
            return []
        
        return (self.session.query(FunnelTemplate)
                .filter_by(stage_id=stage.id, is_active=True)
                .all())
    
    def schedule_message(
        self,
        contato_id: int,
        scheduled_for: datetime,
        channel: str,
        content: str = None,
        template_id: int = None,
        params: Dict = None
    ) -> ScheduledMessage:
        """
        Agenda uma mensagem para envio
        
        Args:
            contato_id: ID do contato
            scheduled_for: Data/hora para envio
            channel: Canal de envio (whatsapp, email, sms)
            content: Conteúdo da mensagem (se não usar template)
            template_id: ID do template (opcional)
            params: Parâmetros para o template (opcional)
        
        Returns:
            ScheduledMessage: Mensagem agendada
        """
        # Valida os dados
        if not content and not template_id:
            raise ValueError("É necessário fornecer ou conteúdo ou template_id")
        
        scheduled = ScheduledMessage(
            contato_id=contato_id,
            template_id=template_id,
            channel=channel,
            content=content,
            scheduled_for=scheduled_for,
            params=params or {}
        )
        
        self.session.add(scheduled)
        self.session.commit()
        
        return scheduled
    
    def get_scheduled_messages(
        self,
        ready_to_send: bool = False,
        channel: str = None,
        limit: int = 50
    ) -> List[ScheduledMessage]:
        """
        Obtém mensagens agendadas
        
        Args:
            ready_to_send: Se True, retorna apenas mensagens prontas para envio
            channel: Filtrar por canal específico
            limit: Limite de resultados
        
        Returns:
            List[ScheduledMessage]: Lista de mensagens agendadas
        """
        query = self.session.query(ScheduledMessage).filter_by(status='pending')
        
        if ready_to_send:
            query = query.filter(ScheduledMessage.scheduled_for <= datetime.now())
        
        if channel:
            query = query.filter_by(channel=channel)
        
        return query.order_by(asc(ScheduledMessage.scheduled_for)).limit(limit).all()
    
    def update_message_schedule_status(
        self,
        schedule_id: int,
        status: str,
        sent_at: datetime = None
    ) -> Optional[ScheduledMessage]:
        """
        Atualiza o status de uma mensagem agendada
        
        Args:
            schedule_id: ID da mensagem agendada
            status: Novo status (sent, failed, cancelled)
            sent_at: Data/hora de envio (apenas para status=sent)
        
        Returns:
            ScheduledMessage: Mensagem atualizada ou None se não encontrada
        """
        message = self.session.query(ScheduledMessage).get(schedule_id)
        
        if message:
            message.status = status
            
            if status == 'sent' and sent_at:
                message.sent_at = sent_at
            
            self.session.commit()
        
        return message
    
    def get_leads_for_classification(self, limit: int = 100) -> List[Dict]:
        """
        Obtém leads que precisam ser classificados ou reclassificados
        
        Args:
            limit: Limite de resultados
        
        Returns:
            List[Dict]: Lista de leads para classificação
        """
        # Estratégia 1: Leads sem classificação de funil
        query1 = (self.session.query(Contato)
                 .outerjoin(FunnelContact, Contato.id == FunnelContact.contato_id)
                 .filter(FunnelContact.id == None)
                 .limit(limit))
        
        # Estratégia 2: Leads com classificação antiga (mais de 7 dias)
        seven_days_ago = datetime.now() - timedelta(days=7)
        query2 = (self.session.query(Contato)
                 .join(FunnelContact, Contato.id == FunnelContact.contato_id)
                 .filter(FunnelContact.last_updated < seven_days_ago)
                 .limit(limit))
        
        # Combina os resultados (até o limite)
        results1 = query1.all()
        
        if len(results1) < limit:
            results2 = query2.limit(limit - len(results1)).all()
            results = results1 + results2
        else:
            results = results1[:limit]
        
        # Formata os resultados
        leads = []
        for contato in results:
            leads.append({
                "id": contato.id,
                "nome": contato.nome,
                "cargo": contato.cargo,
                "empresa_id": contato.empresa_id,
                "email": contato.email,
                "whatsapp_number": contato.whatsapp_number,
                "funnel_stage": contato.funnel_stage,
                "lead_score": contato.lead_score
            })
        
        return leads
    
    def add_contact_tags(self, contato_id: int, tags: List[str]) -> Optional[Contato]:
        """
        Adiciona tags a um contato
        
        Args:
            contato_id: ID do contato
            tags: Lista de tags para adicionar
        
        Returns:
            Contato: Contato atualizado ou None se não encontrado
        """
        contato = self.session.query(Contato).get(contato_id)
        
        if contato:
            current_tags = contato.lead_tags or ""
            current_tag_list = [tag.strip() for tag in current_tags.split(",") if tag.strip()]
            
            # Adiciona novas tags
            for tag in tags:
                if tag not in current_tag_list:
                    current_tag_list.append(tag)
            
            # Atualiza o campo
            contato.lead_tags = ",".join(current_tag_list)
            self.session.commit()
        
        return contato
    
    def create_human_task(self, contato_id: int, reason: str) -> Dict[str, Any]:
        """
        Cria uma tarefa para intervenção humana
        
        Args:
            contato_id: ID do contato
            reason: Motivo para a intervenção
        
        Returns:
            Dict: Dados da tarefa criada
        """
        # Este método pode ser expandido para criar uma tarefa em um sistema de tickets
        # Por enquanto, apenas registra uma interação
        contato = self.session.query(Contato).get(contato_id)
        
        if not contato:
            return {"success": False, "error": "Contato não encontrado"}
        
        # Cria uma interação para registro
        interacao = Interacao(
            contato_id=contato_id,
            tipo="human_task",
            descricao=f"Intervenção humana necessária: {reason}",
            status_conversao="follow_up"
        )
        
        self.session.add(interacao)
        self.session.commit()
        
        # Atualiza o status do contato
        contato.status = "follow_up"
        self.session.commit()
        
        return {
            "success": True,
            "task_id": interacao.id,
            "contato_id": contato_id,
            "nome": contato.nome,
            "reason": reason,
            "created_at": interacao.data
        }


class MarketingRepository:
    """
    Repositório principal que combina funcionalidades de WhatsApp e Funil
    """
    
    def __init__(self, session: Session):
        """
        Inicializa o repositório
        
        Args:
            session: Sessão SQLAlchemy
        """
        self.session = session
        self.whatsapp = WhatsAppRepository(session)
        self.funnel = FunnelRepository(session)
    
    def get_contact_interactions(self, contato_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Obtém todas as interações de um contato (mensagens e interações)
        
        Args:
            contato_id: ID do contato
            limit: Limite de resultados
        
        Returns:
            List[Dict]: Lista de interações ordenadas por data
        """
        # Busca mensagens
        mensagens = (self.session.query(Mensagem)
                    .filter_by(contato_id=contato_id)
                    .order_by(desc(Mensagem.data_envio))
                    .limit(limit)
                    .all())
        
        # Busca mensagens WhatsApp
        whatsapp_msgs = (self.session.query(WhatsAppMessage)
                         .filter_by(contato_id=contato_id)
                         .order_by(desc(WhatsAppMessage.timestamp))
                         .limit(limit)
                         .all())
        
        # Busca interações
        interacoes = (self.session.query(Interacao)
                     .filter_by(contato_id=contato_id)
                     .order_by(desc(Interacao.data))
                     .limit(limit)
                     .all())
        
        # Converte para formato unificado
        result = []
        
        for msg in mensagens:
            result.append({
                "id": f"msg_{msg.id}",
                "date": msg.data_envio,
                "type": "message",
                "channel": msg.canal,
                "direction": "outbound" if not msg.resposta else "inbound",
                "content": msg.conteudo if not msg.resposta else msg.resposta,
                "status": msg.status
            })
        
        for msg in whatsapp_msgs:
            result.append({
                "id": f"wa_{msg.id}",
                "date": msg.timestamp,
                "type": "message",
                "channel": "whatsapp",
                "direction": msg.direction,
                "content": msg.content,
                "status": msg.status,
                "message_type": msg.message_type
            })
        
        for inter in interacoes:
            result.append({
                "id": f"int_{inter.id}",
                "date": inter.data,
                "type": inter.tipo,
                "content": inter.descricao,
                "status": inter.status_conversao
            })
        
        # Ordena por data (mais recentes primeiro)
        result.sort(key=lambda x: x["date"], reverse=True)
        
        # Limita ao número solicitado
        return result[:limit]
    
    def get_lead_funnel_summary(self) -> Dict[str, int]:
        """
        Retorna um resumo dos leads em cada estágio do funil
        
        Returns:
            Dict[str, int]: Contagem de leads por estágio
        """
        stages = self.funnel.get_funnel_stages()
        result = {}
        
        for stage in stages:
            count = (self.session.query(func.count(FunnelContact.id))
                    .filter(FunnelContact.stage_id == stage.id)
                    .scalar())
            result[stage.name] = count
        
        return result
    
    def get_contact_by_id_or_whatsapp(
        self, 
        id_or_whatsapp: Union[int, str]
    ) -> Optional[Contato]:
        """
        Busca um contato por ID ou número de WhatsApp
        
        Args:
            id_or_whatsapp: ID do contato ou número de WhatsApp
        
        Returns:
            Contato: Objeto contato ou None se não encontrado
        """
        if isinstance(id_or_whatsapp, int) or id_or_whatsapp.isdigit():
            # Busca por ID
            return self.session.query(Contato).get(int(id_or_whatsapp))
        else:
            # Busca por WhatsApp
            return self.whatsapp.get_contact_by_whatsapp(id_or_whatsapp)
    
    def update_contact_analysis(
        self,
        whatsapp: str,
        intent: str = None,
        sentiment: str = None,
        funnel_stage: str = None
    ) -> Optional[Contato]:
        """
        Atualiza a análise de um contato com base em mensagem WhatsApp
        
        Args:
            whatsapp: Número de WhatsApp
            intent: Intenção detectada
            sentiment: Sentimento detectado
            funnel_stage: Estágio do funil sugerido
        
        Returns:
            Contato: Contato atualizado ou None se não encontrado
        """
        contato = self.whatsapp.get_contact_by_whatsapp(whatsapp)
        
        if not contato:
            # Contato não encontrado, cria um novo
            contato = self.whatsapp.create_contact_from_whatsapp(whatsapp)
        
        # Atualiza campos conforme análise
        if intent:
            # Cria interação para registrar a intenção
            interacao = Interacao(
                contato_id=contato.id,
                tipo="intent_analysis",
                descricao=f"Intenção detectada: {intent}",
                status_conversao="follow_up"
            )
            self.session.add(interacao)
        
        if funnel_stage:
            # Atualiza estágio do funil
            # A pontuação será calculada pelo FunnelManager
            self.funnel.create_or_update_funnel_contact(
                contato_id=contato.id,
                stage_name=funnel_stage
            )
        
        self.session.commit()
        return contato
    
    def save_suggested_response(
        self,
        whatsapp: str,
        original_message: str,
        suggested_response: str
    ) -> Dict[str, Any]:
        """
        Salva uma resposta sugerida pelo LLM
        
        Args:
            whatsapp: Número de WhatsApp
            original_message: Mensagem original
            suggested_response: Resposta sugerida
        
        Returns:
            Dict: Dados da sugestão salva
        """
        # Encontra ou cria o contato
        contato = self.whatsapp.get_contact_by_whatsapp(whatsapp)
        
        if not contato:
            # Contato não encontrado, cria um novo
            contato = self.whatsapp.create_contact_from_whatsapp(whatsapp)
        
        # Cria uma mensagem com a sugestão
        mensagem = Mensagem(
            contato_id=contato.id,
            canal="whatsapp",
            conteudo=suggested_response,
            status="suggested",  # Status especial para sugestões
            resposta=original_message,  # Armazena a mensagem original
            observacoes="Resposta sugerida pelo LLM"
        )
        
        self.session.add(mensagem)
        self.session.commit()
        
        return {
            "id": mensagem.id,
            "contato_id": contato.id,
            "nome": contato.nome,
            "whatsapp": whatsapp,
            "original_message": original_message,
            "suggested_response": suggested_response
        }
    
    def get_automation_settings(self) -> Dict[str, Any]:
        """
        Obtém configurações de automação
        
        Returns:
            Dict: Configurações de automação
        """
        # Esta função pode ser expandida para carregar configurações de banco de dados
        # Por enquanto, retorna valores padrão
        return {
            "auto_respond": False,  # Se deve responder automaticamente
            "auto_classify": True,   # Se deve classificar leads automaticamente
            "auto_schedule": True,   # Se deve agendar mensagens automaticamente
            "working_hours": {
                "start": "08:00",
                "end": "18:00"
            },
            "max_auto_responses_per_day": 3
        }


# Função de fábrica para criar repositórios
def create_repositories(session: Session) -> Dict[str, Any]:
    """
    Cria e retorna instâncias dos repositórios
    
    Args:
        session: Sessão SQLAlchemy
    
    Returns:
        Dict: Dicionário com repositórios
    """
    return {
        "whatsapp": WhatsAppRepository(session),
        "funnel": FunnelRepository(session),
        "marketing": MarketingRepository(session)
    }
