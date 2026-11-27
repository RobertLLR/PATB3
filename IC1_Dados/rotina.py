import yfinance as yf
import pandas as pd
from pathlib import Path #cria e manipula pastas e arquivos

#período
DATA_INICIAL = "2014-01-01"
DATA_FINAL = "2026-01-01"

def verificar_duplicados(dados): #verifica se existem registros duplicados no DataFrame
    duplicados = dados[dados.duplicated(keep=False)].copy()
    return duplicados

def verificar_faltantes(dados): #verifica se existem valores faltantes em qualquer coluna
    faltantes = dados[dados.isna().any(axis=1)].copy()
    return faltantes

def verificar_zeros(dados): #verifica se existem valores zero em colunas que não deveriam ter
    colunas = ["Close", "Adj. Close", "High", "Low", "Open", "Volume"]
    zeros = dados[(dados[colunas] == 0).any(axis=1)].copy()
    return zeros

def verificar_negativos(dados): #verifica valores negativos nos preços e volume de negociação
    colunas = ["Close", "Adj. Close", "High", "Low", "Open", "Volume"]
    negativos = dados[(dados[colunas] < 0).any(axis=1)].copy()
    return negativos

def verificar_precos(dados): #verifica inconsistências nos preços, como preços inconsistentes entre abertura e fechamento
    inconsistentes = dados[
                        (dados["High"] < dados["Low"]) | 
                        (dados["Open"] > dados["High"]) |
                        (dados["Open"] < dados["Low"]) |
                        (dados["Close"] > dados["High"]) |
                        (dados["Close"] < dados["Low"])].copy()
    return inconsistentes

def verificar_variacoes(dados, limite=20): #verifica variações percentuais elevadas (parametro inicial)
    variacoes = dados.copy() #calcula a variação entre os fechamentos
    variacoes["Variacao (%)"] = (variacoes["Close"].pct_change() * 100
    )
    atipicas = variacoes[variacoes["Variacao (%)"].notna() & (variacoes["Variacao (%)"].abs() > limite)].copy()

    return atipicas

def verificar_volume(dados): #verifica inconsistências no volume de negociação, como volumes atípicos
    volume = dados.copy()

    #calcula a média móvel de 20 dias do volume
    volume["Media Volume"] = (volume["Volume"].shift(1).rolling(window=20).median()
    )
    #identifica volumes superiores ao histórico
    volume_atipico = volume[(volume["Volume"] > volume["Media Volume"] * 5) & 
                            (volume["Media Volume"].notna())].copy()

    return volume_atipico

def verificar_periodo(dados): #verifica o período de coleta de dados disponivel
    if dados.empty:
        return {"data_inicial": None, "data_final": None, "registros": 0}

    return {
        "data_inicial": str(dados["Date"].min()),
        "data_final": str(dados["Date"].max()),
        "registros": len(dados)}

# DataFrame
controle = pd.DataFrame(columns=["nome", "data_inicial", "data_final"])

#pasta dos relatórios
pasta_relatorios = Path(__file__).resolve().parent / "relatorios"
pasta_relatorios.mkdir(parents=True, exist_ok=True)

arquivo_relatorio = pasta_relatorios / "relatorio_coleta.txt"
arquivo_relatorio.write_text(f"Relatório de coleta de dados - {pd.Timestamp.now()}\n\n", encoding="utf-8")

arquivo_validacao = pasta_relatorios / "relatorio_validacao.txt"
arquivo_validacao.write_text(f"Relatório de validação de dados - {pd.Timestamp.now()}\n\n", encoding="utf-8")

