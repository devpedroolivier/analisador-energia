from flask import Flask, request, jsonify, render_template, send_file, url_for
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Configura o backend do Matplotlib para evitar erros de thread
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Configuração do Flask e caminhos
app = Flask(__name__, template_folder='../templates', static_folder='../static')  # Define as pastas para templates e arquivos estáticos

@app.route('/')
def home():
    return render_template('index.html')  # Renderiza o arquivo HTML principal

@app.route('/upload', methods=['POST'])
def upload_data():
    try:
        # Verifica se um arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({"error": "Nenhum arquivo foi enviado."}), 400

        file = request.files['file']
        cost_per_kwh = request.form.get('cost', type=float, default=0.0)

        # Lê o arquivo CSV para um DataFrame do pandas
        df = pd.read_csv(file)

        # Verifica se o DataFrame contém as colunas esperadas
        if "Nome" not in df.columns or "Consumo (kWh)" not in df.columns:
            return jsonify({"error": "O arquivo deve conter as colunas 'Nome' e 'Consumo (kWh)'."}), 400

        # Realiza análises básicas
        soma_total = int(df["Consumo (kWh)"].sum())
        media_consumo = float(df["Consumo (kWh)"].mean())
        maior_consumo = int(df["Consumo (kWh)"].max())
        menor_consumo = int(df["Consumo (kWh)"].min())

        # Cálculo de custos e economia potencial
        local_maior_consumo = df.loc[df["Consumo (kWh)"].idxmax(), "Nome"]
        economia_potencial_kwh = maior_consumo * 0.10  # 10% de redução
        economia_potencial_reais = economia_potencial_kwh * cost_per_kwh if cost_per_kwh > 0 else 0

        # Sugestões
        sugestoes = [
            f"Reduzir o consumo do {local_maior_consumo} em 10% economizaria {economia_potencial_kwh:.2f} kWh.",
            f"Isso resultaria em uma economia de R${economia_potencial_reais:.2f}, considerando o custo por kWh informado.",
            f"O {local_maior_consumo} representa {df.loc[df['Nome'] == local_maior_consumo, 'Consumo (kWh)'].sum() / soma_total * 100:.2f}% do consumo total."
        ]

        # Gera um gráfico de barras com Matplotlib
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

        # Gera o relatório em PDF
        pdf_path = os.path.join(app.static_folder, 'relatorio_consumo.pdf')
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, 750, "Relatório de Consumo de Energia")
        c.setFont("Helvetica", 12)
        c.drawString(100, 700, f"Soma Total do Consumo: {soma_total} kWh")
        c.drawString(100, 680, f"Consumo Médio: {media_consumo:.2f} kWh")
        c.drawString(100, 660, f"Maior Consumo: {maior_consumo} kWh")
        c.drawString(100, 640, f"Menor Consumo: {menor_consumo} kWh")
        c.drawString(100, 600, "Sugestões:")
        y = 580
        for sugestao in sugestoes:
            c.drawString(120, y, f"- {sugestao}")
            y -= 20
        c.drawImage(graph_path, 100, 300, width=400, height=250)
        c.save()

        # Renderiza o template HTML com os resultados
        return render_template('results.html',
                               file_name=file.filename,
                               soma_total=soma_total,
                               media_consumo=media_consumo,
                               maior_consumo=maior_consumo,
                               menor_consumo=menor_consumo,
                               sugestoes=sugestoes,
                               graph_path=url_for('static', filename='consumo_grafico.png'),
                               pdf_path=url_for('static', filename='relatorio_consumo.pdf'),
                               excel_path=url_for('static', filename='analise_consumo.xlsx'))
    except Exception as e:
        print(f"Erro no servidor: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/export/excel', methods=['GET'])
def export_excel():
    try:
        excel_path = os.path.join(app.static_folder, 'analise_consumo.xlsx')
        if not os.path.exists(excel_path):
            return jsonify({"error": "O arquivo Excel não foi gerado ainda."}), 404
        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        print(f"Erro no servidor: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/export/pdf', methods=['GET'])
def export_pdf():
    try:
        pdf_path = os.path.join(app.static_folder, 'relatorio_consumo.pdf')
        if not os.path.exists(pdf_path):
            return jsonify({"error": "O arquivo PDF não foi gerado ainda."}), 404
        return send_file(pdf_path, as_attachment=True)
    except Exception as e:
        print(f"Erro no servidor: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)
