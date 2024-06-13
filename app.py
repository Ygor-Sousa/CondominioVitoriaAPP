from flask import Flask, redirect, render_template, jsonify, request, url_for, session

from flask_bcrypt import Bcrypt

import mysql.connector

import json

import datetime

from datetime import datetime

bcrypt = Bcrypt()

app = Flask(__name__, template_folder="templates")

app.secret_key = 'F0xtr0t'  # Defina uma chave secreta única


def get_apartamentos():
  """
  Obtém os dados da tabela "apartamentos".

  Retorna:
    Uma lista de dicionários com os dados dos apartamentos.
  """

  conexao = mysql.connector.connect(
    host="mysql.hypevitro.com.br",
    user="condominiovito",
    password="F0xtr0t979",
    database="condominiovito"
  )

  cursor = conexao.cursor()
  cursor.execute("SELECT * FROM apartamentos")

  apartamentos = []
  for apartamento in cursor.fetchall():
    apartamentos.append({
      "id": apartamento[0],
      "bloco": apartamento[1],
      "apartamento": apartamento[2],
      "morador": apartamento[3],
      "carros": json.loads(apartamento[4]),
    })

  cursor.close()
  conexao.close()

  return apartamentos

# ... (seu código existente) ...

@app.route("/login", methods=['GET', 'POST'])
def login():
    mensagem = None

    if request.method == 'POST':
        # Obtenha as credenciais do formulário
        username = request.form['username']
        password = request.form['password']

        # Faça a validação das credenciais (por exemplo, em um banco de dados)
        if validar_credenciais(username, password):
            # Se as credenciais são válidas, adicione 'username' à sessão e redirecione para a página principal
            session['username'] = username
            session['nivel_acesso'] = validar_credenciais(username, password)[1]  # Adiciona o nível de acesso à sessão
            return redirect(url_for('index'))
        else:
            # Se as credenciais são inválidas, defina a mensagem de erro na sessão
            mensagem = "Credenciais inválidas"
            session['mensagem'] = mensagem

            # Redirecione para a página de login
            return redirect(url_for('login'))

    # Se o método é GET, apenas renderize a página de login
    # Passe a mensagem diretamente para o template
    return render_template("login.html", mensagem=session.get('mensagem'))

def validar_credenciais(username, password):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor()
    cursor.execute("SELECT password_hash, nivel_acesso FROM usuarios WHERE username = %s", (username,))
    resultado = cursor.fetchone()
    cursor.close()
    conexao.close()

    if resultado and bcrypt.check_password_hash(resultado[0], password):
        return True, resultado[1]  # Retorna True e o nível de acesso se as credenciais são válidas
    else:
        return False, None  # Retorna False se as credenciais são inválidas


@app.route("/", methods=['GET', 'POST'])
def index():
    
    # Verifique se o usuário está autenticado
    if 'username' not in session:
        # Se não estiver autenticado, redirecione para a página de login
        return redirect(url_for('login'))

    # Obtenha os dados dos apartamentos após a atualização
    apartamentos = get_apartamentos()

    return render_template("index.html", apartamentos=apartamentos)


# Função para executar a consulta SQL e obter os resultados
def executar_consulta():
    # Conecte-se ao banco de dados
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor(dictionary=True)  # Definindo o cursor para retornar os resultados como dicionários

    # Execute a consulta SQL
    cursor.execute("""
        SELECT
          bloco,
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": true}') THEN 1 ELSE 0 END) AS placas_presentes,
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": false}') THEN 1 ELSE 0 END) AS placas_ausentes
        FROM
          apartamentos
        GROUP BY
          bloco;
    """)

    # Obtenha os resultados como uma lista de dicionários
    resultados = cursor.fetchall()

    # Feche a conexão com o banco de dados
    cursor.close()
    conexao.close()

    return resultados


@app.route("/resultado_consulta")
def resultado_consulta():
    # Execute sua consulta SQL aqui e obtenha os resultados
    resultados = executar_consulta()

    # Calcule o total de presentes e ausentes
    total_presentes = sum(resultado['placas_presentes'] for resultado in resultados)
    total_ausentes = sum(resultado['placas_ausentes'] for resultado in resultados)

    # Retorna os totais como uma resposta JSON
    return jsonify({"total_presentes": total_presentes, "total_ausentes": total_ausentes})


# Função para executar a consulta SQL e obter os resultados
def executar_consulta_blocos():
    # Conecte-se ao banco de dados
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor()

    # Execute a consulta SQL
    cursor.execute("""
        SELECT
          bloco,
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": true}') THEN 1 ELSE 0 END) AS placas_presentes,
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": false}') THEN 1 ELSE 0 END) AS placas_ausentes
        FROM
          apartamentos
        GROUP BY
          bloco;
    """)

    # Obtenha os resultados
    resultadosBlocos = cursor.fetchall()

    # Feche a conexão com o banco de dados
    cursor.close()
    conexao.close()

    return resultadosBlocos

