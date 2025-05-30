#!/usr/bin/env python3
"""
Script simples para iniciar a API FastAPI básica sem dependências complexas
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Criar aplicação FastAPI básica
app = FastAPI(
    title="ZF Portal Intelligence Agent API",
    description="API simples para o ZF Portal Intelligence Agent",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ZF Portal Intelligence Agent API está rodando!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ZF Portal Intelligence Agent"}

@app.get("/api/status")
async def api_status():
    return {
        "api": "online",
        "database": "sqlite",
        "whatsapp": "not_connected",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("🚀 Iniciando ZF Portal Intelligence Agent API...")
    print("📡 API disponível em: http://localhost:8000")
    print("📚 Documentação em: http://localhost:8000/docs")
    uvicorn.run(
        "run_simple_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
