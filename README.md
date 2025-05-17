# ZF Portal Intelligence Agent

Este projeto implementa um agente inteligente para identificação e conversão de contatos-chave da área financeira para o ZF Portal de Antecipações.

## Funcionalidades Principais

- Enriquecimento de dados de contatos
- Comunicação personalizada automatizada via WhatsApp
- Integração com modelos de linguagem (LLM) para personalização de mensagens
- Automação inteligente do funil de marketing (Atração, Relacionamento e Conversão)
- Automação de processos de prospecção
- Análise de métricas de conversão
- Gestão de relacionamento com contatos-chave

## Módulos

1. **Data Enrichment**: Identificação e enriquecimento de dados de contatos
2. **Communication**: Sistema de comunicação personalizada
3. **WhatsApp**: Integração com WhatsApp Web API (WAHA)
4. **LLM**: Interface para modelos de linguagem natural
5. **Marketing**: Gerenciamento inteligente de funil de marketing
6. **Templates**: Sistema de templates personalizáveis
7. **Automation**: Automação de processos de prospecção
8. **Database**: Gestão de dados e relacionamentos
9. **Analytics**: Análise de métricas e resultados

## Configuração do Ambiente

### Requisitos

- Python 3.9+ 
- Docker e Docker Compose (para WhatsApp WAHA)
- Redis (opcional, para cache e filas)

### Passos para instalação

1. Crie um ambiente virtual Python:
   
   ```bash
   python -m venv venv
   ```

2. Ative o ambiente virtual:
   - Windows:
     
     ```bash
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     
     ```bash
     source venv/bin/activate
     ```

3. Instale as dependências:
   
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione as variáveis necessárias (ver `.env.example`)

5. Configure e inicie os serviços do Docker:
   
   ```bash
   python setup_waha.py
   ```
   
   Ou use Docker Compose para iniciar todos os serviços:
   
   ```bash
   docker-compose up -d
   ```

6. Inicie o sistema completo com um único comando:
   
   ```bash
   python run_system.py
   ```

## Estrutura do Projeto

```
zf_portal_agent/
├── src/
│   ├── data_enrichment/
│   ├── communication/
│   ├── automation/
│   ├── database/
│   └── analytics/
├── config/
├── tests/
├── requirements.txt
└── README.md
```

## Tecnologias Utilizadas

- Python 3.9+
- SQLAlchemy (Database ORM)
- FastAPI (API REST)
- Pandas (Análise de dados)
- Selenium (Automação web)

## Política de Privacidade

Nossa política de privacidade está disponível em:
https://danielsmartaccess.github.io/ZF_Portal_Intelligence_Agent/privacy-policy.html

## Integração WhatsApp e LLM

### Configuração do WhatsApp

A integração com WhatsApp usa o projeto WAHA (WhatsApp HTTP API) que cria uma API REST para o WhatsApp Web.

1. Inicie o servidor WAHA:

   ```bash
   python setup_waha.py
   ```

2. Escaneie o QR Code para autenticar:

   ```bash
   curl -X GET "http://localhost:8000/api/v1/whatsapp/sessions/qr-code" -H "accept: application/json"
   ```
   
   Ou acesse a URL no navegador: http://localhost:8000/api/v1/whatsapp/sessions/qr-code

3. Envie uma mensagem de teste:

   ```bash
   curl -X POST "http://localhost:8000/api/v1/whatsapp/messages/send" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"recipient":"5511999999999","message":"Olá! Esta é uma mensagem de teste.","message_type":"text"}'
   ```

### Configuração do LLM

1. Configure sua chave API no arquivo `.env`:

   ```
   LLM_PROVIDER=openai
   LLM_API_KEY=sua-chave-api-aqui
   LLM_MODEL=gpt-4o
   ```

2. Teste a integração com o LLM:

   ```bash
   curl -X POST "http://localhost:8000/api/v1/funnel/classify" \
     -H "accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{"contato_id":1,"analyze_messages":true}'
   ```

### Gerenciamento de Funil

Acesse as rotas de gerenciamento de funil através da API:

```
http://localhost:8000/api/v1/docs
```

## Próximos Passos

1. Desenvolver interface de usuário para visualização e gestão do funil
2. Implementar métricas e relatórios de desempenho
3. Otimizar fluxos de comunicação automática
4. Expandir integrações com outras plataformas
