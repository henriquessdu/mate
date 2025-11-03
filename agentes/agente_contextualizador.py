"""
Agente Contextualizador - Cria enunciados contextualizados para questões.
"""

from typing import Dict


class AgenteContextualizador:
    """
    Cria enunciados contextualizados alinhados às habilidades BNCC.
    
    Gera textos de questões adequados ao ano escolar e contexto cotidiano.
    """
    
    def __init__(self, llm):
        """
        Inicializa o agente contextualizador.
        
        Args:
            llm: Modelo LLM para geração de texto
        """
        self.llm = llm
    
    def criar_contexto(self, habilidade: Dict) -> str:
        """
        Cria o enunciado de uma questão matemática.
        
        Args:
            habilidade: Dict com 'descricao', 'ano' e 'codigo' da BNCC
            
        Returns:
            String com o enunciado da questão
        """
        prompt = f"""Crie apenas o ENUNCIADO de uma questão de matemática alinhada à habilidade abaixo.

HABILIDADE (BNCC): {habilidade['descricao']}
ANO ESCOLAR: {habilidade['ano']}

REQUISITOS:
- Escreva em português brasileiro.
- Contexto cotidiano, simples e plausível.
- Use números pequenos (até 3 dígitos).
- Linguagem clara e objetiva, adequada ao ano informado.
- O enunciado deve ter entre 2 e 3 linhas.
- Não inclua alternativas, resolução ou resposta.
- O problema deve ser possível de resolver com base apenas na informação dada.

Saída esperada: apenas o texto do enunciado.
"""
        
        resposta = self.llm.invoke(prompt)
        if hasattr(resposta, 'content'):
            return resposta.content.strip()
        return str(resposta).strip()
