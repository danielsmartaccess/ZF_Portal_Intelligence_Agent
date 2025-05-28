import logging

print('Running debugging...')
from src.chatbot.chatbot_service import ChatbotService

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Inicializar chatbot
chatbot = ChatbotService()
print(f'Sessão configurada: {chatbot.session_name}')
