"""
Pacote de gerenciamento de templates para ZF Portal Intelligence Agent

Este pacote implementa o gerenciamento de templates para mensagens
personalizadas em diferentes estágios do funil de marketing.
"""

from .templates_manager import TemplatesManager, FunnelTemplatesManager

__all__ = [
    'TemplatesManager',
    'FunnelTemplatesManager'
]
