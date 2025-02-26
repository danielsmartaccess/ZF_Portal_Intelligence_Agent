# ZF Portal Intelligence Agent

Este projeto implementa um agente inteligente para identificação e conversão de contatos-chave da área financeira para o ZF Portal de Antecipações.

## Funcionalidades Principais

- Enriquecimento de dados de contatos
- Comunicação personalizada automatizada
- Automação de processos de prospecção
- Análise de métricas de conversão
- Gestão de relacionamento com contatos-chave

## Módulos

1. **Data Enrichment**: Identificação e enriquecimento de dados de contatos
2. **Communication**: Sistema de comunicação personalizada
3. **Automation**: Automação de processos de prospecção
4. **Database**: Gestão de dados e relacionamentos
5. **Analytics**: Análise de métricas e resultados

## Configuração do Ambiente

1. Crie um ambiente virtual Python:
   ```
   python -m venv venv
   ```

2. Ative o ambiente virtual:
   - Windows:
     ```
     .\venv\Scripts\activate
     ```
   - Linux/Mac:
     ```
     source venv/bin/activate
     ```

3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Adicione as variáveis necessárias (ver `.env.example`)

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

## Próximos Passos

1. Configurar banco de dados
2. Implementar módulo de enriquecimento de dados
3. Desenvolver sistema de comunicação
4. Criar automações de processos
5. Implementar análises e métricas
