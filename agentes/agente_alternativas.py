"""
Agente Alternativas - Gera alternativas erradas (distratores) plausíveis.
"""

import re
import json
import random
from typing import Dict, List, Optional
import sys
from pathlib import Path

# Adiciona pasta pai ao path para importar utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import normalize_space, split_value_unit, same_value, perturb_value, clean_json_markdown


class AgenteAlternativas:
    """
    Gera alternativas de múltipla escolha com distratores plausíveis.
    
    Usa LLM para gerar distratores e fallback matemático se necessário.
    """
    
    def __init__(self, llm, seed: Optional[int] = None):
        """
        Inicializa o agente de alternativas.
        
        Args:
            llm: Modelo LLM configurado
            seed: Seed para reprodutibilidade do embaralhamento (opcional)
        """
        self.llm = llm
        self.seed = seed
        self.rng = random.Random()
        if self.seed is not None:
            self.rng.seed(self.seed)

    def criar_alternativas(self, enunciado: str, resposta_correta: str, habilidade: Dict) -> Dict:
        """
        Cria 4 alternativas (A, B, C, D) sendo 1 correta e 3 distratores.
        
        Args:
            enunciado: Texto da questão
            resposta_correta: Resposta correta calculada
            habilidade: Dict com informações BNCC
            
        Returns:
            Dict com chaves 'A', 'B', 'C', 'D' e 'gabarito'
        """
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

        # Tenta obter distratores do LLM
        linhas = []
        try:
            resp = self.llm.invoke(prompt)
            texto = getattr(resp, "content", str(resp))
            
            t = clean_json_markdown(texto)
            dados = json.loads(t)
            
            if isinstance(dados.get("distratores"), list):
                linhas = [str(d).strip(" -•\t") for d in dados["distratores"]]
            else:
                raise ValueError("Chave 'distratores' ausente ou não é uma lista.")

        except (json.JSONDecodeError, ValueError, AttributeError) as e:
            print(f"  ⚠️  Aviso (AgenteAlternativas): Falha ao parsear JSON do LLM. Acionando fallback. Erro: {e}")
            linhas = []

        # Filtra duplicatas e valores iguais à correta
        vistas = set()
        alts = []
        for l in linhas:
            if same_value(l, resposta_correta):
                continue
            key = normalize_space(l)
            if key and key not in vistas:
                vistas.add(key)
                alts.append(l)
            if len(alts) == 3:
                break

        # Completa com fallback se necessário
        if len(alts) < 3:
            print(f"  ⚙️  Fallback (AgenteAlternativas): Gerando {3 - len(alts)} alternativa(s) por perturbação.")
            val, uni = split_value_unit(resposta_correta)
            
            deltas = [0.10, -0.10, 0.25, -0.25, 0.05, -0.05, 0.50, -0.50]
            
            # Se for fração, adiciona deltas baseados no denominador
            if '/' in val:
                try:
                    n_str, d_str = val.split('/')
                    d = float(d_str)
                    if d != 0:
                        deltas.extend([1.0/d, -1.0/d])
                except:
                    pass
            
            for delta in deltas:
                if len(alts) == 3:
                    break
                sug = perturb_value(val, uni, delta)
                if not same_value(sug, resposta_correta) and normalize_space(sug) not in vistas:
                    vistas.add(normalize_space(sug))
                    alts.append(sug)

        # Preenche com placeholders se ainda faltar
        while len(alts) < 3:
            val, uni = split_value_unit(resposta_correta)
            placeholder = perturb_value(val, uni, (len(alts) + 1) * 0.33)
            if not same_value(placeholder, resposta_correta) and normalize_space(placeholder) not in vistas:
                vistas.add(normalize_space(placeholder))
                alts.append(placeholder)
            else:
                alts.append(f"Valor {len(alts)+1}")

        # Monta A-D embaralhado
        todas = [resposta_correta] + alts[:3]
        self.rng.shuffle(todas)

        letras = ['A', 'B', 'C', 'D']
        resultado = {letras[i]: todas[i] for i in range(4)}
        
        # Define gabarito
        for i, v in enumerate(todas):
            if same_value(v, resposta_correta):
                resultado["gabarito"] = letras[i]
                break
                
        return resultado
