"""
Script para adaptação do modelo de dados para WhatsApp e Funil de Marketing

Este script adiciona novas tabelas e campos ao modelo de dados existente para suportar
integrações de WhatsApp e gestão de funil de marketing.
"""

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# Caminho para o arquivo de banco de dados atual
DATABASE_PATH = 'sqlite:///database.db'

# Base para novos modelos
Base = declarative_base()


# Definição das novas tabelas
class WhatsAppSession(Base):
    __tablename__ = 'whatsapp_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default='INITIALIZING')  # INITIALIZING, SCAN_QR_CODE, CONNECTED, FAILED, DISCONNECTED, STOPPED
    qr_code = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    connected_at = Column(DateTime)
    last_activity = Column(DateTime)
    data = Column(JSON)  # Dados adicionais da sessão em formato JSON


class WhatsAppMessage(Base):
    __tablename__ = 'whatsapp_messages'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(String(100), unique=True)
    contato_id = Column(Integer, ForeignKey('contatos.id'))
    whatsapp_number = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False)  # inbound, outbound
    message_type = Column(String(20), nullable=False)  # text, image, document, audio, video, etc.
    content = Column(Text)
    media_url = Column(String)
    status = Column(String(20))  # sent, delivered, read, replied, failed    timestamp = Column(DateTime, default=datetime.now)
    response_to = Column(Integer, ForeignKey('whatsapp_messages.id'))
    message_metadata = Column(JSON)  # Dados adicionais da mensagem em formato JSON
    
    # Relacionamentos
    contato = relationship("Contato", back_populates="whatsapp_messages")
    responses = relationship("WhatsAppMessage", foreign_keys=[response_to])


class FunnelStage(Base):
    __tablename__ = 'funnel_stages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)  # attraction, relationship, conversion, customer
    description = Column(String(255))
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relacionamentos
    contacts = relationship("FunnelContact", back_populates="stage")
    templates = relationship("FunnelTemplate", back_populates="stage")


class FunnelContact(Base):
    __tablename__ = 'funnel_contacts'
    
    id = Column(Integer, primary_key=True)
    contato_id = Column(Integer, ForeignKey('contatos.id'), nullable=False)
    stage_id = Column(Integer, ForeignKey('funnel_stages.id'), nullable=False)
    score = Column(Integer, default=0)  # 0-100
    qualification = Column(String(20))  # cold, warm, hot, sales_ready
    entered_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now)
    days_in_stage = Column(Integer, default=0)
    next_action = Column(String(50))
    next_action_date = Column(DateTime)
    notes = Column(Text)
    
    # Relacionamentos
    contato = relationship("Contato", back_populates="funnel_data")
    stage = relationship("FunnelStage", back_populates="contacts")
    activities = relationship("FunnelActivity", back_populates="funnel_contact")


