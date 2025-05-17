"""
Pacote de integração WhatsApp para ZF Portal Intelligence Agent

Este pacote implementa a integração com WhatsApp através da API WAHA,
permitindo comunicação bidirecional com leads e clientes.
"""

from .whatsapp_connector import WhatsAppConnector, MessageType
from .whatsapp_session_manager import WhatsAppSessionManager, SessionStatus
from .whatsapp_message_handler import WhatsAppMessageHandler, FunnelStage, MessageIntent
from .whatsapp_webhook_handler import WhatsAppWebhookHandler, WhatsAppWebhookRouter
from .waha_setup import WAHASetup

__all__ = [
    'WhatsAppConnector',
    'MessageType',
    'WhatsAppSessionManager',
    'SessionStatus',
    'WhatsAppMessageHandler',
    'FunnelStage',
    'MessageIntent',
    'WhatsAppWebhookHandler',
    'WhatsAppWebhookRouter',
    'WAHASetup'
]
