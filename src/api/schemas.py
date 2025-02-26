"""
Schemas Pydantic para validação de dados da API
"""
from pydantic import BaseModel, EmailStr, HttpUrl, Field
from typing import Optional, List
from datetime import datetime
import re

# Schemas para Empresa
class EmpresaBase(BaseModel):
    cnpj: str = Field(..., pattern=r'^\d{14}$')
    razao_social: str
    website: Optional[HttpUrl] = None
    status: str = "prospecting"

class EmpresaCreate(EmpresaBase):
    pass

class Empresa(EmpresaBase):
    id: int
    data_cadastro: datetime
    ultima_atualizacao: datetime

    class Config:
        from_attributes = True

# Schemas para Contato
class ContatoBase(BaseModel):
    nome: str
    cargo: str
    perfil_linkedin: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    celular: Optional[str] = None
    status: str = "identified"

class ContatoCreate(ContatoBase):
    empresa_id: int

class Contato(ContatoBase):
    id: int
    empresa_id: int
    data_captura: datetime
    ultima_atualizacao: datetime

    class Config:
        from_attributes = True

# Schemas para Mensagem
class MensagemBase(BaseModel):
    canal: str
    conteudo: str
    status: str = "sent"
    observacoes: Optional[str] = None

class MensagemCreate(MensagemBase):
    contato_id: int

class Mensagem(MensagemBase):
    id: int
    contato_id: int
    data_envio: datetime
    resposta: Optional[str] = None
    data_resposta: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas para Interação
class InteracaoBase(BaseModel):
    tipo: str
    descricao: Optional[str] = None
    status_conversao: str = "follow_up"

class InteracaoCreate(InteracaoBase):
    contato_id: int

class Interacao(InteracaoBase):
    id: int
    contato_id: int
    data: datetime

    class Config:
        from_attributes = True
