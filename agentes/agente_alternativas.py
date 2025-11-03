import re
import json  # Importado
import random
from typing import Dict, List, Optional, Tuple

class AgenteAlternativas:
    def __init__(self, llm, seed: Optional[int] = None):
        self.llm = llm
        self.seed = seed
        # Cria uma instância de Random isolada para não afetar o estado global
        self.rng = random.Random()
        if self.seed is not None:
            self.rng.seed(self.seed)

    # --- utils bem leves ---
    # (Idealmente, movidos para um utils.py, mas mantidos aqui pela completude)
    @staticmethod
    def _normalize(s: str) -> str:
        return re.sub(r'\s+', ' ', (s or '').strip()).lower()

    @staticmethod
    def _split_value_unit(texto: str) -> Tuple[str, str]:
        t = (texto or '').strip()
        m = re.search(r'([-+]?\d+(?:[.,]\d+)?|\d+\/\d+)', t)
        if not m:
            return t, ""
        num = m.group(1)
        uni = (t[m.end():]).strip(" .")
        return num, uni

    @staticmethod
    def _same_value(a: str, b: str) -> bool:
        # comparação simples por texto normalizado
        return AgenteAlternativas._normalize(a) == AgenteAlternativas._normalize(b)

    @staticmethod
    def _perturb(valor: str, unidade: str, delta: float) -> str:
        # gera um número próximo preservando estilo básico
        if re.fullmatch(r'\d+\/\d+', valor):
            # se vier fração, converte para float e aplica delta (retorna decimal simples)
            n, d = valor.split('/')
            try:
                base = float(n) / float(d)
                var = base * (1 + delta)
            except:
                return f"{valor} {unidade}".strip()
            texto = f"{var:.3f}".rstrip('0').rstrip('.')
            texto = texto.replace('.', ',')  # favorece pt-br
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
            # não deu pra perturbar, devolve igual (será filtrado)
            return f"{valor} {unidade}".strip()

    def criar_alternativas(self, enunciado: str, resposta_correta: str, habilidade: Dict) -> Dict:

        # --- PROMPT ATUALIZADO ---
        # Pede explicitamente um JSON com a chave "distratores"
        prompt = f"""
Você é um gerador de alternativas de múltipla escolha.

ENUNCIADO: {enunciado}
RESPOSTA CORRETA: {resposta_correta}

TAREFA:
Crie 3 alternativas ERRADAS (distratores) porém PLAUSÍVEIS.

REGRAS OBRIGATÓRIAS:
- Retorne APENAS um objeto JSON válido.
- O JSON deve conter a chave "distratores", que é uma lista de 3 strings.
- Mantenha o mesmo padrão/unidade da RESPOSTA CORRETA.
- Gere valores próximos, mas diferentes da correta.
- Não repita a resposta correta.
- Não inclua explicações ou texto fora do JSON.

EXEMPLO DE SAÍDA (apenas JSON):
{{
  "distratores": [
    "12,5 litros",
    "11 litros",
    "14 litros"
  ]
}}
""".strip()

        # --- LÓGICA DE PARSING ATUALIZADA ---
        linhas = []
        try:
            resp = self.llm.invoke(prompt)
            texto = getattr(resp, "content", str(resp))
            
            # Limpeza básica de markdown (caso o LLM ignore o 'format=json')
            t = texto.strip()
            if t.startswith("```json"):
                t = t[7:]
            if t.endswith("```"):
                t = t[:-3]
            
            dados = json.loads(t)
            
            if isinstance(dados.get("distratores"), list):
                # Limpa os valores recebidos
                linhas = [str(d).strip(" -•\t") for d in dados["distratores"]]
            else:
                raise ValueError("Chave 'distratores' ausente ou não é uma lista.")

        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            # Se o LLM falhar (JSON inválido, etc.), 'linhas' continuará vazia
            # e o código de fallback será acionado.
            print(f"  ⚠️  Aviso (AgenteAlternativas): Falha ao parsear JSON do LLM. Acionando fallback. Erro: {e}")
            linhas = [] # Garante que está vazia para o fallback

        # --- LÓGICA DE FILTRAGEM E FALLBACK (SE MANTÉM) ---

        # remove duplicatas, remove iguais à correta
        vistas = set()
        alts = []
        for l in linhas:
            if self._same_value(l, resposta_correta):
                continue
            key = self._normalize(l)
            if key and key not in vistas:
                vistas.add(key)
                alts.append(l)
            if len(alts) == 3:
                break

        # completa com backups, se necessário
        if len(alts) < 3:
            print(f"  ⚙️  Fallback (AgenteAlternativas): Gerando {3 - len(alts)} alternativa(s) por perturbação.")
            val, uni = self._split_value_unit(resposta_correta)
            
            # Lista de deltas para perturbação
            deltas = [0.10, -0.10, 0.25, -0.25, 0.05, -0.05, 0.50, -0.50]
            if '/' in val:
                try:
                    n_str, d_str = val.split('/')
                    d = float(d_str)
                    if d != 0:
                        deltas.extend([1.0/d, -1.0/d]) # Adiciona deltas baseados no denominador
                except:
                    pass # ignora se a fração for inválida
            
            for delta in deltas:
                if len(alts) == 3:
                    break
                sug = self._perturb(val, uni, delta)
                if not self._same_value(sug, resposta_correta) and self._normalize(sug) not in vistas:
                    vistas.add(self._normalize(sug))
                    alts.append(sug)

        # se ainda faltar (caso extremo), preenche com placeholders
        while len(alts) < 3:
            val, uni = self._split_value_unit(resposta_correta)
            # Gera um placeholder que tem menos chance de colidir
            placeholder = self._perturb(val, uni, (len(alts) + 1) * 0.33) 
            if not self._same_value(placeholder, resposta_correta) and self._normalize(placeholder) not in vistas:
                 vistas.add(self._normalize(placeholder))
                 alts.append(placeholder)
            else:
                # Fallback final se o _perturb falhar
                alts.append(f"Valor {len(alts)+1}")


        # monta A-D embaralhado
        todas = [resposta_correta] + alts[:3]
        
        # --- SHUFFLE ATUALIZADO ---
        self.rng.shuffle(todas)

        letras = ['A', 'B', 'C', 'D']
        resultado = {letras[i]: todas[i] for i in range(4)}
        
        # gabarito
        for i, v in enumerate(todas):
            if self._same_value(v, resposta_correta):
                resultado["gabarito"] = letras[i]
                break
                
        return resultado