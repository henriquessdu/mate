# 🍅 Mate | Sistema de Geração de Questões de Matemática com IA

Sistema multiagentes inteligente para geração automática de questões de matemática alinhadas à BNCC (Base Nacional Comum Curricular), desenvolvido como parte do TCC: **"Aplicação de Inteligência Artificial na Criação de Questões de Matemática para o Ensino Básico"**.

## 🎯 Sobre o Projeto

A Mate utiliza técnicas de Inteligência Artificial e arquitetura multiagentes para criar questões de matemática contextualizadas, com resolução passo a passo e alternativas plausíveis. O sistema opera completamente local usando Ollama e o modelo LLaMA 3.1 8B.

### Características Principais

- ✅ **Geração automática** de questões alinhadas às habilidades BNCC
- 🤖 **Arquitetura multiagentes** especializada (RAG-like)
- 📝 **Contextualização** automática dos enunciados
- 🔢 **Cálculo e validação** automática das respostas
- 🎲 **Distratores plausíveis** para múltipla escolha
- ✔️ **Revisão automática** de qualidade
- 🌐 **Interface web** simples e intuitiva
- 💻 **100% local** - sem dependência de APIs externas

## 🏗️ Arquitetura

O sistema é composto por 4 agentes especializados que trabalham em pipeline:

```
┌─────────────────────────────────────────────────────┐
│   SISTEMA MATE                                      │
└─────────────────────────────────────────────────────┘
                                                
   1️⃣  Agente Contextualizador                               
       └─> Cria enunciado contextualizado                     
                                                              
   2️⃣  Agente Calculador                                      
       └─> Resolve e gera resolução passo a passo             
                                                               
   3️⃣  Agente Alternativas                                    
       └─> Gera distratores plausíveis (A, B, C, D)            
                                                                
  4️⃣  Agente Revisor                                         
      └─> Valida questão completa e aprova/reprova            
                                                             
```

### Fluxo de Geração

1. **Entrada**: Código de habilidade BNCC (ex: `EF06MA09`)
2. **Processamento**: Pipeline de 4 agentes
3. **Validação**: Até 3 tentativas com revisão automática
4. **Saída**: Questão completa validada ou mensagem de erro

## 🚀 Instalação

### Pré-requisitos

- Python 3.8+
- [Ollama](https://ollama.ai/) instalado e rodando
- Modelo LLaMA 3.1 8B baixado no Ollama

### Passos

1. **Clone o repositório**
```bash
git clone https://github.com/henriquessdu/mate.git
cd mate
```

2. **Instale as dependências**
```bash
pip install -r requirements.txt
```

3. **Baixe o modelo LLaMA no Ollama**
```bash
ollama pull llama3.1:8b
```

4. **Execute o sistema**
```bash
python mate.py
```

5. **Acesse a interface**
```
http://localhost:5000
```

## 📖 Como Usar

### Interface Web

1. Acesse `http://localhost:5000`
2. Selecione uma habilidade BNCC do menu
3. Clique em "Gerar Questão"
4. Aguarde o processamento (pode levar alguns segundos)
5. Visualize a questão gerada com alternativas e resolução

### API REST

#### Listar Habilidades
```bash
GET /api/habilidades
```

#### Gerar Questão
```bash
POST /api/gerar
Content-Type: application/json

{
  "codigo_bncc": "EF06MA09"
}
```

#### Verificar Status
```bash
GET /api/status
```

### Exemplo de Uso Programático

```python
from gerador_questoes import sistema

# Gerar questão para habilidade específica
resultado = sistema.processar_requisicao("EF06MA09")

if resultado['status'] == 'sucesso':
    print("Enunciado:", resultado['enunciado'])
    print("Alternativas:", resultado['alternativas'])
    print("Resolução:", resultado['resolucao'])
else:
    print("Erro:", resultado['mensagem'])
```

## 📁 Estrutura do Projeto

```
mate/
├── agentes/
│   ├── __init__.py                  # Módulo de agentes
│   ├── agente_contextualizador.py   # Cria enunciados
│   ├── agente_calculador.py         # Resolve questões
│   ├── agente_alternativas.py       # Gera distratores
│   └── agente_revisor.py            # Valida questões
├── bncc_matematica.json             # Base de habilidades BNCC
├── gerador_questoes.py              # Sistema orquestrador
├── mate.py                          # API Flask
├── index.html                       # Interface web
├── utils.py                         # Funções utilitárias
├── requirements.txt                 # Dependências Python
└── README.md                        # Este arquivo
```

## 🔧 Tecnologias Utilizadas

- **Python 3.8+**: Linguagem principal
- **Flask**: Framework web para API REST
- **LangChain**: Orquestração de LLMs
- **Ollama**: Execução local de modelos LLM
- **LLaMA 3.1 8B**: Modelo de linguagem
- **HTML/CSS/JavaScript**: Interface frontend

## 🎓 Habilidades BNCC Suportadas

O sistema atualmente suporta as seguintes habilidades:

- **EF06MA03**: Cálculos com números naturais (6º ano)
- **EF06MA09**: Frações de quantidades (6º ano)
- **EF07MA02**: Problemas com porcentagens (7º ano)
- **EF07MA18**: Equações de 1º grau (7º ano)
- **EF08MA02**: Potenciação e radiciação (8º ano)

*Novos códigos podem ser adicionados no arquivo `bncc_matematica.json`*

## 🧠 Como Funciona

### 1. Agente Contextualizador
Recebe a habilidade BNCC e cria um enunciado contextualizado adequado ao ano escolar, usando situações cotidianas e linguagem apropriada.

### 2. Agente Calculador
Resolve a questão matematicamente e gera uma resolução passo a passo detalhada, incluindo todos os cálculos intermediários.

### 3. Agente Alternativas
Cria 3 distratores plausíveis (alternativas incorretas) usando o LLM ou métodos de perturbação numérica, garantindo que sejam diferentes da resposta correta.

### 4. Agente Revisor
Valida a questão completa verificando:
- Ausência de duplicatas nas alternativas
- Correção dos cálculos
- Consistência das unidades
- Qualidade geral da questão

Se reprovada, o sistema tenta novamente (até 3 vezes).

## ⚙️ Configuração

### Modificar Modelo LLM

Edite o arquivo `gerador_questoes.py`:

```python
OLLAMA_MODEL = "llama3.1:8b"  # Altere para outro modelo
```

### Ajustar Temperatura

```python
LLM_TEXT = Ollama(
    model=OLLAMA_MODEL,
    temperature=0.7,  # Ajuste entre 0.0 e 1.0
    num_predict=3000
)
```

### Adicionar Novas Habilidades

Edite `bncc_matematica.json`:

```json
{
  "EF09MA99": {
    "codigo": "EF09MA99",
    "descricao": "Descrição da habilidade...",
    "ano": "9º ano",
    "eixo": "Álgebra"
  }
}
```

## 📚 Trabalho Acadêmico

Este sistema foi desenvolvido como parte do Trabalho de Conclusão de Curso (TCC) em Engenharia de Computação:

**Título:** Aplicação de Inteligência Artificial na Criação de Questões de Matemática para o Ensino Básico

**Autor:** Henrique Salles Souza Duarte

**Instituição:** Centro Universitário Facens

**Ano:** 2025

**Orientador:** Prof. Allan Marconato Marum

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.
