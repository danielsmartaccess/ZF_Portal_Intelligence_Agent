"""
Módulo para gerenciamento de templates de mensagens

Este módulo implementa o gerenciamento de templates de mensagens
para comunicação personalizada via WhatsApp em diferentes estágios
do funil de marketing.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("templates_manager")


class TemplatesManager:
    """
    Gerenciador de templates para mensagens
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Inicializa o gerenciador de templates
        
        Args:
            templates_dir: Diretório com os templates (opcional)
        """
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        # Garante que o diretório de templates existe
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # Configura o ambiente Jinja2
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Cache de templates
        self._template_cache: Dict[str, Template] = {}
        
        # Carrega templates predefinidos
        self._ensure_default_templates()
    
    def _ensure_default_templates(self) -> None:
        """
        Garante que os templates padrão estejam presentes
        """
        # Verifica templates para cada estágio do funil
        self._create_default_template(
            "atracao_inicial.txt",
            """Olá {{ nome|default('') }}!

Obrigado por seu interesse na ZF Portal. Somos especializados em {{ servicos|default('soluções digitais') }} e gostaríamos de entender melhor suas necessidades.

Posso ajudar com alguma informação específica sobre nossos serviços?

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "relacionamento_lead.txt",
            """Olá {{ nome|default('') }},

Espero que esteja tudo bem! Estamos acompanhando seu interesse em {{ servicos|default('nossos serviços') }} e gostaria de saber se podemos ajudar com mais informações ou esclarecer dúvidas.

{% if evento %}
Inclusive, teremos {{ evento }} em breve e seria uma ótima oportunidade para conversarmos mais sobre suas necessidades.
{% endif %}

Conte conosco!

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "oferta_conversao.txt",
            """Olá {{ nome|default('') }},

Com base no seu interesse em {{ servicos|default('nossos serviços') }}, preparamos uma proposta personalizada para atender às suas necessidades.

{% if desconto %}
*Oferta especial:* {{ desconto }} de desconto para contratação até {{ prazo|default('o final do mês') }}.
{% endif %}

Podemos agendar uma conversa rápida para apresentar os detalhes?

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "boas_vindas_cliente.txt",
            """Olá {{ nome|default('') }}!

Bem-vindo(a) à ZF Portal! Estamos muito felizes em tê-lo(a) como cliente.

Seu acesso já foi configurado e você pode começar a utilizar nossos serviços imediatamente.

Em caso de dúvidas, estou à disposição para ajudar.

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "followup_atracao.txt",
            """Olá {{ nome|default('') }},

Passando para saber se você teve a oportunidade de conhecer mais sobre a ZF Portal e nossos serviços de {{ servicos|default('soluções digitais') }}.

