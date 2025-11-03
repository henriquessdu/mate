import json
from typing import Dict, Optional
import random
import re

from langchain_community.llms import Ollama

OLLAMA_MODEL = "llama3.1:8b"

LLM = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.7,
    num_predict=3000
)

class BNCCDatabase:
    
    def __init__(self, json_path: str = "bncc_matematica.json"):
        with open(json_path, 'r', encoding='utf-8') as f:
            self.habilidades = json.load(f)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Dict]:
        codigo = codigo.upper().strip()
        return self.habilidades.get(codigo)
    
    def listar_todas(self):
        return self.habilidades


class AgenteContextualizador:
    
    def __init__(self, llm):
        self.llm = llm
    
    def criar_contexto(self, habilidade: Dict) -> str:
        prompt = f"""Crie APENAS o enunciado de uma questão de matemática.

HABILIDADE: {habilidade['descricao']}
ANO: {habilidade['ano']}

REQUISITOS:
- Situação cotidiana
- Valores numéricos simples
- Pergunta clara
- 2-3 linhas

Escreva APENAS o enunciado.
"""
        
        resposta = self.llm.invoke(prompt)
        if hasattr(resposta, 'content'):
            return resposta.content.strip()
        return str(resposta).strip()


class AgenteCalculador:
    
    def __init__(self, llm):
        self.llm = llm
    
    def calcular_resposta(self, enunciado: str, habilidade: Dict) -> Dict:
        prompt = f"""Resolva esta questão matematicamente.

ENUNCIADO: {enunciado}

FORMATO:

**RESOLUÇÃO:**
Passo 1: [cálculo]
Passo 2: [cálculo]

**RESPOSTA:** [valor exato com unidade se houver, ex: 0,875 litros OU 7/8 litros]

Seja preciso e inclua a unidade de medida na resposta.
"""
        
        resposta = self.llm.invoke(prompt)
        if hasattr(resposta, 'content'):
            texto = resposta.content
        else:
            texto = str(resposta)
        
        match = re.search(r'\*\*RESPOSTA[:\*]*\s*(.+?)(?:\n|$)', texto, re.IGNORECASE)
        resposta_correta = match.group(1).strip() if match else "0"
        
        return {
            "resolucao": texto,
            "resposta_correta": resposta_correta
        }


class AgenteDistratores:
    
    def __init__(self, llm):
        self.llm = llm
    
    def criar_alternativas(self, resposta_correta: str) -> Dict:

        texto_limpo = resposta_correta.lower().strip()
        
        match_decimal = re.search(r'(\d+[,.]?\d*)', texto_limpo)
        
        match_fracao = re.search(r'(\d+/\d+)', texto_limpo)
        
        unidade = ""
        if match_decimal:
            pos = texto_limpo.find(match_decimal.group(1))
            unidade = texto_limpo[pos + len(match_decimal.group(1)):].strip()
        
        if match_fracao:
            partes = match_fracao.group(1).split('/')
            valor_correto = float(partes[0]) / float(partes[1])
        elif match_decimal:
            valor_str = match_decimal.group(1).replace(',', '.')
            valor_correto = float(valor_str)
        else:
            valor_correto = 1.0
        
        variacoes = [
            valor_correto * 0.75,
            valor_correto * 1.25,
            valor_correto * 0.5
        ]
        
        todas_alternativas = [valor_correto] + variacoes
        
        alternativas_texto = []
        for v in todas_alternativas:
            if v >= 1 and v == int(v):
                alt = f"{int(v)}"
            elif v < 0.01:
                alt = f"{v:.4f}"
            else:
                alt = f"{v:.2f}".rstrip('0').rstrip('.')
            
            if unidade:
                alt = f"{alt} {unidade}"
            
            alternativas_texto.append(alt)
        
        alternativas_texto = list(dict.fromkeys(alternativas_texto))
        
        while len(alternativas_texto) < 4:
            novo_valor = valor_correto * random.uniform(0.6, 1.4)
            if novo_valor >= 1 and novo_valor == int(novo_valor):
                novo_texto = f"{int(novo_valor)}"
            else:
                novo_texto = f"{novo_valor:.2f}".rstrip('0').rstrip('.')
            
            if unidade:
                novo_texto = f"{novo_texto} {unidade}"
            
            if novo_texto not in alternativas_texto:
                alternativas_texto.append(novo_texto)
        
        alternativas_texto = alternativas_texto[:4]
        
        indices = list(range(4))
        random.shuffle(indices)
        
        letras = ['A', 'B', 'C', 'D']
        resultado = {}
        gabarito = None
        
        for i, idx in enumerate(indices):
            resultado[letras[i]] = alternativas_texto[idx]
            if idx == 0:  # Primeira é a correta
                gabarito = letras[i]
        
        resultado['gabarito'] = gabarito
        
        return resultado


