# 🧮 Sistema Gerador de Questões de Matemática

Sistema baseado em agentes LLM para gerar questões de múltipla escolha alinhadas à BNCC (Base Nacional Comum Curricular).

## 📋 Descrição

O sistema utiliza 4 agentes especializados que trabalham em conjunto:

1. **AgenteContextualizador** - Cria enunciados contextualizados e adequados ao ano escolar
2. **AgenteCalculador** - Resolve a questão matematicamente e gera resolução passo a passo
3. **AgenteAlternativas** - Gera alternativas erradas (distratores) plausíveis
4. **AgenteRevisor** - Valida toda a questão antes de aprovar

## 🚀 Como Rodar

### Pré-requisitos
- Python 3.8+
- Ollama instalado com modelo llama3.1:8b

### Instalação

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
python mate.py
```

Acesse: **http://localhost:5000**

## 📚 Habilidades BNCC Suportadas

| Código | Descrição | Ano |
|--------|-----------|-----|
| EF06MA07 | Frações equivalentes | 6º ano |
| EF06MA08 | Números racionais (fração/decimal) | 6º ano |
| EF06MA09 | Cálculo de fração de quantidade | 6º ano |
| EF06MA10 | Operações com frações | 6º ano |

## 📁 Estrutura do Projeto

```
.
├── agente_calculador.py        # Resolve questões
├── agente_contextualizador.py  # Cria enunciados
├── agente_alternativas.py      # Gera distratores
├── agente_revisor.py           # Valida questões
├── gerador_questoes.py         # Orquestra os agentes
├── mate.py                     # API Flask
├── bncc_matematica.json        # Base de habilidades
└── requirements.txt            # Dependências
```

## 🔧 Configuração

O sistema usa o modelo **Ollama Llama 3.1 8B** com duas configurações:

- **LLM_TEXT** (temperature=0.7) - Para textos criativos
- **LLM_JSON** (temperature=0.1, format="json") - Para dados estruturados

## 📊 Fluxo de Geração

```
1. Usuário seleciona habilidade BNCC
   ↓
2. Contextualizador cria enunciado
   ↓
3. Calculador resolve e gera resposta
   ↓
4. Alternativas cria distratores
   ↓
5. Revisor valida questão completa
   ↓
6. Se aprovada: retorna questão
   Se reprovada: tenta novamente (até 3x)
```

## 📝 Exemplo de Uso via API

```python
import requests

response = requests.post('http://localhost:5000/api/gerar', 
    json={'codigo_bncc': 'EF06MA09'})

questao = response.json()
print(questao['enunciado'])
print(questao['alternativas'])
```

## ⚙️ Sistema de Validação

O AgenteRevisor verifica:

- ✅ Resposta correta está entre as alternativas
- ✅ Todas as alternativas são diferentes
- ✅ Cálculos estão corretos
- ✅ Unidades são consistentes
- ✅ Resolução está completa

## 🎓 Trabalho de Conclusão de Curso

Este projeto foi desenvolvido como TCC, demonstrando:
- Arquitetura multi-agente
- Integração com LLMs locais
- Validação automática de conteúdo educacional
- API REST para integração

## 📄 Licença

Projeto acadêmico - TCC 2024
