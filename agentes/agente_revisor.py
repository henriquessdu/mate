"""
Agente Revisor - Valida questões completas antes de aprovar.
"""

import json
import re
from typing import Dict, Optional
import sys
from pathlib import Path

# Adiciona pasta pai ao path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import normalize_space, split_value_unit, to_float, same_value, clean_json_markdown


class AgenteRevisor:
    """
    Valida questões completas verificando cálculos, alternativas e coerência.
    
    Realiza verificações determinísticas e usa LLM para revisar cálculos.
    """
    
    def __init__(self, llm, strict_json: bool = True):
        """
        Inicializa o agente revisor.
        
        Args:
            llm: Modelo LLM configurado (preferencialmente JSON mode)
            strict_json: Se True, exige JSON válido do LLM
        """
        self.llm = llm
        self.strict_json = strict_json

    def _precheck(self, questao: Dict) -> Optional[Dict]:
        """
        Realiza validações determinísticas antes de consultar o LLM.
        
        Args:
            questao: Dicionário com questão completa
            
        Returns:
            Dict com erro se houver problema, None se passou nas validações
        """
        alt = questao['alternativas']
        enunciado = questao['enunciado']
        resolucao = questao['resolucao']
        gabarito_texto = questao['gabarito_texto']

        # 1) Verifica duplicatas
        alternativas_valores = [alt['A'], alt['B'], alt['C'], alt['D']]
        if len(set(alternativas_valores)) < 4:
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Alternativas duplicadas detectadas. Todas devem ser diferentes."}

        # 2) Gabarito presente e válido
        gabarito = alt.get('gabarito')
        if gabarito not in ['A', 'B', 'C', 'D']:
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Gabarito inválido ou não definido."}

        # 3) Gabarito confere com texto
        valor_gabarito = alt[gabarito]
        if not same_value(valor_gabarito, gabarito_texto):
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Valor do gabarito ({valor_gabarito}) não confere com gabarito_texto ({gabarito_texto})."}

        # 4) Unidade consistente
        _, u1 = split_value_unit(valor_gabarito)
        _, u2 = split_value_unit(gabarito_texto)
        if u1 and u2 and normalize_space(u1).rstrip('s') != normalize_space(u2).rstrip('s'):
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Unidade inconsistente entre gabarito ({u1}) e gabarito_texto ({u2})."}

        # 5) Resolução não vazia
        if not normalize_space(resolucao):
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Resolução vazia ou ausente."}

        return None

    def _build_prompt(self, questao: Dict, habilidade: Dict) -> str:
        """
        Constrói prompt para o LLM revisar a questão.
        
        Args:
            questao: Dicionário com questão completa
            habilidade: Dict com informações BNCC
            
        Returns:
            String com prompt formatado
        """
        alt = questao['alternativas']
        return f"""Você é um revisor matemático.

ENUNCIADO: {questao['enunciado']}

RESOLUÇÃO (do gerador): {questao['resolucao']}

RESPOSTA INDICADA (texto): {questao['gabarito_texto']}

ALTERNATIVAS:
A) {alt['A']}
B) {alt['B']}
C) {alt['C']}
D) {alt['D']}

GABARITO: {alt.get('gabarito')}

TAREFA:
1. Refaça os cálculos de forma independente.
2. Diga qual alternativa corresponde ao resultado correto.
3. Compare sua resposta com a indicada e conclua STATUS.

SAÍDA (JSON válido, sem texto fora do JSON):
{{
  "calculos": "Passo 1...\\nPasso 2...",
  "resposta_revisor": "[valor com unidade, se aplicável]",
  "gabarito_correspondente": "A|B|C|D|nenhuma",
  "coincidem": true/false,
  "status": "APROVADA|REPROVADA",
  "motivo": "[se REPROVADA, explique em 1-2 frases]"
}}
""".strip()

    def _parse_llm_json(self, raw: str) -> Optional[Dict]:
        """
        Parseia JSON retornado pelo LLM.
        
        Args:
            raw: String com resposta do LLM
            
        Returns:
            Dict parseado ou None se falhar
        """
        t = clean_json_markdown(raw)
        try:
            data = json.loads(t)
            return data
        except Exception:
            return None

    def revisar(self, questao_completa: Dict, habilidade: Dict) -> Dict:
        """
        Revisa uma questão completa.
        
        Args:
            questao_completa: Dict com enunciado, alternativas, resolução, gabarito
            habilidade: Dict com informações BNCC
            
        Returns:
            Dict com 'status' ("APROVADA" ou "REPROVADA") e 'detalhes'
        """
        # Pré-checagens determinísticas
        fail = self._precheck(questao_completa)
        if fail:
            return fail

        # Prompt ao LLM
        prompt = self._build_prompt(questao_completa, habilidade)
        resp = self.llm.invoke(prompt)
        texto = getattr(resp, "content", str(resp)).strip()

        data = self._parse_llm_json(texto)
        if not data:
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Revisor não retornou JSON válido. Saída: {texto[:200]}..."}

        # Normaliza status
        status = (data.get("status") or "").upper()
        if status not in {"APROVADA", "REPROVADA"}:
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Campo 'status' inválido na saída do revisor: {data}"}

        # Checagem final: coerência entre resposta_revisor e alternativa indicada
        alt = questao_completa['alternativas']
        gab_rev = (data.get("gabarito_correspondente") or "").upper()
        if gab_rev in ['A', 'B', 'C', 'D']:
            if not same_value(data.get("resposta_revisor", ""), alt[gab_rev]):
                data.setdefault("motivo", "")
                data["motivo"] = ("Inconsistência: 'resposta_revisor' diferente do valor da alternativa "
                                  f"{gab_rev} ({alt[gab_rev]}). " + data["motivo"]).strip()

        return {
            "status": status,
            "detalhes": json.dumps(data, ensure_ascii=False, indent=2)
        }
