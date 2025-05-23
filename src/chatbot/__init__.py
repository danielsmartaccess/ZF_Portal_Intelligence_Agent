"""
Módulo de chatbot para integração com WhatsApp

Este módulo implementa a lógica do chatbot para comunicação via WhatsApp
através da integração com WAHA (WhatsApp HTTP API).
"""

from .chatbot_handler import ChatbotHandler, ChatbotResponse
from .chatbot_service import ChatbotService

__all__ = [
    'ChatbotHandler',
    'ChatbotResponse',
    'ChatbotService'
]
