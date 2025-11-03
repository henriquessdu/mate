"""
Sistema Gerador de Questões - Orquestra os agentes para gerar questões BNCC.
"""

import json
from typing import Dict, Optional
from langchain_community.llms import Ollama

from agentes.agente_contextualizador import AgenteContextualizador
from agentes.agente_calculador import AgenteCalculador
from agentes.agente_alternativas import AgenteAlternativas
from agentes.agente_revisor import AgenteRevisor


# Configuração dos modelos
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
    """
    Gerencia o banco de dados de habilidades BNCC.
    """
    
    def __init__(self, json_path: str = "bncc_matematica.json"):
        """
        Inicializa o banco de dados.
        
        Args:
            json_path: Caminho para arquivo JSON com habilidades
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            self.habilidades = json.load(f)
    
    def buscar_por_codigo(self, codigo: str) -> Optional[Dict]:
        """
        Busca habilidade por código.
        
        Args:
            codigo: Código BNCC (ex: "EF06MA09")
            
        Returns:
            Dict com dados da habilidade ou None se não encontrar
        """
        codigo = codigo.upper().strip()
        return self.habilidades.get(codigo)
    
    def listar_todas(self):
        """
        Retorna todas as habilidades disponíveis.
        
        Returns:
            Dict com todas as habilidades
        """
        return self.habilidades


class SistemaGeradorQuestoes:
    """
    Sistema principal que coordena os agentes para gerar questões.
    """
    
    def __init__(self):
        """
        Inicializa o sistema e todos os agentes.
        """
        self.database = BNCCDatabase()
        
        self.contextualizador = AgenteContextualizador(LLM_TEXT)
        self.calculador = AgenteCalculador(LLM_JSON)
        self.agente_alternativas = AgenteAlternativas(LLM_JSON)
        self.revisor = AgenteRevisor(LLM_JSON)
        
        self.historico = []
    
    def processar_requisicao(self, codigo_bncc: str, max_tentativas: int = 3) -> Dict:
        """
        Processa requisição de geração de questão.
        
        Args:
            codigo_bncc: Código da habilidade BNCC
            max_tentativas: Número máximo de tentativas antes de desistir
            
        Returns:
            Dict com questão gerada ou mensagem de erro
        """
        habilidade = self.database.buscar_por_codigo(codigo_bncc)
        
        if not habilidade:
            return {
                "erro": f"Código {codigo_bncc} não encontrado",
                "codigos_disponiveis": list(self.database.listar_todas().keys())
            }
        
        for tentativa in range(1, max_tentativas + 1):
            print(f"\n🔄 Tentativa {tentativa}/{max_tentativas}")
            
            try:
                # Passo 1: Criar enunciado
                enunciado = self.contextualizador.criar_contexto(habilidade)
                print(f"  ✅ Enunciado criado")
                
                # Passo 2: Calcular resposta
                calculo = self.calculador.calcular_resposta(enunciado, habilidade)
                resposta_correta = calculo['resposta_correta']
                print(f"  ✅ Resposta calculada: {resposta_correta}")
                
                # Passo 3: Gerar alternativas
                alternativas = self.agente_alternativas.criar_alternativas(
                    enunciado=enunciado,
                    resposta_correta=resposta_correta,
                    habilidade=habilidade
                )
                print(f"  ✅ Alternativas geradas: A={alternativas['A']}, B={alternativas['B']}, "
                      f"C={alternativas['C']}, D={alternativas['D']}")
                
                # Passo 4: Montar questão completa
                questao_completa = {
                    "enunciado": enunciado,
                    "alternativas": alternativas,
                    "gabarito_texto": resposta_correta,
                    "resolucao": calculo['resolucao']
                }
                
                # Passo 5: Revisar
                validacao = self.revisor.revisar(questao_completa, habilidade)
                
                if validacao["status"] == "APROVADA":
                    print(f"  ✅ APROVADA")
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
                    print(f"  ❌ REPROVADA")
                    motivo = validacao['detalhes'][:80] if len(validacao['detalhes']) > 80 else validacao['detalhes']
                    print(f"     Motivo: {motivo}...")
            
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


# Instância global do sistema
sistema = SistemaGeradorQuestoes()
