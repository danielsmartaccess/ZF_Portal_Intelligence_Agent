"""
Módulo para gerenciamento de sessões WhatsApp

Este módulo implementa o gerenciamento de sessões para conexão
com WhatsApp através da API WAHA, incluindo autenticação QR,
status de conexão e persistência de sessão.
"""

import os
import json
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .whatsapp_connector import WhatsAppConnector

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("whatsapp_session_manager")


class SessionStatus:
    """Enumeração para estados da sessão WhatsApp"""
    INITIALIZING = "INITIALIZING"
    SCAN_QR_CODE = "SCAN_QR_CODE"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"
    DISCONNECTED = "DISCONNECTED"
    STOPPED = "STOPPED"


class WhatsAppSessionManager:
    """
    Classe para gerenciamento de sessões WhatsApp via WAHA
    """
    
    def __init__(
        self, 
        base_url: str, 
        api_key: str,
        session_id: str = "default",
        sessions_dir: str = None,
        auto_reconnect: bool = True
    ):
        """
        Inicializa o gerenciador de sessões WhatsApp
        
        Args:
            base_url: URL base do servidor WAHA
            api_key: Chave API para autenticação
            session_id: Identificador da sessão (padrão: "default")
            sessions_dir: Diretório para armazenar dados de sessão
            auto_reconnect: Se deve reconectar automaticamente em caso de desconexão
        """
        self.base_url = base_url
        self.api_key = api_key
        self.session_id = session_id
        self.sessions_dir = sessions_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
        self.auto_reconnect = auto_reconnect
        self.status = SessionStatus.INITIALIZING
        self.connector = WhatsAppConnector(base_url, api_key, session_id)
        self.qr_code = None
        self.last_activity = datetime.now()
        self.status_listeners: List[Callable[[str], None]] = []
        self.monitoring_thread = None
        self.should_monitor = False
        
        # Garante que o diretório de sessões existe
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
    
    def add_status_listener(self, callback: Callable[[str], None]) -> None:
        """
        Adiciona um listener para mudanças de status da sessão
        
        Args:
            callback: Função de callback que recebe o novo status como parâmetro
        """
        self.status_listeners.append(callback)
    
    def remove_status_listener(self, callback: Callable[[str], None]) -> None:
        """
        Remove um listener para mudanças de status da sessão
        
        Args:
            callback: Função de callback a ser removida
        """
        if callback in self.status_listeners:
            self.status_listeners.remove(callback)
    
    def _notify_status_change(self, new_status: str) -> None:
        """
        Notifica todos os listeners sobre mudança de status
        
        Args:
            new_status: Novo status da sessão
        """
        self.status = new_status
        for listener in self.status_listeners:
            try:
                listener(new_status)
            except Exception as e:
                logger.error(f"Erro ao notificar listener de status: {e}")
    
    def session_file_path(self) -> str:
        """
        Retorna o caminho para o arquivo de dados da sessão
        
        Returns:
            str: Caminho para o arquivo de sessão
        """
        return os.path.join(self.sessions_dir, f"{self.session_id}.json")
    
    def save_session_data(self, data: Dict[str, Any]) -> bool:
        """
        Salva os dados da sessão em arquivo
        
        Args:
            data: Dados da sessão
        
        Returns:
            bool: True se os dados foram salvos com sucesso
        """
        try:
            with open(self.session_file_path(), 'w') as file:
                json.dump(data, file, indent=4)
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados da sessão: {e}")
            return False
    
    def load_session_data(self) -> Optional[Dict[str, Any]]:
        """
        Carrega os dados da sessão do arquivo
        
        Returns:
            Dict: Dados da sessão ou None se o arquivo não existir
        """
        file_path = self.session_file_path()
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Erro ao carregar dados da sessão: {e}")
            return None
    
    def update_session_data(self, key: str, value: Any) -> None:
        """
        Atualiza um valor específico nos dados da sessão
        
        Args:
            key: Chave a ser atualizada
            value: Novo valor
        """
        data = self.load_session_data() or {}
        data[key] = value
        data["last_updated"] = datetime.now().isoformat()
        self.save_session_data(data)
    
    def start(self) -> bool:
        """
        Inicia a sessão WhatsApp
        
        Returns:
            bool: True se a sessão foi iniciada com sucesso
        """
        try:
            self._notify_status_change(SessionStatus.INITIALIZING)
            logger.info(f"Iniciando sessão WhatsApp: {self.session_id}")
            
            # Inicia a sessão no WAHA
            response = self.connector.start_session()
            
            # Verifica o status inicial após iniciar
            status_response = self.connector.check_session_status()
            current_status = status_response.get("status", SessionStatus.INITIALIZING)
            
            if current_status == "CONNECTED":
                self._notify_status_change(SessionStatus.CONNECTED)
                self.update_session_data("status", SessionStatus.CONNECTED)
                self.update_session_data("qr_code", None)
                self._start_monitoring()
                return True
            
            # Se não estiver conectado, pode ser necessário escanear o QR
            if current_status in ["INITIALIZING", "SCAN_QR_CODE"]:
                self._notify_status_change(SessionStatus.SCAN_QR_CODE)
                self._get_and_store_qr_code()
                self._start_monitoring()
                return True
            
            # Se chegou aqui, algo deu errado
            logger.error(f"Sessão não pôde ser iniciada: {status_response}")
            self._notify_status_change(SessionStatus.FAILED)
            return False
            
        except Exception as e:
            logger.error(f"Erro ao iniciar sessão: {e}")
            self._notify_status_change(SessionStatus.FAILED)
            return False
    
    def _get_and_store_qr_code(self) -> Optional[str]:
        """
        Obtém o código QR e armazena nos dados da sessão
        
        Returns:
            str: URL do código QR ou None se houver falha
        """
        try:
            qr_response = self.connector.get_qr_code()
            if "qr" in qr_response:
                qr_code = qr_response["qr"]
                self.qr_code = qr_code
                self.update_session_data("qr_code", qr_code)
                self.update_session_data("qr_timestamp", datetime.now().isoformat())
                return qr_code
            
            logger.warning(f"QR code não disponível: {qr_response}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter QR code: {e}")
            return None
    
    def get_qr_code(self) -> Optional[str]:
        """
        Retorna o código QR atual
        
        Returns:
            str: URL do código QR ou None se não disponível
        """
        return self.qr_code
    
    def stop(self) -> bool:
        """
        Para a sessão WhatsApp
        
        Returns:
            bool: True se a sessão foi parada com sucesso
        """
        try:
            # Para o monitoramento
            self._stop_monitoring()
            
            logger.info(f"Parando sessão WhatsApp: {self.session_id}")
            response = self.connector.stop_session()
            
            self._notify_status_change(SessionStatus.STOPPED)
            self.update_session_data("status", SessionStatus.STOPPED)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao parar sessão: {e}")
            return False
    
    def logout(self) -> bool:
        """
        Realiza logout da sessão WhatsApp
        
        Returns:
            bool: True se o logout foi realizado com sucesso
        """
        try:
            # Para o monitoramento
            self._stop_monitoring()
            
            logger.info(f"Realizando logout da sessão WhatsApp: {self.session_id}")
            response = self.connector.logout_session()
            
            self._notify_status_change(SessionStatus.DISCONNECTED)
            self.update_session_data("status", SessionStatus.DISCONNECTED)
            self.update_session_data("qr_code", None)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fazer logout: {e}")
            return False
    
    def check_status(self) -> str:
        """
        Verifica o status atual da sessão no WAHA
        
        Returns:
            str: Status atual da sessão
        """
        try:
            status_response = self.connector.check_session_status()
            current_status = status_response.get("status", "UNKNOWN")
            
            # Se o status mudou, notifica os listeners
            if current_status != self.status:
                self._notify_status_change(current_status)
                self.update_session_data("status", current_status)
            
            # Se desconectou e tem auto_reconnect, tenta reconectar
            if current_status == "DISCONNECTED" and self.auto_reconnect:
                logger.info("Sessão desconectada, tentando reconectar...")
                self.start()
            
            # Se está esperando QR, verifica se o QR expirou
            if current_status == "SCAN_QR_CODE" and self.qr_code:
                # Obtém um novo QR se necessário
                session_data = self.load_session_data() or {}
                qr_timestamp_str = session_data.get("qr_timestamp")
                
                if qr_timestamp_str:
                    qr_timestamp = datetime.fromisoformat(qr_timestamp_str)
                    # Se o QR tem mais de 2 minutos, atualiza
                    if (datetime.now() - qr_timestamp).total_seconds() > 120:
                        logger.info("QR code expirado, solicitando novo...")
                        self._get_and_store_qr_code()
            
            return current_status
            
        except Exception as e:
            logger.error(f"Erro ao verificar status: {e}")
            return SessionStatus.FAILED
    
    def _monitor_status(self) -> None:
        """
        Monitora periodicamente o status da sessão
        """
        while self.should_monitor:
            try:
                self.check_status()
                self.last_activity = datetime.now()
            except Exception as e:
                logger.error(f"Erro no monitoramento de sessão: {e}")
            
            time.sleep(20)  # Verifica a cada 20 segundos
    
    def _start_monitoring(self) -> None:
        """
        Inicia o monitoramento de status da sessão
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.should_monitor = True
        self.monitoring_thread = threading.Thread(target=self._monitor_status)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info(f"Monitoramento de sessão iniciado: {self.session_id}")
    
    def _stop_monitoring(self) -> None:
        """
        Para o monitoramento de status da sessão
        """
        self.should_monitor = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
            logger.info(f"Monitoramento de sessão finalizado: {self.session_id}")


# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de configuração
    waha_url = "http://localhost:3000"
    api_key = "zf_portal_waha_key"
    session_id = "zf_portal_session"
    
    # Inicialização do gerenciador de sessão
    session_manager = WhatsAppSessionManager(waha_url, api_key, session_id)
    
    # Adicionar um listener de status
    def status_changed(status):
        print(f"Status da sessão mudou para: {status}")
        if status == SessionStatus.SCAN_QR_CODE:
            qr = session_manager.get_qr_code()
            print(f"Escaneie o QR code: {qr}")
    
    session_manager.add_status_listener(status_changed)
    
    # Iniciar a sessão
    if session_manager.start():
        print("Sessão iniciada, aguarde a conexão...")
        
        # Aguarda por um minuto ou até conectar
        for _ in range(12):
            time.sleep(5)
            if session_manager.status == SessionStatus.CONNECTED:
                print("Sessão conectada com sucesso!")
                break
        
        # Demonstração: para a sessão depois de conectada
        if session_manager.status == SessionStatus.CONNECTED:
            print("Sessão será encerrada em 10 segundos...")
            time.sleep(10)
            session_manager.stop()
            print("Sessão encerrada.")
