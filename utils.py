"""
Funções utilitárias compartilhadas entre os agentes.
"""

import re
from typing import Tuple, Optional


def normalize_space(s: str) -> str:
    """Normaliza espaços em branco e converte para lowercase."""
    return re.sub(r'\s+', ' ', s or '').strip().lower()


def split_value_unit(texto: str) -> Tuple[str, str]:
    """
    Extrai valor numérico e unidade de um texto.
    
    Exemplos:
        "12,5 litros" -> ("12,5", "litros")
        "7/8 metro" -> ("7/8", "metro")
    """
    t = (texto or "").strip()
    m = re.search(r'([-+]?\d+(?:[.,]\d+)?|\d+\/\d+)', t)
    if not m:
        return t, ""
    num = m.group(1)
    unidade = (t[m.end():]).strip(" .")
    return num, unidade


def to_float(x: str) -> Optional[float]:
    """
    Converte string (decimal ou fração) para float.
    
    Exemplos:
        "12,5" -> 12.5
        "7/8" -> 0.875
        "abc" -> None
    """
    x = (x or "").strip()
    
    # Trata fração
    if re.fullmatch(r'\d+\/\d+', x):
        n, d = x.split('/')
        try:
            return float(n) / float(d)
        except:
            return None
    
    # Trata decimal
    x = x.replace(',', '.')
    try:
        return float(x)
    except:
        return None


def same_value(a: str, b: str) -> bool:
    """
    Verifica se dois valores são equivalentes.
    
    Considera:
    - Equivalência numérica (0,875 == 0.875 == 7/8)
    - Unidades ignorando plural (litro == litros)
    - Equivalência textual se não houver número
    
    Exemplos:
        same_value("0,875 litros", "7/8 litro") -> True
        same_value("12 metros", "12 metro") -> True
    """
    a_val, a_unit = split_value_unit(a)
    b_val, b_unit = split_value_unit(b)
    
    fa, fb = to_float(a_val), to_float(b_val)
    same_num = (fa is not None and fb is not None and abs(fa - fb) < 1e-9)
    same_text = normalize_space(a) == normalize_space(b)
    
    au = normalize_space(a_unit).rstrip('s')
    bu = normalize_space(b_unit).rstrip('s')
    same_unit = (au == bu) or (au == "" and bu == "")
    
    return (same_num and same_unit) or same_text


def perturb_value(valor: str, unidade: str, delta: float) -> str:
    """
    Gera um valor próximo ao original (usado para criar distratores).
    
    Args:
        valor: Valor numérico ou fração
        unidade: Unidade (ex: "metros", "litros")
        delta: Percentual de variação (ex: 0.10 = +10%)
    
    Retorna:
        Novo valor perturbado com unidade
    """
    if re.fullmatch(r'\d+\/\d+', valor):
        n, d = valor.split('/')
        try:
            base = float(n) / float(d)
            var = base * (1 + delta)
        except:
            return f"{valor} {unidade}".strip()
        texto = f"{var:.3f}".rstrip('0').rstrip('.')
        texto = texto.replace('.', ',')
        return f"{texto} {unidade}".strip()
    
    try:
        estilo_virgula = (',' in valor and '.' not in valor)
        base = float(valor.replace(',', '.'))
        var = base * (1 + delta)
        texto = f"{var:.3f}".rstrip('0').rstrip('.')
        if estilo_virgula:
            texto = texto.replace('.', ',')
        return f"{texto} {unidade}".strip()
    except:
        return f"{valor} {unidade}".strip()


def clean_json_markdown(texto: str) -> str:
    """Remove marcadores markdown de blocos JSON (```json ou ```)."""
    t = texto.strip()
    if t.startswith("```json"):
        t = t[7:]
    elif t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()
