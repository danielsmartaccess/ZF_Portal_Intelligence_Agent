#!/usr/bin/env python
"""
Servidor mock para simular a API backend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import random
from datetime import datetime, timedelta

app = FastAPI(title="ZF Portal API Mock")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos para API mock
class Contact(BaseModel):
    id: int
    name: str
    company: str
    position: str
    email: str
    phone: str
    linkedin: str
    status: str
    last_interaction: datetime
    engagement_score: float

class Metric(BaseModel):
    label: str
    value: float
    change: float
    trend: str

class ChartData(BaseModel):
    name: str
    series: List[Dict[str, Any]]

# Dados mock
contacts = [
    {
        "id": i,
        "name": f"Contato {i}",
        "company": random.choice(["Bosch", "Mercedes-Benz", "Volkswagen", "ZF"]),
        "position": random.choice(["Diretor Financeiro", "Gerente Financeiro", "Controller"]),
        "email": f"contato{i}@empresa.com",
        "phone": f"(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
        "linkedin": f"https://linkedin.com/in/contato{i}",
        "status": random.choice(["Novo", "Contatado", "Interessado", "Negociando", "Convertido"]),
        "last_interaction": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
        "engagement_score": random.uniform(0, 10)
    } for i in range(1, 51)
]

metrics = [
    {"label": "Contatos Totais", "value": 245, "change": 12.5, "trend": "up"},
    {"label": "Interações", "value": 1289, "change": 8.3, "trend": "up"},
    {"label": "Taxa de Conversão", "value": 18.5, "change": 2.1, "trend": "up"},
    {"label": "Tempo Médio de Resposta", "value": 3.2, "change": -0.8, "trend": "down"}
]

chart_data = [
    {
        "name": "Funil de Marketing",
        "series": [
            {"name": "Atração", "value": 100},
            {"name": "Interesse", "value": 65},
            {"name": "Consideração", "value": 40},
            {"name": "Intenção", "value": 25},
            {"name": "Avaliação", "value": 15},
            {"name": "Conversão", "value": 10}
        ]
    },
    {
        "name": "Interações por Canal",
        "series": [
            {"name": "WhatsApp", "value": 45},
            {"name": "Email", "value": 30},
            {"name": "LinkedIn", "value": 25}
        ]
    },
    {
        "name": "Conversões por Semana",
        "series": [
            {"name": "Semana 1", "value": 3},
            {"name": "Semana 2", "value": 4},
            {"name": "Semana 3", "value": 7},
            {"name": "Semana 4", "value": 5}
        ]
    }
]

@app.get("/")
def read_root():
    return {"message": "ZF Portal API Mock"}

@app.get("/api/v1/metrics")
def get_metrics():
    return metrics

@app.get("/api/v1/charts/{chart_type}")
def get_chart_data(chart_type: str):
    for chart in chart_data:
        if chart_type.lower() in chart["name"].lower():
            return chart
    return chart_data[0]

@app.get("/api/v1/contacts")
def list_contacts(
    skip: int = 0, 
    limit: int = 10, 
    company: Optional[str] = None, 
    status: Optional[str] = None
):
    filtered = contacts
    
    if company:
        filtered = [c for c in filtered if company.lower() in c["company"].lower()]
        
    if status:
        filtered = [c for c in filtered if status.lower() in c["status"].lower()]
        
    return {
        "total": len(filtered),
        "items": filtered[skip:skip+limit]
    }

@app.get("/api/v1/contacts/{contact_id}")
def get_contact(contact_id: int):
    for contact in contacts:
        if contact["id"] == contact_id:
            return contact
    raise HTTPException(status_code=404, detail="Contact not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