@app.route("/resultado_consulta_blocos")
def resultado_consulta_blocos():
    # Execute sua consulta SQL aqui e obtenha os resultados
    resultadosBlocos = executar_consulta_blocos()

    # Inicialize um dicionário para armazenar os resultados por bloco
    resultados_por_bloco = {}

    # Organize os resultados por bloco
    for resultado in resultadosBlocos:
        bloco = resultado[0]
        presentes = resultado[1]
        ausentes = resultado[2]
        resultados_por_bloco[bloco] = f'<i class="fa-solid fa-car" style="color: #07c713;"></i> {presentes} <i class="fa-solid fa-car" style="color: #e70a0a;"></i> {ausentes}'

    # Retorna os resultados organizados por bloco como uma resposta JSON
    return jsonify(resultados_por_bloco)




@app.route("/atualizar_vaga", methods=['POST'])
def atualizar_vaga_route():
    # Obtenha os dados do formulário do pedido POST
    id = request.form['id']
    apartamento = request.form['apartamento']
    morador = request.form['morador']
    placa = request.form['placa']
    veiculo = request.form['veiculo']
    cor = request.form['cor']
    tipoVeiculo = request.form['tipo_veiculo']
    presente = request.form['presente']
    usuario = session['username']  # Obtenha o nome do usuário da sessão
    indiceCarro = request.form['indiceCarro'] 
    

    # Chame a função atualizar_vaga com os dados do formulário
    atualizar_vaga(apartamento, morador, placa, veiculo, cor, tipoVeiculo, presente, usuario, id, indiceCarro)

    # Retorne uma resposta JSON para indicar sucesso
    return jsonify({"message": "Vaga atualizada com sucesso!"})

def atualizar_vaga(apartamento, morador, placa, veiculo, cor, tipoVeiculo, presente, usuario, id, indiceCarro):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    bloco = apartamento[0]

    print('Query:', apartamento, morador, placa, veiculo, cor, tipoVeiculo)

    cursor = conexao.cursor()

    # Executando a consulta SQL para atualizar a vaga
     # Verificando se há outro carro presente para o mesmo apartamento
    """sql_select = "SELECT COUNT(*) FROM apartamentos WHERE bloco = %s AND apartamento = %s AND JSON_EXTRACT(placa, CONCAT('$[', %s, '].presente')) = false"
    values_select = (bloco, apartamento, indiceCarro)
    cursor.execute(sql_select, values_select)
    resultado = cursor.fetchone()
    if resultado[0] > 0:
        # Se já existe um carro presente, retorne uma mensagem de erro ou faça o tratamento adequado
        return jsonify({"error": "Já existe um carro presente para este apartamento."})"""

    # Executando a consulta SQL para atualizar a vaga
    sql_update = f"UPDATE apartamentos SET placa = JSON_SET(placa, '$[{indiceCarro}].presente', {presente}) WHERE id = %s"
    values_update = (id,)
    cursor.execute(sql_update, values_update)

    conexao.commit()

    movimentacao = ''

    if presente == 'true':
        movimentacao = 'Saída'
        print('if:', presente)
    else:
        movimentacao = 'Entrada'
        print('else:', presente)

    # Verificando se o update foi bem-sucedido
    if cursor.rowcount > 0:
        # Se o update foi bem-sucedido, inserir um registro de log
        acao = f"Movimentação de {movimentacao} do veículo {veiculo} - apartamento {apartamento} feita por: {usuario}"

        data_atual = datetime.now().date()
        hora_atual = datetime.now().time()

        # Executando a consulta SQL para inserir o registro de log
        sql_insert_log = "INSERT INTO logs (usuario, apartamento, placa, acao, data, hora) VALUES (%s, %s, %s, %s, %s, %s)"
        values_insert_log = (usuario, apartamento, placa, acao, data_atual, hora_atual)
        print(sql_insert_log)
        cursor.execute(sql_insert_log, values_insert_log)
        conexao.commit()

    cursor.close()
    conexao.close()


@app.route("/logout")
def logout():
  # Remova 'username' da sessão (logout)
  session.pop('username', None)
  return redirect(url_for('login'))

@app.route("/api/apartamentos")
def get_apartamentos_json():
    # Verifique se foi fornecido o parâmetro de consulta 'bloco'
    bloco = request.args.get('bloco')

    if bloco:
        # Obtém os dados dos apartamentos apenas para o bloco especificado
        apartamentos = [apartamento for apartamento in get_apartamentos() if apartamento['bloco'] == bloco]
        # Obtenha os totais de presentes e ausentes para o bloco especificado
        resultados = get_presenca_placas(bloco)
        # Adicione os resultados à resposta JSON
        response = {
            "apartamentos": apartamentos,
            "total_presentes": resultados["total_presentes"],
            "total_ausentes": resultados["total_ausentes"]
        }
    else:
        # Se nenhum bloco foi especificado, retorna todos os apartamentos
        apartamentos = get_apartamentos()
        response = {
            "apartamentos": apartamentos
        }

    return jsonify(response)



