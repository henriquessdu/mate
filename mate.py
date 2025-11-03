"""
API Flask para o Sistema Gerador de Questões.

Fornece endpoints REST para listar habilidades, gerar questões e verificar status.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from gerador_questoes import sistema


app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)


@app.route('/')
def index():
    """
    Rota principal - retorna interface HTML.
    
    Returns:
        Template HTML da aplicação
    """
    return render_template('index.html')


@app.route('/api/habilidades', methods=['GET'])
def listar_habilidades():
    """
    Lista todas as habilidades BNCC disponíveis.
    
    Returns:
        JSON com todas as habilidades ou erro 500
    """
    try:
        habilidades = sistema.database.listar_todas()
        return jsonify(habilidades)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/api/gerar', methods=['POST'])
def gerar_questao():
    """
    Gera uma questão para a habilidade BNCC especificada.
    
    Request JSON:
        {
            "codigo_bncc": "EF06MA09"
        }
    
    Returns:
        JSON com questão gerada ou mensagem de erro
    """
    try:
        data = request.get_json()
        codigo_bncc = data.get('codigo_bncc')
        
        if not codigo_bncc:
            return jsonify({'erro': 'Código BNCC não fornecido'}), 400
        
        print(f"\n📋 Gerando questão para: {codigo_bncc}")
        
        resultado = sistema.processar_requisicao(codigo_bncc)
        
        if resultado['status'] == 'sucesso':
            print(f"✅ Questão gerada com sucesso!")
        else:
            print(f"❌ Falha na geração")
        
        return jsonify(resultado)
    
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return jsonify({
            'status': 'erro',
            'mensagem': f'Erro no servidor: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def status():
    """
    Verifica status do servidor e configuração.
    
    Returns:
        JSON com informações do sistema
    """
    return jsonify({
        'status': 'online',
        'modelo': 'Ollama Llama 3.1 8B',
        'habilidades_disponiveis': len(sistema.database.listar_todas()),
        'versao': '3.0 - Refatorado'
    })


if __name__ == '__main__':
    print("\n🍅 Mate inicializado (acesse http://localhost:5000)\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
