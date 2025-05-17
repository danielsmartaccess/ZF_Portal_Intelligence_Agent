"""
Pacote de marketing para ZF Portal Intelligence Agent

Este pacote implementa funcionalidades para gerenciamento do funil de marketing,
classificação de leads e automação de comunicações personalizadas.
"""

from .funnel_manager import FunnelManager, LeadClassifier, FunnelStage, LeadScore

__all__ = [
    'FunnelManager',
    'LeadClassifier',
    'FunnelStage',
    'LeadScore'
]