def get_presenca_placas(bloco):
    """
    Obtém os totais de presentes e ausentes para um bloco específico.

    Parâmetros:
      bloco (str): O bloco específico para o qual os totais devem ser calculados.

    Retorna:
      Um dicionário contendo os totais de presentes e ausentes.
    """

    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor(dictionary=True)

    # Execute a consulta SQL para obter os totais de presentes e ausentes para o bloco especificado
    sql = """
        SELECT
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": true}') THEN 1 ELSE 0 END) AS placas_presentes,
          SUM(CASE WHEN JSON_CONTAINS(placa, '{"presente": false}') THEN 1 ELSE 0 END) AS placas_ausentes
        FROM
          apartamentos
        WHERE
          bloco = %s
        GROUP BY
          bloco;
    """
    cursor.execute(sql, (bloco,))
    resultado = cursor.fetchone()

    total_presentes = resultado['placas_presentes'] if resultado else 0
    total_ausentes = resultado['placas_ausentes'] if resultado else 0

    cursor.close()
    conexao.close()

    return {"total_presentes": total_presentes, "total_ausentes": total_ausentes}


@app.route("/search", methods=['GET'])
def search():
    search_query = request.args.get('query')
    apartamento_query = request.args.get('apartamento')  # Novo parâmetro de consulta para o apartamento

    # Se ambas as consultas de pesquisa estiverem vazias, retorne todos os apartamentos
    if not search_query and not apartamento_query:
        return jsonify(get_apartamentos())

    # Filtra os apartamentos com base na consulta de pesquisa e/ou no número do apartamento
    filtered_apartamentos = []

    for apartamento in get_apartamentos():
        if (not search_query or any(carro for carro in apartamento['carros'] if search_query.lower() in carro['placa'].lower())) and \
           (not apartamento_query or apartamento_query.lower() in apartamento['apartamento'].lower()):
            filtered_apartamentos.append(apartamento)

    # Calcula os totais de presentes e ausentes para o bloco especificado na pesquisa
    totais = get_presenca_placas(apartamento_query)

    # Retorna os apartamentos filtrados e os totais como uma resposta JSON
    return jsonify({"apartamentos": filtered_apartamentos, "totais": totais})




@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    # Verifique se o usuário está autenticado
    if 'username' not in session:
        # Se não estiver autenticado, redirecione para a página de login
        return redirect(url_for('login'))

    mensagem_sucesso = None

    if request.method == 'POST':
        # Recupere os dados do formulário
        username = request.form['username']
        senha = request.form['senha']

        # Hash da senha usando bcrypt
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

        # Insira o usuário no banco de dados
        cadastrar_usuario(username, senha_hash)

        # Defina a mensagem de sucesso
        mensagem_sucesso = "Usuário cadastrado com sucesso!"

    return render_template("cadastro.html", mensagem_sucesso=mensagem_sucesso)

def cadastrar_usuario(username, senha_hash):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor()
    cursor.execute("INSERT INTO usuarios (username, password_hash) VALUES (%s, %s)", (username, senha_hash))
    conexao.commit()
    cursor.close()
    conexao.close()



@app.route("/cadastroApartamento", methods=['GET', 'POST'])
def cadastroApartamento():
    # Verifique se o usuário está autenticado
    if 'username' not in session:
        # Se não estiver autenticado, redirecione para a página de login
        return redirect(url_for('login'))

    mensagem_sucesso = None

    # Verifique se o usuário tem permissão de administrador (ADM)
    if session.get('nivel_acesso') != 'ADM':
        # Se não tiver permissão, redirecione para alguma página de erro ou de acesso negado
        return render_template("erro_acesso_negado.html")

    if request.method == 'POST':
        # Recupere os dados do formulário
        apartamento = request.form['apartamento']
        morador = request.form['morador']
        placa = request.form['placa']
        veiculo = request.form['veiculo']
        cor = request.form['cor']
        tipoVeiculo = request.form['tipo_veiculo']

        # Insira o usuário no banco de dados
        cadastrar_apartamento(apartamento, morador, placa, veiculo, cor, tipoVeiculo)

        # Defina a mensagem de sucesso
        mensagem_sucesso = "Apartamento cadastrado com sucesso!"

    return render_template("cadastroApartamento.html", mensagem_sucesso=mensagem_sucesso)