class FunnelActivity(Base):
    __tablename__ = 'funnel_activities'
    
    id = Column(Integer, primary_key=True)
    funnel_contact_id = Column(Integer, ForeignKey('funnel_contacts.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # message, stage_change, score_update, interaction
    description = Column(String(255))
    previous_value = Column(String(50))
    new_value = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    activity_metadata = Column(JSON)
    
    # Relacionamentos
    funnel_contact = relationship("FunnelContact", back_populates="activities")


class FunnelTemplate(Base):
    __tablename__ = 'funnel_templates'
    
    id = Column(Integer, primary_key=True)
    stage_id = Column(Integer, ForeignKey('funnel_stages.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    stage = relationship("FunnelStage", back_populates="templates")
    scheduled_messages = relationship("ScheduledMessage", back_populates="template")


class ScheduledMessage(Base):
    __tablename__ = 'scheduled_messages'
    
    id = Column(Integer, primary_key=True)
    contato_id = Column(Integer, ForeignKey('contatos.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('funnel_templates.id'))
    channel = Column(String(20), nullable=False)  # whatsapp, email, sms
    content = Column(Text)  # Usado quando não há template
    scheduled_for = Column(DateTime, nullable=False)
    status = Column(String(20), default='pending')  # pending, sent, failed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime)
    params = Column(JSON)  # Parâmetros para preencher template
    
    # Relacionamentos
    contato = relationship("Contato")
    template = relationship("FunnelTemplate", back_populates="scheduled_messages")


# Função para adicionar novas colunas à tabela de contatos existente
def add_columns_to_contacts(engine):
    """Adiciona novas colunas à tabela de contatos"""
    meta = MetaData()
    meta.reflect(bind=engine)
    
    contatos_table = meta.tables['contatos']
    
    # Verificar se as colunas já existem antes de adicionar
    column_names = [column.name for column in contatos_table.columns]
    
    new_columns = []
    if 'whatsapp_number' not in column_names:
        new_columns.append(Column('whatsapp_number', String(50)))
    if 'whatsapp_status' not in column_names:
        new_columns.append(Column('whatsapp_status', String(20)))
    if 'last_whatsapp_interaction' not in column_names:
        new_columns.append(Column('last_whatsapp_interaction', DateTime))
    if 'funnel_stage' not in column_names:
        new_columns.append(Column('funnel_stage', String(50)))
    if 'lead_score' not in column_names:
        new_columns.append(Column('lead_score', Integer, default=0))
    if 'lead_tags' not in column_names:
        new_columns.append(Column('lead_tags', String(255)))
    if 'lead_source' not in column_names:
        new_columns.append(Column('lead_source', String(50)))
    
    # Adiciona as colunas se alguma foi definida
    if new_columns:
        for column in new_columns:
            engine.execute(f'ALTER TABLE contatos ADD COLUMN {column.name} {column.type}')
        
        print(f"Adicionadas {len(new_columns)} novas colunas à tabela contatos")
    else:
        print("Nenhuma coluna nova necessária na tabela contatos")


# Função para configurar relacionamentos nos modelos existentes
def setup_relationships():
    """
    Define novos relacionamentos para os modelos existentes
    
    Nota: Esta função deve ser chamada após a criação das novas tabelas
    """
    from .models import Contato
    
    # Adiciona relacionamentos ao modelo Contato
    Contato.whatsapp_messages = relationship("WhatsAppMessage", back_populates="contato")
    Contato.funnel_data = relationship("FunnelContact", back_populates="contato")
    

# Função para inicializar o funil com estágios padrão
def initialize_funnel_stages(session):
    """
    Cria os estágios padrão do funil de marketing se não existirem
    """
    stages = [
        {"name": "attraction", "description": "Fase inicial de atração", "order": 1},
        {"name": "relationship", "description": "Fase de desenvolvimento de relacionamento", "order": 2},
        {"name": "conversion", "description": "Fase de conversão/decisão", "order": 3},
        {"name": "customer", "description": "Cliente convertido", "order": 4}
    ]
    
    for stage_data in stages:
        existing = session.query(FunnelStage).filter_by(name=stage_data["name"]).first()
        if not existing:
            stage = FunnelStage(**stage_data)
            session.add(stage)
    
    session.commit()
    print("Estágios do funil de marketing inicializados")


def upgrade_database(database_path=DATABASE_PATH):
    """
    Atualiza o banco de dados com as novas tabelas e colunas
    """
    engine = create_engine(database_path)
    
    # Adiciona novas colunas às tabelas existentes
    add_columns_to_contacts(engine)
    
    # Cria as novas tabelas
    Base.metadata.create_all(engine)
    print("Novas tabelas criadas com sucesso")
    
    # Configura a sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Inicializa dados padrão
    initialize_funnel_stages(session)
    
    # Fecha a sessão
    session.close()
    
    return "Banco de dados atualizado com sucesso"


if __name__ == "__main__":
    result = upgrade_database()
    print(result)
