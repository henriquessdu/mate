"""
Módulo de agentes especializados para geração de questões BNCC.

Cada agente tem uma responsabilidade específica:
- AgenteContextualizador: Cria enunciados contextualizados
- AgenteCalculador: Resolve questões e gera resolução
- AgenteAlternativas: Gera distratores plausíveis
- AgenteRevisor: Valida questões completas
"""

from .agente_contextualizador import AgenteContextualizador
from .agente_calculador import AgenteCalculador
from .agente_alternativas import AgenteAlternativas
from .agente_revisor import AgenteRevisor

__all__ = [
    'AgenteContextualizador',
    'AgenteCalculador',
    'AgenteAlternativas',
    'AgenteRevisor'
]

__version__ = '3.0.0'
