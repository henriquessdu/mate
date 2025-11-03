import json
import re
from typing import Dict, List

class AgenteCalculador:
    
    def __init__(self, llm):
        # Modelo em modo JSON é ideal aqui
        self.llm = llm
    
    def calcular_resposta(self, enunciado: str, habilidade: Dict) -> Dict:
        # --- PROMPT ATUALIZADO ---
        prompt = f"""Resolva a questão de matemática apresentada abaixo.

ENUNCIADO: {enunciado}

Regras obrigatórias:
- Responda apenas com um objeto JSON válido (sem texto fora do JSON).
- Retorne os passos como uma LISTA de strings, cada uma iniciando com "Passo X:".
- Seja claro e sequencial; inclua os cálculos relevantes NOS PASSOS.
- Informe a "resposta_correta" com o valor exato e a unidade apropriada (ex.: "0,875 litro(s)" ou "7/8 litro(s)").
- Não adicione comentários fora do JSON.

Formato de saída esperado:
{{
  "resolucao_passos": [
    "Passo 1: ...",
    "Passo 2: ...",
    "Passo 3: ..."
  ],
  "resposta_correta": "..."
}}
"""
        # --- FIM DO PROMPT ATUALIZADO ---

        resposta = self.llm.invoke(prompt)
        texto_json = getattr(resposta, 'content', str(resposta))

        try:
            # limpar cercas de markdown, se houver
            t = texto_json.strip()
            if t.startswith("```json"):
                t = t[7:]
            if t.endswith("```"):
                t = t[:-3]

            dados = json.loads(t)

            # validações mínimas
            if "resolucao_passos" not in dados or "resposta_correta" not in dados:
                raise ValueError("JSON de saída não contém 'resolucao_passos' ou 'resposta_correta'.")

            if not isinstance(dados["resolucao_passos"], list) or not all(isinstance(x, str) for x in dados["resolucao_passos"]):
                raise ValueError("'resolucao_passos' deve ser uma lista de strings.")

            # saneamento: remove vazios e normaliza "Passo X:"
            passos = [p.strip() for p in dados["resolucao_passos"] if p and p.strip()]
            # (opcional) garante prefixo "Passo i:"
            passos_norm = []
            for i, p in enumerate(passos, 1):
                if not re.match(r'^\s*Passo\s*\d+\s*:', p, flags=re.I):
                    p = f"Passo {i}: {p}"
                passos_norm.append(p)
            
            # Garante que o retorno seja uma string limpa
            resposta_final = str(dados["resposta_correta"]).strip()

            # --- CHECK DE SEGURANÇA (OPCIONAL) ---
            # Se ainda assim o LLM incluir um "=", pegamos só a parte final
            if '=' in resposta_final:
                print("  ⚠️  Aviso (AgenteCalculador): LLM incluiu '='. Limpando a resposta.")
                partes = resposta_final.split('=')
                resposta_final = partes[-1].strip()
            # --- FIM DO CHECK ---

            return {
                "resolucao": "\n".join(passos_norm),
                "resposta_correta": resposta_final
            }

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ❌ Erro de JSON no Calculador: {e}")
            print(f"  Saída recebida: {texto_json[:200]}...")
            raise e