# Manual de Uso: Integração WhatsApp e LLM no ZF Portal Intelligence Agent

Este documento detalha como utilizar as funcionalidades da integração de WhatsApp e Modelo de Linguagem (LLM) para automação inteligente do funil de marketing.

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Configuração Inicial](#2-configuração-inicial)
   - [Requisitos de Sistema](#21-requisitos-de-sistema)
   - [Instalação](#22-instalação)
   - [Configuração do WhatsApp](#23-configuração-do-whatsapp)
   - [Configuração do LLM](#24-configuração-do-llm)
3. [Administração do Sistema](#3-administração-do-sistema)
   - [Inicialização dos Serviços](#31-inicialização-dos-serviços)
   - [Monitoramento](#32-monitoramento)
   - [Backup e Manutenção](#33-backup-e-manutenção)
4. [Utilizando o Funil de Marketing](#4-utilizando-o-funil-de-marketing)
   - [Estágios do Funil](#41-estágios-do-funil)
   - [Gerenciamento de Contatos](#42-gerenciamento-de-contatos)
   - [Templates de Mensagens](#43-templates-de-mensagens)
   - [Agendamento de Mensagens](#44-agendamento-de-mensagens)
5. [API de Integração](#5-api-de-integração)
   - [Autenticação](#51-autenticação)
   - [Endpoints do WhatsApp](#52-endpoints-do-whatsapp)
   - [Endpoints do Funil](#53-endpoints-do-funil)
   - [Exemplos de Uso](#54-exemplos-de-uso)
6. [Solução de Problemas](#6-solução-de-problemas)
7. [Perguntas Frequentes](#7-perguntas-frequentes)

## 1. Visão Geral

A integração de WhatsApp e LLM no ZF Portal Intelligence Agent permite automatizar a comunicação com leads e clientes potenciais, utilizando inteligência artificial para personalizar mensagens e classificar contatos nas diferentes etapas do funil de marketing.

O sistema é composto por:

- **WhatsApp Web API (WAHA)**: Permite enviar e receber mensagens via WhatsApp
- **Interface LLM**: Integra com modelos de linguagem para análise e geração de conteúdo
- **Sistema de Funil de Marketing**: Gerencia contatos em diferentes estágios do processo
- **Agendador de Mensagens**: Programa envios automáticos em horários estratégicos
- **Templates Personalizáveis**: Cria mensagens adaptadas a cada estágio e contato

## 2. Configuração Inicial

### 2.1 Requisitos de Sistema

- Python 3.9 ou superior
- Docker e Docker Compose
- Redis (para cache e filas)
- Acesso à internet para comunicação com APIs externas

### 2.2 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/zf-portal-intelligence-agent.git
   cd zf-portal-intelligence-agent
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Edite o arquivo .env com suas configurações
   ```

### 2.3 Configuração do WhatsApp

1. Execute o script de configuração do servidor WAHA:
   ```bash
   python setup_waha.py
   ```

2. Inicie a API:
   ```bash
   python run_api.py
   ```

3. Obtenha o QR Code para autenticação do WhatsApp:
   - Acesse: http://localhost:8000/api/v1/whatsapp/sessions/qr-code
   - Escaneie o QR Code com o WhatsApp do número a ser utilizado

4. Verifique o status da conexão:
   - Acesse: http://localhost:8000/api/v1/whatsapp/sessions/status

### 2.4 Configuração do LLM

1. Obtenha uma chave API para o provedor escolhido:
   - [OpenAI](https://platform.openai.com/account/api-keys)
   - [Azure OpenAI](https://azure.microsoft.com/pt-br/products/cognitive-services/openai-service)

2. Edite as configurações no arquivo `.env`:
   ```
   LLM_PROVIDER=openai
   LLM_API_KEY=sua-chave-api-aqui
   LLM_MODEL=gpt-4o
   LLM_TEMPERATURE=0.7
   ```

3. Teste a integração com o LLM:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/funnel/classify" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"contato_id":1,"analyze_messages":true}'
   ```

## 3. Administração do Sistema

### 3.1 Inicialização dos Serviços

Para iniciar todos os serviços com um único comando:

```bash
python run_system.py
```

Este script inicializa:
- Servidor WAHA para WhatsApp
- Redis para cache e filas
- API FastAPI
- Agendador de mensagens

Para iniciar componentes individualmente:

1. WhatsApp WAHA:
   ```bash
   python setup_waha.py
   ```

2. API:
   ```bash
   python run_api.py
   ```

3. Docker Compose (todos os serviços de infraestrutura):
   ```bash
   docker-compose up -d
   ```

### 3.2 Monitoramento

#### Logs do Servidor WAHA

```bash
docker logs -f zf-portal-waha
```

#### Logs da API (quando executada com run_system.py)

Os logs são exibidos diretamente no console.

#### Monitoramento do Redis

```bash
docker exec -it zf-portal-redis redis-cli
> MONITOR
```

### 3.3 Backup e Manutenção

#### Backup do Banco de Dados

```bash
# Criar cópia do arquivo SQLite
cp database.db database.db.bkp-$(date +%Y%m%d)
```

#### Backup das Sessões WhatsApp

As sessões são armazenadas em `waha-data/`. Faça backup periódico desta pasta.

```bash
cp -r waha-data/ waha-data-backup-$(date +%Y%m%d)
```

## 4. Utilizando o Funil de Marketing

### 4.1 Estágios do Funil

O sistema utiliza quatro estágios principais:

1. **Atração (Attraction)**
   - Objetivo: Criar consciência da marca e despertar interesse inicial
   - Conteúdo típico: Informações sobre o mercado, problemas comuns, benefícios gerais

2. **Relacionamento (Relationship)**
   - Objetivo: Construir relacionamento e credibilidade
   - Conteúdo típico: Conteúdo educativo, casos de uso, depoimentos

3. **Conversão (Conversion)**
   - Objetivo: Transformar interesse em decisão de compra
   - Conteúdo típico: Vantagens competitivas, propostas de valor, condições comerciais

4. **Cliente (Customer)**
   - Objetivo: Manter relacionamento após conversão
   - Conteúdo típico: Suporte, upsell, indicações

#### Criando um Estágio

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/stages" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "attraction",
    "description": "Estágio de atração de leads",
    "order": 1
  }'
```

### 4.2 Gerenciamento de Contatos

#### Adicionando um Contato ao Funil

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/contacts" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "stage_id": 1,
    "score": 50,
    "qualification": "cold",
    "notes": "Lead captado via LinkedIn"
  }'
```

#### Atualizando o Estágio de um Contato

```bash
curl -X PUT "http://localhost:8000/api/v1/funnel/contacts/1" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "stage_id": 2,
    "qualification": "warm"
  }'
```

#### Classificação Automática de Leads

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/classify" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "analyze_messages": true,
    "analyze_interactions": true
  }'
```

### 4.3 Templates de Mensagens

#### Criando um Template

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/templates" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Apresentação Inicial",
    "description": "Mensagem de primeiro contato",
    "stage_id": 1,
    "content": "Olá {{nome}}, tudo bem? Sou {{representante}} do ZF Portal e gostaria de apresentar nossa solução de antecipação para fornecedores que pode ajudar a {{empresa}}.",
    "message_type": "text",
    "variables": ["nome", "representante", "empresa"]
  }'
```

#### Utilizando um Template

```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/messages/send" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "5511999999999",
    "message_type": "template",
    "template_id": 1,
    "template_data": {
      "nome": "João Silva",
      "representante": "Carlos",
      "empresa": "Empresa XYZ"
    }
  }'
```

### 4.4 Agendamento de Mensagens

#### Agendando uma Mensagem

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/schedule" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "message_type": "text",
    "content": "Olá! Apenas verificando se recebeu nossa proposta.",
    "scheduled_time": "2023-05-20T14:30:00"
  }'
```

#### Agendando com Template

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/schedule" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "message_type": "template",
    "template_id": 1,
    "template_data": {
      "nome": "João Silva",
      "representante": "Carlos",
      "empresa": "Empresa XYZ"
    },
    "scheduled_time": "2023-05-20T14:30:00"
  }'
```

#### Processando a Fila de Mensagens

O processamento é automático através do agendador. Para forçar um processamento:

```bash
curl -X POST "http://localhost:8000/api/v1/funnel/process-queue" \
  -H "accept: application/json"
```

## 5. API de Integração

### 5.1 Autenticação

A API utiliza autenticação JWT. Para obter um token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

Adicione o token nos headers das requisições:

```bash
-H "Authorization: Bearer seu-token-aqui"
```

### 5.2 Endpoints do WhatsApp

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | /api/v1/whatsapp/sessions | Inicia sessão WhatsApp |
| GET | /api/v1/whatsapp/sessions/qr-code | Obtém QR Code |
| GET | /api/v1/whatsapp/sessions/status | Verifica status da sessão |
| POST | /api/v1/whatsapp/sessions/restart | Reinicia sessão |
| POST | /api/v1/whatsapp/messages/send | Envia mensagem |
| POST | /api/v1/whatsapp/check-number | Verifica existência de número |

### 5.3 Endpoints do Funil

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | /api/v1/funnel/stages | Lista estágios do funil |
| POST | /api/v1/funnel/stages | Cria estágio |
| GET | /api/v1/funnel/contacts | Lista contatos no funil |
| POST | /api/v1/funnel/contacts | Adiciona contato ao funil |
| PUT | /api/v1/funnel/contacts/{id} | Atualiza contato no funil |
| POST | /api/v1/funnel/classify | Classifica lead |
| GET | /api/v1/funnel/templates | Lista templates |
| POST | /api/v1/funnel/templates | Cria template |
| POST | /api/v1/funnel/schedule | Agenda mensagem |
| GET | /api/v1/funnel/schedule | Lista mensagens agendadas |
| POST | /api/v1/funnel/process-queue | Processa fila de mensagens |

### 5.4 Exemplos de Uso

#### Fluxo Completo de Onboarding de Lead

1. Verificar número no WhatsApp:
```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/check-number" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"number":"5511999999999"}'
```

2. Adicionar ao funil como lead inicial:
```bash
curl -X POST "http://localhost:8000/api/v1/funnel/contacts" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "stage_id": 1,
    "score": 30,
    "qualification": "cold"
  }'
```

3. Enviar mensagem inicial:
```bash
curl -X POST "http://localhost:8000/api/v1/whatsapp/messages/send" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "5511999999999",
    "message_type": "text",
    "message": "Olá João, tudo bem? Sou Carlos do ZF Portal e gostaria de apresentar nossa solução que pode beneficiar a Empresa XYZ."
  }'
```

4. Agendar follow-up para 2 dias depois:
```bash
curl -X POST "http://localhost:8000/api/v1/funnel/schedule" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{
    "contato_id": 1,
    "message_type": "text",
    "content": "Olá João, estou disponível para esclarecer qualquer dúvida sobre o ZF Portal. Quando podemos conversar?",
    "scheduled_time": "2023-05-22T10:30:00"
  }'
```

## 6. Solução de Problemas

### Problemas com Sessão WhatsApp

1. **QR Code não aparece ou expira**
   - Reinicie a sessão: `http://localhost:8000/api/v1/whatsapp/sessions/restart`
   - Verifique logs do container: `docker logs zf-portal-waha`

2. **Mensagens não são enviadas**
   - Verifique status da sessão: `http://localhost:8000/api/v1/whatsapp/sessions/status`
   - Confirme se o número está no formato correto (ex: 5511999999999)

3. **Container WAHA não inicia**
   - Verifique se a porta 3000 está disponível
   - Tente reiniciar o Docker: `docker restart zf-portal-waha`

### Problemas com LLM

1. **Erros de API**
   - Verifique se a chave API está correta
   - Confirme se há saldo disponível na conta

2. **Classificação incorreta**
   - Verifique logs para entender o contexto usado
   - Ajuste parâmetros como temperatura para maior precisão

## 7. Perguntas Frequentes

### Gerais

1. **Quantas sessões de WhatsApp posso ter?**
   - O WAHA suporta múltiplas sessões, mas cada uma requer um número diferente.

2. **O sistema funciona com WhatsApp Business?**
   - Sim, tanto WhatsApp pessoal quanto Business são suportados.

3. **As mensagens são armazenadas?**
   - Sim, para fins de análise e histórico, com criptografia no banco de dados.

### Técnicas

1. **Qual banco de dados é utilizado?**
   - SQLite por padrão, mas pode ser configurado para PostgreSQL ou MySQL.

2. **Posso usar outro provedor de LLM?**
   - Sim, a interface é extensível para outros provedores além de OpenAI e Azure.

3. **Como escalar para mais contatos?**
   - Para volumes maiores, considere:
     - Migrar para banco de dados PostgreSQL
     - Utilizar sistema de filas distribuído
     - Configurar múltiplas instâncias WAHA
     
4. **Quais são os limites do WhatsApp?**
   - O WhatsApp tem limites de envio que variam conforme o tipo de conta
   - Para contas pessoais: aproximadamente 200 mensagens/dia
   - Para WhatsApp Business API: limites mais altos baseados em métricas de qualidade