class AgenteRevisor:
    
    def __init__(self, llm):
        self.llm = llm
    
    def revisar(self, questao_completa: Dict, habilidade: Dict) -> Dict:
        
        alt = questao_completa['alternativas']
        alternativas_valores = [alt['A'], alt['B'], alt['C'], alt['D']]
        
        if len(set(alternativas_valores)) < 4:
            return {
                "status": "REPROVADA",
                "detalhes": "ERRO: Alternativas duplicadas detectadas. Todas devem ser diferentes."
            }
        
        gabarito = alt.get('gabarito')
        if not gabarito or gabarito not in ['A', 'B', 'C', 'D']:
            return {
                "status": "REPROVADA",
                "detalhes": "ERRO: Gabarito inválido ou não definido."
            }
        
        prompt = f"""Você é um revisor matemático.

ENUNCIADO: {questao_completa['enunciado']}

RESOLUÇÃO: {questao_completa['resolucao']}

RESPOSTA INDICADA: {questao_completa['gabarito_texto']}

ALTERNATIVAS:
A) {alt['A']}
B) {alt['B']}
C) {alt['C']}
D) {alt['D']}

GABARITO: {gabarito})

TAREFA:
1. Refaça os cálculos
2. Compare sua resposta com a indicada
3. Verifique se o gabarito está correto

FORMATO:

**CÁLCULOS:** [refaça]
**SUA RESPOSTA:** [valor]
**COINCIDEM?** SIM ou NÃO
**STATUS:** APROVADA ou REPROVADA
**MOTIVO:** [se reprovada]
"""
        
        resposta = self.llm.invoke(prompt)
        if hasattr(resposta, 'content'):
            validacao = resposta.content
        else:
            validacao = str(resposta)
        
        aprovada = "APROVADA" in validacao.upper() and "REPROVADA" not in validacao.upper()
        status = "APROVADA" if aprovada else "REPROVADA"
        
        return {
            "status": status,
            "detalhes": validacao
        }


class SistemaGeradorQuestoes:
    
    def __init__(self):
        self.database = BNCCDatabase()
        self.contextualizador = AgenteContextualizador(LLM)
        self.calculador = AgenteCalculador(LLM)
        self.distratores = AgenteDistratores(LLM)
        self.revisor = AgenteRevisor(LLM)
        self.historico = []
    
    def processar_requisicao(self, codigo_bncc: str, max_tentativas: int = 3) -> Dict:
        
        habilidade = self.database.buscar_por_codigo(codigo_bncc)
        
        if not habilidade:
            return {
                "erro": f"Código {codigo_bncc} não encontrado",
                "codigos_disponiveis": list(self.database.listar_todas().keys())
            }
        
        for tentativa in range(1, max_tentativas + 1):
            print(f"\n🔄 Tentativa {tentativa}/{max_tentativas}")
            
            try:
                enunciado = self.contextualizador.criar_contexto(habilidade)
                print(f"  ✅ Enunciado criado")
                
                calculo = self.calculador.calcular_resposta(enunciado, habilidade)
                resposta_correta = calculo['resposta_correta']
                print(f"  ✅ Resposta: {resposta_correta}")
                
                alternativas = self.distratores.criar_alternativas(resposta_correta)
                print(f"  ✅ Alternativas: {alternativas['A']}, {alternativas['B']}, {alternativas['C']}, {alternativas['D']}")
                
                questao_completa = {
                    "enunciado": enunciado,
                    "alternativas": alternativas,
                    "gabarito_texto": resposta_correta,
                    "resolucao": calculo['resolucao']
                }
                
                validacao = self.revisor.revisar(questao_completa, habilidade)
                print(f"  {validacao['status']}")
                
                if validacao["status"] == "APROVADA":
                    print(f"\n✅ SUCESSO na tentativa {tentativa}!")
                    
                    resultado = {
                        "status": "sucesso",
                        "codigo_bncc": codigo_bncc,
                        "habilidade": habilidade,
                        "enunciado": enunciado,
                        "alternativas": alternativas,
                        "resolucao": calculo['resolucao'],
                        "tentativas": tentativa,
                        "validacao": validacao["detalhes"]
                    }
                    
                    self.historico.append(resultado)
                    return resultado
                else:
                    print(f"  Motivo: {validacao['detalhes'][:80]}...")
                
            except Exception as e:
                print(f"  ❌ Erro: {str(e)}")
                continue
        
        return {
            "status": "falha",
            "codigo_bncc": codigo_bncc,
            "mensagem": f"Não foi possível gerar questão aprovada em {max_tentativas} tentativas"
        }

sistema = SistemaGeradorQuestoes()