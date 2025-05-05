# ZF Portal Intelligence Agent Dashboard

Frontend Angular para o dashboard do ZF Portal Intelligence Agent, proporcionando visualização de métricas, dados de contatos e interações.

## Estrutura do Projeto

```
/frontend
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   ├── dashboard/
│   │   │   ├── metrics-card/
│   │   │   └── contact-table/
│   │   ├── services/
│   │   │   └── api.service.ts
│   │   ├── app.component.ts
│   │   └── app.module.ts
│   ├── assets/
│   ├── environments/
│   ├── index.html
│   ├── main.ts
│   ├── polyfills.ts
│   └── styles.css
├── angular.json
├── package.json
├── proxy.conf.json
├── tsconfig.json
└── tsconfig.app.json
```

## Funcionalidades

- **Dashboard com Métricas**: Visualização de indicadores-chave como total de contatos, interações, taxa de conversão e tempo médio de resposta
- **Gráficos Interativos**: Usando ngx-charts para mostrar tendências e dados analíticos
- **Tabela de Contatos**: Lista paginada e pesquisável de contatos com informações detalhadas
- **Design Responsivo**: Interface adaptável a diferentes tamanhos de tela
- **Integração com Backend**: Comunicação com a API FastAPI através de serviços HTTP

## Requisitos

- Node.js (versão 16.x ou superior)
- NPM (versão 8.x ou superior)
- Angular CLI (versão 17.x)

## Como Instalar

1. Instale as dependências:
```bash
cd frontend
npm install
```

2. Certifique-se de que o backend está rodando em `http://localhost:8000`

## Como Executar

Execute o servidor de desenvolvimento:
```bash
npm start
```

O frontend estará disponível em `http://localhost:4200`

## Integração com o Backend

A comunicação com o backend é feita através do proxy configurado em `proxy.conf.json`, redirecionando todas as chamadas a `/api/*` para o servidor backend em `http://localhost:8000`.

Os serviços Angular em `services/api.service.ts` encapsulam as chamadas HTTP para os endpoints da API.
