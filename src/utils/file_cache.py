"""
Módulo de cache baseado em arquivos para substituir o Redis
quando não for possível instalar o Redis no ambiente.
"""
import os
import json
import time
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FileCache:
    """
    Implementação de cache baseado em arquivos.
    Simula as funcionalidades básicas do Redis para armazenamento de cache.
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Inicializa o cache baseado em arquivos.
        
        Args:
            cache_dir: Diretório para armazenar os arquivos de cache.
                       Se não for fornecido, usa o diretório 'cache' na raiz do projeto.
        """
        if cache_dir is None:
            # Usa o diretório 'cache' na raiz do projeto
            root_dir = Path(__file__).parent.parent.parent
            cache_dir = os.path.join(root_dir, 'cache')
        
        self.cache_dir = cache_dir
        
        # Cria o diretório de cache se não existir
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Cache inicializado no diretório: {self.cache_dir}")
    
    def _get_cache_path(self, key: str) -> str:
        """
        Obtém o caminho do arquivo de cache para uma chave.
        
        Args:
            key: Chave do cache
            
        Returns:
            Caminho do arquivo de cache
        """
        # Substitui caracteres não permitidos em nomes de arquivo
        safe_key = key.replace(':', '_').replace('/', '_').replace('\\', '_')
        return os.path.join(self.cache_dir, f"{safe_key}.cache")
    
    def set(self, key: str, value: Any, ex: int = None) -> bool:
        """
        Define um valor no cache.
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ex: Tempo de expiração em segundos (opcional)
            
        Returns:
            True se o valor foi armazenado com sucesso
        """
        try:
            cache_path = self._get_cache_path(key)
            
            # Prepara os dados para armazenamento
            cache_data = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ex if ex else None
            }
            
            # Salva os dados no arquivo
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            return True
        except Exception as e:
            logger.error(f"Erro ao definir cache para chave {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            Valor armazenado ou None se não encontrado ou expirado
        """
        try:
            cache_path = self._get_cache_path(key)
            
            # Verifica se o arquivo de cache existe
            if not os.path.exists(cache_path):
                return None
            
            # Carrega os dados do arquivo
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verifica se o cache expirou
            if cache_data['expires_at'] and time.time() > cache_data['expires_at']:
                # Remove o arquivo de cache expirado
                os.remove(cache_path)
                return None
            
            return cache_data['value']
        except Exception as e:
            logger.error(f"Erro ao obter cache para chave {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Remove um valor do cache.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se o valor foi removido com sucesso
        """
        try:
            cache_path = self._get_cache_path(key)
            
            # Verifica se o arquivo de cache existe
            if os.path.exists(cache_path):
                os.remove(cache_path)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao remover cache para chave {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verifica se uma chave existe no cache e não está expirada.
        
        Args:
            key: Chave do cache
            
        Returns:
            True se a chave existe e não está expirada
        """
        try:
            value = self.get(key)
            return value is not None
        except:
            return False
    
    def ping(self) -> bool:
        """
        Verifica se o cache está funcionando.
        
        Returns:
            True se o cache está funcionando
        """
        try:
            test_key = "ping_test"
            test_value = "pong"
            
            # Tenta definir e obter um valor de teste
            self.set(test_key, test_value)
            result = self.get(test_key)
            self.delete(test_key)
            
            return result == test_value
        except:
            return False
    
    def clear(self) -> bool:
        """
        Limpa todo o cache.
        
        Returns:
            True se o cache foi limpo com sucesso
        """
        try:
            for file_name in os.listdir(self.cache_dir):
                if file_name.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, file_name))
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False
