"""
Sistema de agendamento e envio de mensagens do funil de marketing

Este módulo implementa o sistema de agendamento e envio automático de 
mensagens para contatos em diferentes estágios do funil de marketing.
"""

import logging
import time
import threading
import schedule
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import pytz

from ..database.marketing_repository import FunnelRepository, WhatsAppRepository
from ..whatsapp.whatsapp_connector import WhatsAppConnector
from ..templates.templates_manager import TemplatesManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("message_scheduler")


class MessageScheduler:
    """
    Sistema de agendamento e envio de mensagens
    """
    
    def __init__(
        self,
        funnel_repository: FunnelRepository,
        whatsapp_repository: WhatsAppRepository,
        whatsapp_connector: WhatsAppConnector = None,
        templates_manager: TemplatesManager = None,
        timezone: str = "America/Sao_Paulo"
    ):
        """
        Inicializa o agendador de mensagens
        
        Args:
            funnel_repository: Repositório do funil
            whatsapp_repository: Repositório WhatsApp
            whatsapp_connector: Conector WhatsApp (opcional)
            templates_manager: Gerenciador de templates (opcional)
            timezone: Fuso horário para agendamentos
        """
        self.funnel_repo = funnel_repository
        self.whatsapp_repo = whatsapp_repository
        self.whatsapp_connector = whatsapp_connector
        self.templates_manager = templates_manager
        self.timezone = pytz.timezone(timezone)
        self.scheduler_thread = None
        self.running = False
        self.job_count = 0
        
        # Configura o scheduler
        schedule.clear()
    
    def start(self) -> bool:
        """
        Inicia o serviço de agendamento em uma thread separada
        
        Returns:
            bool: True se o serviço foi iniciado com sucesso
        """
        if self.running:
            logger.warning("Serviço de agendamento já está em execução")
            return False
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # Configura jobs recorrentes
        self._setup_recurring_jobs()
        
        logger.info("Serviço de agendamento iniciado")
        return True
    
    def stop(self) -> bool:
        """
        Para o serviço de agendamento
        
        Returns:
            bool: True se o serviço foi parado com sucesso
        """
        if not self.running:
            logger.warning("Serviço de agendamento não está em execução")
            return False
        
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("Serviço de agendamento parado")
        return True
    
    def _run_scheduler(self) -> None:
        """
        Executa o loop principal do agendador
        """
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def _setup_recurring_jobs(self) -> None:
        """
        Configura jobs recorrentes para o agendador
        """
        # Verifica mensagens pendentes a cada 5 minutos
        schedule.every(5).minutes.do(self.process_pending_messages)
        
        # Verifica novos leads para envio de mensagem inicial todos os dias
        schedule.every().day.at("09:00").do(self.process_new_leads)
        
        # Verifica leads para seguimento todos os dias
        schedule.every().day.at("13:00").do(self.process_followup_leads)
        
        logger.info("Jobs recorrentes configurados")
    
    def process_pending_messages(self) -> int:
        """
        Processa mensagens agendadas pendentes
        
        Returns:
            int: Número de mensagens processadas
        """
        logger.info("Processando mensagens agendadas...")
        
        # Busca mensagens prontas para envio
        messages = self.funnel_repo.get_scheduled_messages(ready_to_send=True)
        
        processed_count = 0
        
        for message in messages:
            try:
                # Verifica se está dentro do horário comercial
                if not self._is_business_hours():
                    logger.info("Fora do horário comercial. Mensagens serão enviadas no próximo horário válido.")
                    return processed_count
                
                # Processa a mensagem
                if message.channel == 'whatsapp':
                    self._send_whatsapp_message(message)
                elif message.channel == 'email':
                    # Implementar envio de email
                    logger.warning("Envio de email não implementado. Mensagem será marcada como falha.")
                    self.funnel_repo.update_message_schedule_status(message.id, 'failed')
                else:
                    logger.warning(f"Canal não suportado: {message.channel}")
                    self.funnel_repo.update_message_schedule_status(message.id, 'failed')
                
                processed_count += 1
                    
            except Exception as e:
                logger.error(f"Erro ao processar mensagem agendada {message.id}: {e}")
                self.funnel_repo.update_message_schedule_status(message.id, 'failed')
        
        logger.info(f"Processadas {processed_count} mensagens agendadas")
        return processed_count
    
    def _send_whatsapp_message(self, message):
        """
        Envia uma mensagem WhatsApp agendada
        
        Args:
            message: Objeto ScheduledMessage
        
        Raises:
            Exception: Se ocorrer algum erro no envio
        """
        if not self.whatsapp_connector:
            logger.error("WhatsApp connector não configurado")
            self.funnel_repo.update_message_schedule_status(message.id, 'failed')
            return
        
        # Obtém contato
        contato = self.whatsapp_repo.session.query(self.whatsapp_repo.session.registry.attrs.Contato).get(message.contato_id)
        
        if not contato or not contato.whatsapp_number:
            logger.error(f"Contato {message.contato_id} não possui número WhatsApp")
            self.funnel_repo.update_message_schedule_status(message.id, 'failed')
            return
        
        # Obtém conteúdo da mensagem (do template ou direto)
        if message.template_id and self.templates_manager:
            # Obtém template
            template = self.whatsapp_repo.session.query(self.whatsapp_repo.session.registry.attrs.FunnelTemplate).get(message.template_id)
            
            if not template:
                logger.error(f"Template {message.template_id} não encontrado")
                self.funnel_repo.update_message_schedule_status(message.id, 'failed')
                return
            
            # Renderiza o template
            try:
                from jinja2 import Template
                rendered_content = Template(template.content).render(**(message.params or {}))
            except Exception as e:
                logger.error(f"Erro ao renderizar template {message.template_id}: {e}")
                self.funnel_repo.update_message_schedule_status(message.id, 'failed')
                return
                
        else:
            # Usa o conteúdo direto
            rendered_content = message.content
        
        if not rendered_content:
            logger.error(f"Conteúdo vazio para mensagem {message.id}")
            self.funnel_repo.update_message_schedule_status(message.id, 'failed')
            return
        
        # Envia a mensagem
        try:
            result = self.whatsapp_connector.send_text_message(
                contato.whatsapp_number, 
                rendered_content
            )
            
            # Atualiza status da mensagem agendada
            self.funnel_repo.update_message_schedule_status(
                message.id, 
                'sent', 
                datetime.now()
            )
            
            # Salva a mensagem no registro de WhatsApp
            self.whatsapp_repo.save_whatsapp_message({
                "contato_id": message.contato_id,
                "whatsapp_number": contato.whatsapp_number,
                "direction": "outbound",
                "message_type": "text",
                "content": rendered_content,
                "status": "sent",
                "message_id": result.get("id", ""),
                "metadata": {
                    "scheduled_id": message.id,
                    "template_id": message.template_id
                }
            })
            
            logger.info(f"Mensagem agendada {message.id} enviada com sucesso para {contato.whatsapp_number}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp: {e}")
            self.funnel_repo.update_message_schedule_status(message.id, 'failed')
            raise
    
    def _is_business_hours(self) -> bool:
        """
        Verifica se está dentro do horário comercial
        
        Returns:
            bool: True se está dentro do horário comercial
        """
        now = datetime.now(self.timezone)
        
        # Horário comercial: segunda a sexta, 8h às 18h
        if now.weekday() >= 5:  # Sábado ou domingo
            return False
        
        if now.hour < 8 or now.hour >= 18:
            return False
        
        return True
    
    def schedule_message(
        self,
        contato_id: int,
        content: str = None,
        template_id: int = None,
        channel: str = 'whatsapp',
        scheduled_for: datetime = None,
        params: Dict = None,
        delay_minutes: int = None
    ) -> Dict[str, Any]:
        """
        Agenda uma mensagem para envio
        
        Args:
            contato_id: ID do contato
            content: Conteúdo da mensagem (se não usar template)
            template_id: ID do template (opcional)
            channel: Canal de envio (whatsapp, email, sms)
            scheduled_for: Data/hora para envio
            params: Parâmetros para o template
            delay_minutes: Atraso em minutos (se scheduled_for não for fornecido)
        
        Returns:
            Dict: Informações da mensagem agendada
        """
        # Determina o horário de envio
        if not scheduled_for:
            if delay_minutes:
                scheduled_for = datetime.now() + timedelta(minutes=delay_minutes)
            else:
                scheduled_for = datetime.now() + timedelta(hours=1)  # Padrão: 1 hora depois
        
        # Agenda a mensagem
        try:
            scheduled = self.funnel_repo.schedule_message(
                contato_id=contato_id,
                scheduled_for=scheduled_for,
                channel=channel,
                content=content,
                template_id=template_id,
                params=params
            )
            
            logger.info(f"Mensagem agendada para contato {contato_id}: {scheduled.id}")
            
            return {
                "id": scheduled.id,
                "contato_id": contato_id,
                "scheduled_for": scheduled_for.isoformat(),
                "channel": channel,
                "status": "pending"
            }
            
        except Exception as e:
            logger.error(f"Erro ao agendar mensagem: {e}")
            return {
                "error": str(e),
                "contato_id": contato_id
            }
    
    def process_new_leads(self) -> int:
        """
        Processa leads novos para envio de mensagem de boas-vindas
        
        Returns:
            int: Número de leads processados
        """
        logger.info("Processando novos leads...")
        
        # Busca estágio inicial do funil
        attraction_stage = self.funnel_repo.get_stage_by_name("attraction")
        
        if not attraction_stage:
            logger.error("Estágio 'attraction' não encontrado no funil")
            return 0
        
        # Busca templates para o estágio
        templates = self.funnel_repo.get_templates_by_stage("attraction")
        
        if not templates:
            logger.warning("Nenhum template disponível para o estágio 'attraction'")
            return 0
        
        # Seleciona o primeiro template (mensagem de boas-vindas)
        welcome_template = templates[0]
        
        # Busca leads no estágio attraction que não receberam mensagem ainda
        # Esta consulta precisa ser adaptada conforme a estrutura específica do banco
        try:
            # Consulta complexa adaptada para encontrar leads sem mensagens ou atividades recentes
            one_day_ago = datetime.now() - timedelta(days=1)
            
            leads = self.funnel_repo.get_leads_by_stage("attraction")
            
            processed_count = 0
            
            for lead in leads:
                contato_id = lead["id"]
                
                # Verifica se já existe mensagem recente para este contato
                whatsapp_number = lead.get("whatsapp_number")
                
                if not whatsapp_number:
                    logger.info(f"Lead {contato_id} não possui número WhatsApp")
                    continue
                
                # Verifica se já existe mensagem nas últimas 24h
                recent_messages = self.whatsapp_repo.get_whatsapp_messages(
                    whatsapp_number=whatsapp_number, 
                    limit=5
                )
                
                has_recent_message = any(
                    msg.timestamp > one_day_ago and msg.direction == "outbound"
                    for msg in recent_messages
                )
                
                if has_recent_message:
                    logger.info(f"Lead {contato_id} já recebeu mensagem recente, pulando")
                    continue
                
                # Agenda a mensagem de boas-vindas
                params = {
                    "nome": lead.get("nome", ""),
                    "empresa": "",  # Poderia ser buscado se necessário
                }
                
                self.schedule_message(
                    contato_id=contato_id,
                    template_id=welcome_template.id,
                    params=params,
                    delay_minutes=30  # Agenda para 30 minutos depois
                )
                
                processed_count += 1
                
                # Limita processamento
                if processed_count >= 20:
                    break
            
            logger.info(f"Processados {processed_count} novos leads")
            return processed_count
            
        except Exception as e:
            logger.error(f"Erro ao processar novos leads: {e}")
            return 0
    
    def process_followup_leads(self) -> int:
        """
        Processa leads para seguimento conforme estágio do funil
        
        Returns:
            int: Número de leads processados
        """
        logger.info("Processando leads para seguimento...")
        
        # Define tempo de espera por estágio (em dias)
        stage_wait_days = {
            "attraction": 3,
            "relationship": 5,
            "conversion": 2
        }
        
        processed_count = 0
        
        # Processa cada estágio
        for stage_name, wait_days in stage_wait_days.items():
            try:
                # Obtém leads no estágio atual
                leads = self.funnel_repo.get_leads_by_stage(stage_name)
                
                for lead in leads:
                    contato_id = lead["id"]
                    days_in_stage = lead.get("days_in_stage", 0)
                    
                    # Verifica se está no tempo de seguimento
                    if days_in_stage < wait_days:
                        continue
                    
                    # Verifica se tem número WhatsApp
                    whatsapp_number = lead.get("whatsapp_number")
                    if not whatsapp_number:
                        continue
                    
                    # Verifica se já foi contatado recentemente
                    cutoff_date = datetime.now() - timedelta(days=wait_days)
                    recent_messages = self.whatsapp_repo.get_whatsapp_messages(
                        whatsapp_number=whatsapp_number, 
                        limit=5
                    )
                    
                    has_recent_message = any(
                        msg.timestamp > cutoff_date and msg.direction == "outbound"
                        for msg in recent_messages
                    )
                    
                    if has_recent_message:
                        logger.info(f"Lead {contato_id} já recebeu seguimento recente, pulando")
                        continue
                    
                    # Busca template apropriado para seguimento
                    templates = self.funnel_repo.get_templates_by_stage(stage_name)
                    
                    if not templates:
                        logger.warning(f"Nenhum template disponível para o estágio '{stage_name}'")
                        continue
                    
                    # Usa o segundo template se disponível (seguimento)
                    template_index = min(1, len(templates) - 1)
                    followup_template = templates[template_index]
                    
                    # Agenda a mensagem de seguimento
                    params = {
                        "nome": lead.get("nome", ""),
                        "dias": days_in_stage
                    }
                    
                    self.schedule_message(
                        contato_id=contato_id,
                        template_id=followup_template.id,
                        params=params,
                        delay_minutes=random_minutes=90 + (contato_id % 60)  # Agenda em horário levemente aleatório
                    )
                    
                    processed_count += 1
                    
                    # Limita processamento por estágio
                    if processed_count >= 10:
                        break
            
            except Exception as e:
                logger.error(f"Erro ao processar leads no estágio {stage_name}: {e}")
        
        logger.info(f"Processados {processed_count} leads para seguimento")
        return processed_count


# Exemplo de uso
if __name__ == "__main__":
    # Mock para teste
    class MockRepo:
        def get_scheduled_messages(self, ready_to_send=False):
            return []
        
        def get_stage_by_name(self, name):
            class Stage:
                id = 1
                name = name
            return Stage()
            
        def get_templates_by_stage(self, name):
            class Template:
                id = 1
                content = "Olá {{ nome }}, como vai?"
            return [Template()]
        
        def get_leads_by_stage(self, name):
            return [{"id": 1, "nome": "João", "whatsapp_number": "5511999998888"}]
        
        def schedule_message(self, **kwargs):
            class Scheduled:
                id = 1
            return Scheduled()
    
    # Inicialização simulada
    scheduler = MessageScheduler(MockRepo(), MockRepo())
    
    # Teste de agendamento
    result = scheduler.schedule_message(
        contato_id=1,
        content="Teste de mensagem agendada",
        delay_minutes=30
    )
    
    print(f"Mensagem agendada: {result}")