def executar_validacoes(dados, ticker): #executa todas as validações e registra os resultados no arquivo de validação

    resultados = {
        "duplicados": verificar_duplicados(dados),
        "faltantes": verificar_faltantes(dados),
        "zeros": verificar_zeros(dados),
        "negativos": verificar_negativos(dados),
        "precos": verificar_precos(dados),
        "variacoes": verificar_variacoes(dados),
        "volume": verificar_volume(dados)
    }
    with open(arquivo_validacao, "a", encoding="utf-8") as arquivo:

        arquivo.write(f"Validações para {ticker}:\n")

        periodo = verificar_periodo(dados) #cobertura histórico de coleta de dados

        arquivo.write(f"Cobertura histórica de {ticker}:\n")
        arquivo.write(f"Data inicial: {periodo['data_inicial']}\n")
        arquivo.write(f"Data final: {periodo['data_final']}\n")
        arquivo.write(f"Registros: {periodo['registros']}\n")

        for nome, resultado in resultados.items():
            arquivo.write(f"\n{nome}: {len(resultado)} ocorrência(s)\n")

            if not resultado.empty:
                arquivo.write(f"{resultado.to_string(index=False)}\n")
            else:
                arquivo.write("Nenhuma ocorrência encontrada.\n")
        arquivo.write("\n")

def registrar_relatorio(mensagem):
    with open(arquivo_relatorio, "a", encoding="utf-8") as arquivo:
        arquivo.write(mensagem + "\n")

def baixar_acao(ticker):
   global controle
   print(f"Baixando dados de {ticker}...")
   try:
        dados = yf.download(
            ticker,
            start=DATA_INICIAL,
            end=DATA_FINAL,
            progress=False,
            auto_adjust=False,
            actions=True #pede ao yfinance para incluir dividendos e splits no DataFrame
        )

        if dados.empty:
            mensagem = f"Erro: não encontrou dados para {ticker}"
            print(mensagem)
            registrar_relatorio(mensagem)
            return None

        # corrige as colunas do yfinance
        if isinstance(dados.columns, pd.MultiIndex):
            dados.columns = dados.columns.get_level_values(0)

        # renomeia a coluna "Adj Close" para "Adj. Close"
        dados = dados.rename(columns={"Adj Close": "Adj. Close"})
        # transforma a data em uma coluna
        dados = dados.reset_index()
        # deixa somente a data, sem 00:00:00
        dados["Date"] = dados["Date"].dt.date
        # organiza as colunas
        dados = dados[["Date", "Close", "Adj. Close", "High", "Low","Open", "Volume", "Dividends", "Stock Splits"]]
        # executa as validações e registra os resultados no arquivo de validação
        executar_validacoes(dados, ticker)  
        # cria a pasta "acoes" se não existir
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

        caminho_excel = pasta_excel / f"{ticker.replace('.', '_')}.xlsx"
        dados.to_excel(
            caminho_excel,
            index=False,
            engine="openpyxl"
        )

        # Cria arquivos separados para os eventos de dividendos e splits
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

        caminho_eventos_excel = pasta_excel / f"{ticker.replace('.', '_')}_eventos.xlsx"
        eventos.to_excel(
            caminho_eventos_excel,
            index=False,
            engine="openpyxl"
        )

        # Registra o período de coleta no DataFrame de controle
        data_inicial = str(dados["Date"].min())
        data_final = str(dados["Date"].max())

        nova_linha = pd.DataFrame({
            "nome": [ticker],
            "data_inicial": [data_inicial],
            "data_final": [data_final]
        })

        controle = pd.concat([controle, nova_linha], ignore_index=True)

        mensagem = (
            f"Dados de {ticker} baixados com sucesso!\n"
            f"Período: {data_inicial} até {data_final}\n"
            f"Registros: {len(dados)}\n"
            f"Arquivo CSV: {caminho.name}\n"
            f"Arquivo Excel: {caminho_excel.name}\n"
        )
        registrar_relatorio(mensagem)
        print(f"Dados de {ticker} baixados com sucesso!")
        print(f"Período: {data_inicial} até {data_final}")
        print("-" * 40)

        return dados

    # Registra falhas durante o download ou processamento
   except Exception as erro:
        mensagem = f"Falha ao baixar dados de {ticker}: {erro}"
        print(mensagem)
        registrar_relatorio(mensagem)
        return None

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

for ticker in acoes: # baixa todas as ações da lista automaticamente
    baixar_acao(ticker)

print("\nDataFrame de controle:") # mostra o DataFrame de controle no final
print(controle)