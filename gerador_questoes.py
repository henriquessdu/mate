import json
from typing import Dict, Optional

from langchain_community.llms import Ollama

# <<< 1. IMPORTA OS AGENTES DA NOVA PASTA
from agentes import (
    AgenteContextualizador, 
    AgenteCalculador, 
    AgenteAlternativas, 
    AgenteRevisor
)

OLLAMA_MODEL = "llama3.1:8b"

LLM_TEXT = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.7,
    num_predict=3000
)

LLM_JSON = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.1,
    format="json",
    num_predict=2000
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

class SistemaGeradorQuestoes:
    
    def __init__(self):
        self.database = BNCCDatabase()
        
        self.contextualizador = AgenteContextualizador(LLM_TEXT)
        self.calculador = AgenteCalculador(LLM_JSON)
        self.agente_alternativas = AgenteAlternativas(LLM_JSON) # Passa o LLM, embora não o use
        self.revisor = AgenteRevisor(LLM_JSON)
        
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
                
                alternativas = self.agente_alternativas.criar_alternativas(enunciado=enunciado, resposta_correta=resposta_correta, habilidade=habilidade
)
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
            
            except (json.JSONDecodeError, ValueError) as e:
                print(f"  ❌ Erro de processamento (JSON/Valor): {str(e)}")
                continue
            except Exception as e:
                print(f"  ❌ Erro inesperado: {str(e)}")
                continue
        
        return {
            "status": "falha",
            "codigo_bncc": codigo_bncc,
            "mensagem": f"Não foi possível gerar questão aprovada em {max_tentativas} tentativas"
        }

sistema = SistemaGeradorQuestoes()