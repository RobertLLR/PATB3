
import os
import yfinance as yf
import pandas as pd

# Define o arquivo que armazena os dados históricos.
nome_arquivo = "BBAS3_2024_2025.csv"

# Define o ativo e a data inicial do histórico.
ativo = "BBAS3.SA"
data_inicial = "2025-01-01"

# Verifica se o arquivo CSV já existe.
if os.path.exists(nome_arquivo):

    # Lê os dados históricos existentes.
    dados_antigos = pd.read_csv(
        nome_arquivo,
        parse_dates=["Date"]
    )

    # Identifica a última data registrada.
    ultima_data = dados_antigos["Date"].max()

    # Define o início da próxima busca.
    data_inicio = (
        ultima_data + pd.Timedelta(days=1)
    ).strftime("%Y-%m-%d")

    print("Última data registrada:", ultima_data.strftime("%d/%m/%Y"))
    print("Buscando dados a partir de:", data_inicio)

else:

    # Caso o arquivo não exista, inicia o histórico em 2024.
    dados_antigos = pd.DataFrame()
    data_inicio = data_inicial

    print("Arquivo não encontrado. Criando histórico inicial.")

# Baixa somente os dados posteriores à última data registrada.
novos_dados = yf.download(
    ativo,
    start=data_inicio,
    interval="1d",
    auto_adjust=False,
    progress=False
)

# Verifica se o download retornou dados.
if novos_dados.empty:

    print("Nenhum dado novo encontrado.")

else:

    # Trata as colunas múltiplas do yfinance.
    if isinstance(novos_dados.columns, pd.MultiIndex):
        novos_dados.columns = novos_dados.columns.get_level_values(0)

    # Mantém todas as informações disponibilizadas.
    novos_dados = novos_dados[
        ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    ].copy()

    # Transforma o índice de datas em uma coluna.
    novos_dados.index.name = "Date"
    novos_dados = novos_dados.reset_index()

    # Junta os dados antigos com os novos.
    arquivo = pd.concat(
        [dados_antigos, novos_dados],
        ignore_index=True
    )

    # Remove possíveis datas duplicadas.
    arquivo = arquivo.drop_duplicates(
        subset=["Date"],
        keep="last"
    )

    # Organiza os registros pela data.
    arquivo = arquivo.sort_values("Date")

    # Salva o histórico atualizado.
    arquivo.to_csv(nome_arquivo, index=False)

    print("Arquivo atualizado com sucesso!")
    print("Quantidade de pregões:", len(arquivo))
    print("Primeira data:", arquivo["Date"].iloc[0])
    print("Última data:", arquivo["Date"].iloc[-1])
