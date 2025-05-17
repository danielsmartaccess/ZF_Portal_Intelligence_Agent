"""
Pacote de integração com Modelos de Linguagem (LLM) para ZF Portal Intelligence Agent

Este pacote implementa a interface com diferentes modelos de linguagem para
fornecer análise de mensagens, geração de respostas personalizadas e
processamento de interações no funil de marketing.
"""

from .llm_interface import (
    BaseLLMInterface,
    OpenAIInterface,
    AzureOpenAIInterface,
    LLMProvider,
    LLMInterfaceFactory
)

__all__ = [
    'BaseLLMInterface',
    'OpenAIInterface',
    'AzureOpenAIInterface',
    'LLMProvider',
    'LLMInterfaceFactory'
]
