import yfinance as yf
import pandas as pd
from pathlib import Path

#período
DATA_INICIAL = "2014-01-01"
DATA_FINAL = "2026-01-01"

# DataFrame
controle = pd.DataFrame(columns=["nome", "data_inicial", "data_final"])

def baixar_acao(ticker):
    print(f"Baixando dados de {ticker}...")
    dados = yf.download(
        ticker,
        start=DATA_INICIAL,
        end=DATA_FINAL,
        progress=False,
        auto_adjust=False,
        actions=True #pede ao yfinance para incluir dividendos e splits no DataFrame
    )

    if dados.empty:
        print(f"Erro: não encontrou dados para {ticker}")
        return None

    data_inicial = dados.index.min().strftime("%Y-%m-%d")
    data_final = dados.index.max().strftime("%Y-%m-%d")

    # Corrige as colunas do yfinance
    if isinstance(dados.columns, pd.MultiIndex):
       dados.columns = dados.columns.get_level_values(0)

    # Renomeia a coluna "Adj Close" para "Adj. Close"
    dados = dados.rename(columns={"Adj Close": "Adj. Close"})

    # Transforma a data em uma coluna
    dados = dados.reset_index()
    # Deixa somente a data, sem 00:00:00
    dados["Date"] = dados["Date"].dt.date
    # Organiza as colunas
    dados = dados[["Date", "Close", "Adj. Close", "High", "Low",
    "Open", "Volume", "Dividends", "Stock Splits"]]
    
    # Cria a pasta "acoes" se não existir
    pasta = Path(__file__).resolve().parent / "acoes"

    pasta_csv = pasta / "csv"
    pasta_excel = pasta / "excel"

    pasta_csv.mkdir(parents=True, exist_ok=True)
    pasta_excel.mkdir(parents=True, exist_ok=True)

    caminho = pasta_csv / f"{ticker.replace('.', '_')}.csv"
    dados.to_csv(
    caminho,
    sep=";",
    decimal=",",
    index=False,
    encoding="utf-8-sig",
    float_format="%.6f"
    )
    #salva em excel
    caminho_excel = pasta_excel / f"{ticker.replace('.', '_')}.xlsx"
    dados.to_excel(
        caminho_excel,
        index=False,
        engine="openpyxl"
    )
    #cria um arquivo separado para os eventos de dividendos e splits
    eventos = dados.loc[
    (dados["Dividends"] != 0) | (dados["Stock Splits"] != 0),
    ["Date", "Dividends", "Stock Splits"]
    ]

    caminho_eventos = pasta_csv / f"{ticker.replace('.', '_')}_eventos.csv"
    eventos.to_csv(
    caminho_eventos,
    sep=";",
    decimal=",",
    index=False,
    encoding="utf-8-sig"
    )
    #salva os eventos em excel
    caminho_eventos_excel = pasta_excel / f"{ticker.replace('.', '_')}_eventos.xlsx"
    eventos.to_excel(
        caminho_eventos_excel,
        index=False,
        engine="openpyxl"
    )

    global controle 
    nova_linha = pd.DataFrame({
        "nome": [ticker],
        "data_inicial": [data_inicial],
        "data_final": [data_final]
    })

    controle = pd.concat([controle, nova_linha], ignore_index=True)

    print(f"Período: {data_inicial} até {data_final}")
    print("-" * 40)

    return dados

# lista das 30 ações 
acoes = [
    # Financeiro
    "BBAS3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "B3SA3.SA",
    "BPAC11.SA", #antes: BIDI11

    # Energia elétrica
    "CMIG4.SA", #codigo anterior: ELET3/AXIA3
    "CPFE3.SA", 
    "TAEE11.SA",

    # Petróleo, gás e biocombustíveis
    "PETR4.SA",

    # Mineração e siderurgia
    "VALE3.SA",
    "CSNA3.SA",
    "GGBR4.SA",
    "USIM5.SA",

    # Papel e celulose
    "SUZB3.SA",
    "KLBN11.SA",

    # Alimentos
    "ABEV3.SA", #codigo anterior: JBSS3
    "BEEF3.SA", #antes:brfs3

    # Varejo
    "MGLU3.SA",
    "LREN3.SA",

    # Bens industriais
    "WEGE3.SA",
    "RAPT4.SA", #codigo anterior: EMBR3

    # Saúde
    "RADL3.SA",
    "HAPV3.SA",
    "FLRY3.SA", #antes: pard3

    # Educação
    "COGN3.SA",
    "YDUQ3.SA",

    # Telecomunicações
    "TIMS3.SA",
    "VIVT3.SA",

    # Transporte e infraestrutura
    "RAIL3.SA",
    "ECOR3.SA" #codigo anterior: CCRO3
]

# Baixa todas as ações da lista automaticamente
for ticker in acoes:
    baixar_acao(ticker)

# Mostra o DataFrame de controle no final
print("\nDataFrame de controle:")
print(controle)