import json
import re
from typing import Dict, Optional, Tuple

class AgenteRevisor:
    def __init__(self, llm, strict_json: bool = True):
        self.llm = llm
        self.strict_json = strict_json

    # ---------- utils de comparação ----------
    @staticmethod
    def _normalize_space(s: str) -> str:
        return re.sub(r'\s+', ' ', s or '').strip()

    @staticmethod
    def _split_value_unit(texto: str) -> Tuple[str, str]:
        """Extrai a parte numérica (ou fração) e a unidade textual."""
        t = (texto or "").strip()
        m = re.search(r'([-+]?\d+(?:[.,]\d+)?|\d+\/\d+)', t)
        if not m:
            return t, ""  # sem número claro
        num = m.group(1)
        unidade = (t[m.end():]).strip(" .")
        return num, unidade

    @staticmethod
    def _to_float(x: str) -> Optional[float]:
        x = (x or "").strip()
        if re.fullmatch(r'\d+\/\d+', x):
            n, d = x.split('/')
            try:
                return float(n) / float(d)
            except:
                return None
        x = x.replace(',', '.')
        try:
            return float(x)
        except:
            return None

    @classmethod
    def _same_value(cls, a: str, b: str) -> bool:
        """Equivalência numérica (0,875 == 0.875 == 7/8) OU texto igual normalizado."""
        a_val, a_unit = cls._split_value_unit(a)
        b_val, b_unit = cls._split_value_unit(b)
        fa, fb = cls._to_float(a_val), cls._to_float(b_val)
        same_num = (fa is not None and fb is not None and abs(fa - fb) < 1e-9)
        same_text = cls._normalize_space(a).lower() == cls._normalize_space(b).lower()
        # unidade: ignore plural simples
        au = cls._normalize_space(a_unit).lower().rstrip('s')
        bu = cls._normalize_space(b_unit).lower().rstrip('s')
        same_unit = (au == bu) or (au == "" and bu == "")
        return (same_num and same_unit) or same_text

    # ---------- validações determinísticas ----------
    def _precheck(self, questao: Dict) -> Optional[Dict]:
        alt = questao['alternativas']
        enunciado = questao['enunciado']
        resolucao = questao['resolucao']
        gabarito_texto = questao['gabarito_texto']

        # 1) duplicatas (já existe na sua versão, deixo aqui por completude)
        alternativas_valores = [alt['A'], alt['B'], alt['C'], alt['D']]
        if len(set(alternativas_valores)) < 4:
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Alternativas duplicadas detectadas. Todas devem ser diferentes."}

        # 2) gabarito presente e válido
        gabarito = alt.get('gabarito')
        if gabarito not in ['A', 'B', 'C', 'D']:
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Gabarito inválido ou não definido."}

        # 3) gabarito confere com texto do gabarito_texto
        valor_gabarito = alt[gabarito]
        if not self._same_value(valor_gabarito, gabarito_texto):
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Valor do gabarito ({valor_gabarito}) não confere com gabarito_texto ({gabarito_texto})."}

        # 4) unidade consistente entre correta e gabarito_texto (quando há unidade)
        _, u1 = self._split_value_unit(valor_gabarito)
        _, u2 = self._split_value_unit(gabarito_texto)
        if u1 and u2 and self._normalize_space(u1).lower().rstrip('s') != self._normalize_space(u2).lower().rstrip('s'):
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Unidade inconsistente entre gabarito ({u1}) e gabarito_texto ({u2})."}

        # 5) resolução não vazia
        if not self._normalize_space(resolucao):
            return {"status": "REPROVADA",
                    "detalhes": "ERRO: Resolução vazia ou ausente."}

        # Se passou pelos pré-checks, siga para o LLM
        return None

    # ---------- prompt & parsing ----------
    def _build_prompt(self, questao: Dict, habilidade: Dict) -> str:
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
        t = raw.strip()
        t = re.sub(r'^```(?:json)?\s*', '', t)
        t = re.sub(r'\s*```$', '', t)
        try:
            data = json.loads(t)
            return data
        except Exception:
            return None

    # ---------- público ----------
    def revisar(self, questao_completa: Dict, habilidade: Dict) -> Dict:
        # Pré-checagens determinísticas
        fail = self._precheck(questao_completa)
        if fail:
            return fail

        # Prompt ao LLM (idealmente com model format="json" e temperature baixa)
        prompt = self._build_prompt(questao_completa, habilidade)
        resp = self.llm.invoke(prompt)
        texto = getattr(resp, "content", str(resp)).strip()

        data = self._parse_llm_json(texto)
        if not data:
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Revisor não retornou JSON válido. Saída: {texto[:200]}..."}

        # Normalizações
        status = (data.get("status") or "").upper()
        if status not in {"APROVADA", "REPROVADA"}:
            return {"status": "REPROVADA",
                    "detalhes": f"ERRO: Campo 'status' inválido na saída do revisor: {data}"}

        # Checagem final: se o revisor indicou uma alternativa, verifique coerência com o valor
        alt = questao_completa['alternativas']
        gab_rev = (data.get("gabarito_correspondente") or "").upper()
        if gab_rev in ['A', 'B', 'C', 'D']:
            # coerência: resposta_revisor ~ alternativas[gab_rev]
            if not self._same_value(data.get("resposta_revisor", ""), alt[gab_rev]):
                # não reprova automaticamente, mas registra motivo
                data.setdefault("motivo", "")
                data["motivo"] = ("Inconsistência: 'resposta_revisor' diferente do valor da alternativa "
                                  f"{gab_rev} ({alt[gab_rev]}). " + data["motivo"]).strip()

        # Conclusão
        return {
            "status": status,
            "detalhes": json.dumps(data, ensure_ascii=False, indent=2)
        }
