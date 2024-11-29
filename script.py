import pandas as pd
import random
from datetime import datetime, timedelta

# Função para gerar dados aleatórios
def gerar_dados():
    locais = ['Residência', 'Loja', 'Escola', 'Fábrica', 'Escritório Regional']
    dados = []

    # Gerar dados para 5 locais diferentes
    for local in locais:
        for i in range(5):  # 5 registros por local
            consumo = random.randint(100, 2000)  # Consumo aleatório entre 100 e 2000 kWh
            data = datetime.today() - timedelta(days=random.randint(0, 30))  # Data aleatória dentro do último mês
            dados.append([local, consumo, data.strftime('%Y-%m-%d')])

    return dados

# Gerar os dados
dados_energia = gerar_dados()

# Criar um DataFrame
df = pd.DataFrame(dados_energia, columns=['Nome', 'Consumo (kWh)', 'Data'])

# Salvar o DataFrame em um arquivo CSV
file_path = 'consumo_teste.csv'
df.to_csv(file_path, index=False)

print(f"Arquivo CSV {file_path} criado com sucesso!")