Estou à disposição para esclarecer qualquer dúvida.

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "followup_relacionamento.txt",
            """Olá {{ nome|default('') }},

Como vai? Após nossa última conversa sobre {{ assunto|default('nossos serviços') }}, gostaria de compartilhar algumas informações adicionais que podem ser úteis para você.

{% if conteudo %}
Preparamos um material sobre {{ conteudo }} que acredito ser de seu interesse.
{% endif %}

Podemos conversar mais sobre isso?

Atenciosamente,
Equipe ZF Portal"""
        )
        
        self._create_default_template(
            "mensagem_generica.txt",
            """Olá {{ nome|default('') }}!

Obrigado por entrar em contato com a ZF Portal.

{{ mensagem|default('Em que podemos ajudar hoje?') }}

Atenciosamente,
Equipe ZF Portal"""
        )
    
    def _create_default_template(self, filename: str, content: str) -> None:
        """
        Cria um template padrão se ele não existir
        
        Args:
            filename: Nome do arquivo de template
            content: Conteúdo do template
        """
        file_path = os.path.join(self.templates_dir, filename)
        
        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Template padrão criado: {filename}")
            except Exception as e:
                logger.error(f"Erro ao criar template padrão {filename}: {e}")
    
    def get_template_content(self, template_name: str) -> Optional[str]:
        """
        Obtém o conteúdo de um template
        
        Args:
            template_name: Nome do template (com ou sem extensão)
        
        Returns:
            str: Conteúdo do template ou None se não encontrado
        """
        # Garante que o template tem extensão
        if not template_name.endswith(('.txt', '.html', '.md')):
            template_name += '.txt'
        
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                logger.warning(f"Template não encontrado: {template_name}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao ler template {template_name}: {e}")
            return None
    
    def get_template(self, template_name: str, params: Dict[str, Any] = None) -> Optional[str]:
        """
        Obtém um template renderizado com os parâmetros
        
        Args:
            template_name: Nome do template (com ou sem extensão)
            params: Parâmetros para renderização
        
        Returns:
            str: Template renderizado ou None se falhar
        """
        params = params or {}
        
        # Garante que o template tem extensão
        if not template_name.endswith(('.txt', '.html', '.md')):
            template_name += '.txt'
        
        try:
            # Verifica se o template está no cache
            if template_name not in self._template_cache:
                # Carrega o template
                jinja_template = self.env.get_template(template_name)
                self._template_cache[template_name] = jinja_template
            else:
                jinja_template = self._template_cache[template_name]
            
            # Renderiza o template com os parâmetros
            return jinja_template.render(**params)
            
        except Exception as e:
            logger.error(f"Erro ao renderizar template {template_name}: {e}")
            
            # Em caso de falha, tenta retornar o conteúdo sem renderização
            return self.get_template_content(template_name)
    
    def save_template(self, template_name: str, content: str) -> bool:
        """
        Salva ou atualiza um template
        
        Args:
            template_name: Nome do template (com ou sem extensão)
            content: Conteúdo do template
        
        Returns:
            bool: True se o template foi salvo com sucesso
        """
        # Garante que o template tem extensão
        if not template_name.endswith(('.txt', '.html', '.md')):
            template_name += '.txt'
        
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Limpa o cache para este template
            if template_name in self._template_cache:
                del self._template_cache[template_name]
            
            logger.info(f"Template salvo: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar template {template_name}: {e}")
            return False
    
    def delete_template(self, template_name: str) -> bool:
        """
        Exclui um template
        
        Args:
            template_name: Nome do template (com ou sem extensão)
        
        Returns:
            bool: True se o template foi excluído com sucesso
        """
        # Garante que o template tem extensão
        if not template_name.endswith(('.txt', '.html', '.md')):
            template_name += '.txt'
        
        try:
            template_path = os.path.join(self.templates_dir, template_name)
            
            if os.path.exists(template_path):
                os.remove(template_path)
                
                # Limpa o cache para este template
                if template_name in self._template_cache:
                    del self._template_cache[template_name]
                
                logger.info(f"Template excluído: {template_name}")
                return True
            else:
                logger.warning(f"Template não encontrado para exclusão: {template_name}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao excluir template {template_name}: {e}")
            return False
    
    def list_templates(self) -> List[str]:
        """
        Lista todos os templates disponíveis
        
        Returns:
            List[str]: Lista de nomes de templates
        """
        try:
            templates = []
            
            for file in os.listdir(self.templates_dir):
                if file.endswith(('.txt', '.html', '.md')):
                    templates.append(file)
            
            return templates
            
        except Exception as e:
            logger.error(f"Erro ao listar templates: {e}")
            return []
    
    def validate_template(self, template_content: str, test_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Valida um template tentando renderizá-lo com parâmetros de teste
        
        Args:
            template_content: Conteúdo do template a validar
            test_params: Parâmetros de teste para renderização
        
        Returns:
            Dict: Resultado da validação com as chaves 'valid', 'error' e 'rendered'
        """
        test_params = test_params or {
            'nome': 'Usuário Teste',
            'servicos': 'Desenvolvimento Web',
            'evento': 'um webinar',
            'desconto': '10%',
            'prazo': 'sexta-feira',
            'assunto': 'soluções digitais',
            'conteudo': 'cases de sucesso',
            'mensagem': 'Aguardamos seu contato'
        }
        
        try:
            # Tenta criar e renderizar um template temporário
            temp_template = Template(template_content)
            rendered = temp_template.render(**test_params)
            
            return {
                'valid': True,
                'error': None,
                'rendered': rendered
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'rendered': None
            }


# Classe para gerenciar templates específicos para estágios do funil
class FunnelTemplatesManager:
    """
    Gerenciador de templates específicos para estágios do funil de marketing
    """
    
    def __init__(self, templates_manager: TemplatesManager):
        """
        Inicializa o gerenciador de templates para funil
        
        Args:
            templates_manager: Instância de TemplatesManager para acesso aos templates
        """
        self.templates_manager = templates_manager
        
        # Mapeamento de estágios do funil para templates
        self.funnel_templates = {
            "attraction": ["atracao_inicial.txt", "followup_atracao.txt"],
            "relationship": ["relacionamento_lead.txt", "followup_relacionamento.txt"],
            "conversion": ["oferta_conversao.txt"],
            "customer": ["boas_vindas_cliente.txt"]
        }
    
    def get_templates_for_stage(self, stage: str) -> List[str]:
        """
        Obtém lista de templates disponíveis para um estágio do funil
        
        Args:
            stage: Estágio do funil (attraction, relationship, conversion, customer)
        
        Returns:
            List[str]: Lista de nomes de templates para o estágio
        """
        return self.funnel_templates.get(stage.lower(), [])
    
    def get_template_for_stage(
        self, 
        stage: str, 
        template_index: int = 0, 
        params: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        Obtém um template específico para um estágio do funil
        
        Args:
            stage: Estágio do funil
            template_index: Índice do template a utilizar (padrão: 0 - primeiro template)
            params: Parâmetros para renderização
        
        Returns:
            str: Template renderizado ou None se não disponível
        """
        templates = self.get_templates_for_stage(stage)
        
        if not templates or template_index >= len(templates):
            return None
        
        template_name = templates[template_index]
        return self.templates_manager.get_template(template_name, params)


# Exemplo de uso
if __name__ == "__main__":
    # Inicialização do gerenciador de templates
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    manager = TemplatesManager(templates_dir)
    
    # Lista templates disponíveis
    available_templates = manager.list_templates()
    print(f"Templates disponíveis ({len(available_templates)}):")
    for template in available_templates:
        print(f"- {template}")
    
    # Exemplo de renderização
    params = {
        "nome": "João Silva",
        "servicos": "Automação de Marketing",
        "desconto": "15%"
    }
    
    rendered_template = manager.get_template("oferta_conversao", params)
    print("\nTemplate renderizado:")
    print(rendered_template)
    
    # Exemplo do gerenciador de templates para funil
    funnel_manager = FunnelTemplatesManager(manager)
    
    # Templates disponíveis para estágio de conversão
    conversion_templates = funnel_manager.get_templates_for_stage("conversion")
    print(f"\nTemplates para estágio de conversão: {conversion_templates}")
    
    # Renderiza template para estágio de atração
    attraction_template = funnel_manager.get_template_for_stage("attraction", 0, params)
    print("\nTemplate para estágio de atração:")
    print(attraction_template)
