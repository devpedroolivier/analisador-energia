import pyodbc
from flask import Flask, request, jsonify, render_template, send_file, url_for
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os
sys.path.append("C:/Users/poliveira.eficien.SBSP/Desktop/Analisador de Sustentabilidade Energética")

from config import DATABASE_CONFIG




# Configuração do Flask
app = Flask(__name__, template_folder='../templates', static_folder='../static')


# Função para conectar ao banco de dados
def conectar_banco():
    connection_string = (
        f"Driver={{{DATABASE_CONFIG['DRIVER']}}};"
        f"Server={DATABASE_CONFIG['SERVER']};"
        f"Database={DATABASE_CONFIG['DATABASE']};"
        f"Uid={DATABASE_CONFIG['USERNAME']};"
        f"Pwd={DATABASE_CONFIG['PASSWORD']};"
        f"Encrypt={DATABASE_CONFIG['ENCRYPT']};"
        f"TrustServerCertificate={DATABASE_CONFIG['TRUST_SERVER_CERTIFICATE']};"
        f"Connection Timeout={DATABASE_CONFIG['CONNECTION_TIMEOUT']};"
    )
    return pyodbc.connect(connection_string)


# Função para salvar dados no banco
def salvar_no_banco(nome_arquivo, soma_total, media_consumo, maior_consumo, menor_consumo, local_maior_consumo, economia_kwh, economia_reais):
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analisador_energia (
                nome_arquivo, soma_total, media_consumo, maior_consumo, menor_consumo,
                local_maior_consumo, economia_potencial_kwh, economia_potencial_reais, data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome_arquivo, soma_total, media_consumo, maior_consumo, menor_consumo,
              local_maior_consumo, economia_kwh, economia_reais, datetime.now()))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")

# Rota principal
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        # Processa o arquivo CSV
        file = request.files['file']
        cost_per_kwh = request.form.get('cost', type=float, default=0.0)
        df = pd.read_csv(file)

        # Análises
        soma_total = int(df["Consumo (kWh)"].sum())
        media_consumo = float(df["Consumo (kWh)"].mean())
        maior_consumo = int(df["Consumo (kWh)"].max())
        menor_consumo = int(df["Consumo (kWh)"].min())
        local_maior_consumo = df.loc[df["Consumo (kWh)"].idxmax(), "Nome"]

        # Cria o gráfico
        graph_path = os.path.join(app.static_folder, 'consumo_grafico.png')
        plt.figure(figsize=(10, 6))
        plt.bar(df["Nome"], df["Consumo (kWh)"], color='skyblue')
        plt.title("Consumo de Energia por Local", fontsize=16)
        plt.xlabel("Local", fontsize=14)
        plt.ylabel("Consumo (kWh)", fontsize=14)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.savefig(graph_path)
        plt.close()

        # Salva o arquivo Excel para download posterior
        excel_path = os.path.join(app.static_folder, 'analise_consumo.xlsx')
        df.to_excel(excel_path, index=False)

        # Sugestões
        sugestoes = [
            f"Reduzir o consumo do {local_maior_consumo} em 10% economizaria {maior_consumo * 0.10:.2f} kWh.",
            f"Isso resultaria em uma economia de R${(maior_consumo * 0.10 * cost_per_kwh):.2f}, considerando o custo por kWh informado."
        ]

        # Renderiza os resultados no HTML
        return render_template('results.html',
                               file_name=file.filename,
                               soma_total=soma_total,
                               media_consumo=media_consumo,
                               maior_consumo=maior_consumo,
                               menor_consumo=menor_consumo,
                               sugestoes=sugestoes,
                               graph_path=url_for('static', filename='consumo_grafico.png'),
                               excel_path=url_for('static', filename='analise_consumo.xlsx'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Rota para exibir histórico de análises
@app.route('/historico', methods=['GET'])
def historico():
    try:
        conn = conectar_banco()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analisador_energia")
        registros = cursor.fetchall()
        conn.close()

        # Estruturação dos resultados
        colunas = ["id", "nome_arquivo", "soma_total", "media_consumo", "maior_consumo", "menor_consumo",
                   "local_maior_consumo", "economia_potencial_kwh", "economia_potencial_reais", "data"]
        dados = [dict(zip(colunas, registro)) for registro in registros]

        return jsonify(dados)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
