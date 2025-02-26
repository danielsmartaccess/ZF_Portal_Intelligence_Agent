"""
Script para executar a API FastAPI
"""
import uvicorn
import string
from src.api.main import app

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
