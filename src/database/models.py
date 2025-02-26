"""
Modelos de dados para o banco SQLite3
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, create_engine, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Empresa(Base):
    __tablename__ = 'empresas'

    id = Column(Integer, primary_key=True)
    cnpj = Column(String(14), unique=True, nullable=False)
    razao_social = Column(String(255), nullable=False)
    website = Column(String(255))
    status = Column(String(50))  # prospecting, contacted, negotiating, converted, rejected
    data_cadastro = Column(DateTime, default=datetime.now)
    ultima_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    contatos = relationship("Contato", back_populates="empresa")

class Contato(Base):
    __tablename__ = 'contatos'

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey('empresas.id'))
    nome = Column(String(255), nullable=False)
    cargo = Column(String(100), nullable=False)
    perfil_linkedin = Column(String(255))
    email = Column(String(255))
    telefone = Column(String(50))
    celular = Column(String(50))
    status = Column(String(50))  # identified, contacted, interested, converted
    data_captura = Column(DateTime, default=datetime.now)
    ultima_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    empresa = relationship("Empresa", back_populates="contatos")
    mensagens = relationship("Mensagem", back_populates="contato")
    interacoes = relationship("Interacao", back_populates="contato")

class Mensagem(Base):
    __tablename__ = 'mensagens'

    id = Column(Integer, primary_key=True)
    contato_id = Column(Integer, ForeignKey('contatos.id'))
    canal = Column(String(50))  # linkedin, email, whatsapp, sms
    conteudo = Column(String)
    data_envio = Column(DateTime, default=datetime.now)
    status = Column(String(50))  # sent, delivered, read, replied
    resposta = Column(String)
    data_resposta = Column(DateTime)
    observacoes = Column(String)
    
    # Relacionamentos
    contato = relationship("Contato", back_populates="mensagens")

class Interacao(Base):
    __tablename__ = 'interacoes'

    id = Column(Integer, primary_key=True)
    contato_id = Column(Integer, ForeignKey('contatos.id'))
    tipo = Column(String(50))  # call, meeting, email_open, link_click
    data = Column(DateTime, default=datetime.now)
    descricao = Column(String)
    status_conversao = Column(String(50))  # interested, not_interested, follow_up, converted
    
    # Relacionamentos
    contato = relationship("Contato", back_populates="interacoes")

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

def init_db(database_path: str = 'sqlite:///database.db'):
    """
    Inicializa o banco de dados SQLite3 e cria as tabelas se não existirem
    
    Args:
        database_path: Caminho para o arquivo do banco SQLite3
                      Por padrão usa 'database.db' no diretório atual
    """
    engine = create_engine(database_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)