def cadastrar_apartamento(apartamento, morador, placa, veiculo, cor, tipoVeiculo):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    bloco = apartamento[0]

    print('Query:', apartamento, morador, placa, veiculo, cor, tipoVeiculo)

    cursor = conexao.cursor()

    # Criando um dicionário com os dados do veículo
    veiculo_data = [{
        'veiculo': veiculo,
        'cor': cor,
        'placa': placa,
        'presente': True,
        'tipoVeiculo': tipoVeiculo
    }]

    # Convertendo o dicionário para JSON
    placa_json = json.dumps(veiculo_data)

    # Executando a consulta SQL
    sql = "INSERT INTO apartamentos (bloco, apartamento, morador, placa) VALUES (%s, %s, %s, %s)"
    values = (bloco, apartamento, morador, placa_json)
    cursor.execute(sql, values)
    conexao.commit()
    cursor.close()
    conexao.close()



@app.route("/crudApartamento", methods=['GET', 'POST'])
def crudApartamento():
    # Verifique se o usuário está autenticado
    if 'username' not in session:
        # Se não estiver autenticado, redirecione para a página de login
        return redirect(url_for('login'))
    
    # Verifique se o usuário tem permissão de administrador (ADM)
    if session.get('nivel_acesso') != 'ADM':
        # Se não tiver permissão, redirecione para alguma página de erro ou de acesso negado
        return render_template("erro_acesso_negado.html")

    if request.method == 'POST':
        # Recupere os dados do formulário
        apartamento = request.form['apartamento']
        morador = request.form['morador']
        placa = request.form['placa']
        veiculo = request.form['veiculo']
        cor = request.form['cor']
        tipoVeiculo = request.form['tipo_veiculo']
        usuario = session['username']  # Obtenha o nome do usuário da sessão
        # Dados ocultos Formulario
        id = request.form['id']

        # Realize a atualização no banco de dados
        update_apartamento(apartamento, morador, placa, veiculo, cor, tipoVeiculo, usuario, id)

        # Após o envio do formulário, redirecione para a rota de exibição (GET)
        return redirect(url_for('index'))

    # Obtenha os dados dos apartamentos após a atualização
    apartamentos = get_apartamentos()

    return render_template("crudApartamento.html", apartamentos=apartamentos)


def update_apartamento(apartamento, morador, placa, veiculo, cor, tipoVeiculo, usuario, id):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    
    """ Atualiza os dados do apartamento no banco de dados. """


    bloco = apartamento[0]

    cursor = conexao.cursor()

    # Executando a consulta SQL
    sql = "UPDATE apartamentos SET bloco = %s, apartamento = %s, morador = %s, placa = JSON_SET(placa,'$[0].cor', %s, '$[0].placa', %s, '$[0].veiculo', %s, '$[0].tipoVeiculo', %s) WHERE id = %s;"
    values = (bloco, apartamento, morador, cor, placa, veiculo, tipoVeiculo, id)
    cursor.execute(sql, values)
    
    # Imprima a query no console
    print("Query executada:", cursor.statement)

    conexao.commit()
    cursor.close()
    conexao.close()


def get_logs(filtro_apartamento=None, filtro_placa=None):
    conexao = mysql.connector.connect(
        host="mysql.hypevitro.com.br",
        user="condominiovito",
        password="F0xtr0t979",
        database="condominiovito"
    )

    cursor = conexao.cursor(dictionary=True)

    if filtro_apartamento and filtro_placa:
        cursor.execute("SELECT * FROM logs WHERE apartamento LIKE %s AND placa LIKE %s", ('%' + filtro_apartamento + '%', '%' + filtro_placa + '%'))
    elif filtro_apartamento:
        cursor.execute("SELECT * FROM logs WHERE apartamento LIKE %s", ('%' + filtro_apartamento + '%',))
    elif filtro_placa:
        cursor.execute("SELECT * FROM logs WHERE placa LIKE %s", ('%' + filtro_placa + '%',))
    else:
        cursor.execute("SELECT * FROM logs")

    logs = cursor.fetchall()

    cursor.close()
    conexao.close()

    return logs



@app.route("/logs")
def logs():
    # Verifique se o usuário está autenticado
    if 'username' not in session:
        # Se não estiver autenticado, redirecione para a página de login
        return redirect(url_for('login'))
    
    # Verifique se o usuário tem permissão de administrador (ADM)
    if session.get('nivel_acesso') != 'ADM':
        # Se não tiver permissão, redirecione para alguma página de erro ou de acesso negado
        return render_template("erro_acesso_negado.html")
    
    filtro_apartamento = request.args.get('filtro_apartamento')
    filtro_placa = request.args.get('filtro_placa')
    filtro_original = request.args.get('filtro_original')

    if filtro_original and not (filtro_apartamento or filtro_placa):
        return redirect(url_for('logs'))

    logs = get_logs(filtro_apartamento, filtro_placa)
    
    return render_template("logs.html", logs=logs)





if __name__ == "__main__":
  app.run(debug=True)
