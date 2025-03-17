# ZF Portal Intelligence Agent - Documentação do Sistema

## Visão Geral

O ZF Portal Intelligence Agent é um sistema de automação inteligente projetado para identificar e converter contatos-chave da área financeira para o ZF Portal de Antecipações. Utilizando técnicas avançadas de enriquecimento de dados, comunicação personalizada e análise de métricas, o sistema automatiza o processo de prospecção e conversão de clientes potenciais.

## Arquitetura do Sistema

O sistema segue uma arquitetura modular, organizada em componentes especializados que trabalham em conjunto para automatizar o fluxo de trabalho de prospecção e conversão:

```
ZF Portal Intelligence Agent
├── Módulo de Enriquecimento de Dados
│   ├── Identificação de contatos-chave
│   ├── Extração de dados do LinkedIn
│   └── Enrichment de dados de contatos
├── Módulo de Comunicação
│   ├── Geração de mensagens personalizadas
│   └── Gerenciamento de canais de comunicação
├── Módulo de Automação
│   ├── Estratégias de interação
│   └── Funil de conversão
├── Módulo de Banco de Dados
│   ├── Persistência de dados
│   └── Gerenciamento de relacionamentos
└── Módulo de Analytics
    ├── Métricas de conversão
    └── Análise de desempenho
```

## Principais Módulos

### 1. Módulo de Enriquecimento de Dados

**Propósito**: Identificar e coletar informações detalhadas sobre contatos-chave em empresas alvo.

**Componentes Principais**:
- `ContactFinder`: Responsável por identificar contatos-chave em empresas usando LinkedIn Sales Navigator.
- `LinkedInEnrichment`: Extrai informações detalhadas dos perfis do LinkedIn dos contatos.
- `EnrichmentService`: Coordena o processo de enriquecimento de dados de contatos.

**Funcionalidades**:
- Busca automatizada de contatos com cargos específicos (CFO, Gerente Financeiro, etc.)
- Cache de resultados usando Redis para otimização de performance
- Tratamento de erros e limites de taxa (rate limiting)
- Scraping de dados detalhados de perfis do LinkedIn

### 2. Módulo de Comunicação

**Propósito**: Gerenciar a comunicação personalizada com contatos-chave.

**Componentes Principais**:
- `MessageHandler`: Gerencia a criação e envio de mensagens personalizadas.

**Funcionalidades**:
- Criação de mensagens personalizadas baseadas em dados do contato
- Gerenciamento de canais de comunicação (LinkedIn, Email, WhatsApp)
- Acompanhamento de status de mensagens (enviada, entregue, lida, respondida)

### 3. Módulo de Automação

**Propósito**: Automatizar processos de prospecção e interação com contatos.

**Componentes Principais**:
- `ProspectAutomation`: Implementa estratégias de automação de prospecção.

**Funcionalidades**:
- Geração de estratégias de interação personalizadas
- Gerenciamento do funil de conversão
- Agendamento de follow-ups automáticos

### 4. Módulo de Banco de Dados

**Propósito**: Armazenar e gerenciar dados de empresas, contatos e interações.

**Componentes Principais**:
- `ContactRepository`: Interface para operações de banco de dados relacionadas a contatos.
- Modelos ORM: `Empresa`, `Contato`, `Mensagem`, `Interacao`, `Usuario`.

**Funcionalidades**:
- Persistência de dados de empresas e contatos
- Rastreamento de histórico de interações
- Gerenciamento de usuários do sistema

### 5. Módulo de Analytics

**Propósito**: Analisar métricas de conversão e desempenho do sistema.

**Componentes Principais**:
- `ConversionAnalytics`: Realiza análises sobre taxas de conversão e eficácia.

**Funcionalidades**:
- Cálculo de taxas de conversão
- Identificação de melhores práticas
- Geração de relatórios de desempenho

## API REST

O sistema expõe uma API REST para interação com outros sistemas e interfaces de usuário.

**Componentes Principais**:
- Rotas de API para gerenciamento de empresas, contatos e interações
- Sistema de autenticação e autorização
- Validação de dados usando Pydantic

## Tecnologias Utilizadas

- **Backend**: Python 3.9+
- **ORM**: SQLAlchemy
- **API**: FastAPI
- **Banco de Dados**: SQLite (desenvolvimento), PostgreSQL (produção)
- **Cache**: Redis
- **Automação Web**: Selenium
- **Análise de Dados**: Pandas, NumPy
- **Autenticação**: JWT (JSON Web Tokens)

## Fluxo de Trabalho Principal

1. **Identificação de Empresas Alvo**:
   - Entrada manual ou via importação de dados
   - Enriquecimento de dados da empresa

2. **Identificação de Contatos-Chave**:
   - Busca automatizada no LinkedIn Sales Navigator
   - Filtragem por cargos relevantes para área financeira

3. **Enriquecimento de Dados**:
   - Extração de dados detalhados dos perfis
   - Armazenamento no banco de dados

4. **Comunicação Personalizada**:
   - Geração de mensagens personalizadas
   - Envio via canais apropriados (LinkedIn, Email)

5. **Acompanhamento e Follow-up**:
   - Monitoramento de respostas
   - Agendamento automático de follow-ups

6. **Análise de Conversão**:
   - Rastreamento de progresso no funil
   - Análise de taxas de conversão

## Configuração do Ambiente

### Variáveis de Ambiente

```
# LinkedIn Authentication
LINKEDIN_USERNAME=seu_usuario
LINKEDIN_PASSWORD=sua_senha

# Database
DATABASE_URL=sqlite:///database.db

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379

# API Authentication
SECRET_KEY=sua_chave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados
python -m src.database.init_database

# Inicializar usuário admin
python -m src.database.init_admin

# Iniciar API
python -m src.run_api
```

## Modelos de Dados

### Empresa
- `id`: Identificador único
- `cnpj`: CNPJ da empresa
- `razao_social`: Nome da empresa
- `website`: Site da empresa
- `status`: Status no funil (prospecting, contacted, negotiating, converted, rejected)
- `data_cadastro`: Data de cadastro
- `ultima_atualizacao`: Data da última atualização

### Contato
- `id`: Identificador único
- `empresa_id`: Referência à empresa
- `nome`: Nome do contato
- `cargo`: Cargo do contato
- `perfil_linkedin`: URL do perfil LinkedIn
- `email`: Email do contato
- `telefone`: Telefone fixo
- `celular`: Telefone celular
- `status`: Status no funil (identified, contacted, interested, converted)
- `data_captura`: Data de captura
- `ultima_atualizacao`: Data da última atualização

### Mensagem
- `id`: Identificador único
- `contato_id`: Referência ao contato
- `canal`: Canal de comunicação (linkedin, email, whatsapp, sms)
- `conteudo`: Conteúdo da mensagem
- `data_envio`: Data de envio
- `status`: Status da mensagem (sent, delivered, read, replied)
- `resposta`: Resposta recebida
- `data_resposta`: Data da resposta
- `observacoes`: Observações adicionais

### Interação
- `id`: Identificador único
- `contato_id`: Referência ao contato
- `tipo`: Tipo de interação (call, meeting, email_open, link_click)
- `data`: Data da interação
- `descricao`: Descrição da interação
- `status_conversao`: Status de conversão (interested, not_interested, follow_up, converted)

### Usuário
- `id`: Identificador único
- `username`: Nome de usuário
- `email`: Email do usuário
- `full_name`: Nome completo
- `hashed_password`: Senha criptografada
- `is_active`: Status de ativação
- `created_at`: Data de criação
