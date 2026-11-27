# PROJETO PAIC - ANÁLISE TÉCNICA DA BBAS3

import os

# Limpa as informações da execução anterior do terminal.
os.system("cls")

# Importa as bibliotecas que serão utilizadas
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import talib

from indicadores.indicadores import (
    media_movel_simples,
    media_movel_exponencial,
    indice_forca_relativa,
    bandas_de_bollinger
)

# 1. OBTENÇÃO DOS DADOS
# LEITURA DOS DADOS EM DATAFRAME
# Lê o arquivo CSV utilizando o pandas.
dados = pd.read_csv(
    "BBAS3_2024_2025.csv",
    parse_dates=["Date"],
    index_col="Date"
)

fechamento = dados["Close"]

# Mostra as primeiras linhas.
print("\nPrimeiras linhas do arquivo:")
print(dados.head())

# Mostra a quantidade de pregões encontrados.
print("\nQuantidade de pregões:", len(dados))

# Mostra a primeira e a última data disponível.
print("Primeira data:", dados.index.min().strftime("%d/%m/%Y"))
print("Última data:", dados.index.max().strftime("%d/%m/%Y"))

# Mostra os cinco primeiros preços de fechamento.
print("\nPrimeiros preços de fechamento:")
print(fechamento.head())

# CÁLCULO DA MÉDIA MÓVEL SIMPLES (MMS)
# CÁLCULO DA MÉDIA MÓVEL EXPONENCIAL (MME) 

# Calcula a MMS de 12 períodos utilizando o pandas.
mms_pandas = fechamento.rolling(window=12).mean()

# Calcula a MME de 12 períodos utilizando o pandas.
mme_pandas = fechamento.ewm(span=12, adjust=False).mean()

# Calcula a MMS de 12 períodos utilizando nossa função manual.
mms_manual = media_movel_simples(fechamento, 12)

# Calcula a MME de 12 períodos utilizando nossa função manual.
mme_manual = media_movel_exponencial(fechamento, 12)

# CÁLCULO DO RSI (14 PERÍODOS)
# Define o período utilizado no cálculo do RSI.
periodo_rsi = 14
# Calcula o RSI utilizando a biblioteca TA-Lib.
rsi = talib.RSI(
    fechamento.to_numpy(dtype=float),
    timeperiod=periodo_rsi
)
# Converte o resultado para uma Series do pandas.
rsi = pd.Series(
    rsi,
    index=fechamento.index
)

# Calcula o RSI utilizando a função manual de indicadores.py.
rsi_manual = indice_forca_relativa(fechamento, periodo_rsi)

# ============================================================
# CÁLCULO DAS BANDAS DE BOLLINGER (20 PERÍODOS)
# ============================================================

# Define os parâmetros das Bandas de Bollinger.
periodo_bollinger = 20
desvios_bollinger = 2

# Calcula as bandas utilizando a TA-Lib.
banda_superior_talib, banda_central_talib, banda_inferior_talib = talib.BBANDS(
    fechamento.to_numpy(dtype=float),
    timeperiod=periodo_bollinger,
    nbdevup=desvios_bollinger,
    nbdevdn=desvios_bollinger,
    matype=0
)

# Converte os resultados para Series do pandas.
banda_superior_talib = pd.Series(
    banda_superior_talib,
    index=fechamento.index
)

banda_central_talib = pd.Series(
    banda_central_talib,
    index=fechamento.index
)

banda_inferior_talib = pd.Series(
    banda_inferior_talib,
    index=fechamento.index
)

# Calcula as Bandas de Bollinger utilizando a função manual.
banda_superior_manual, banda_central_manual, banda_inferior_manual = bandas_de_bollinger(
    fechamento,
    periodo_bollinger,
    desvios_bollinger
)

# ============================================================
# VERIFICAÇÃO DOS RESULTADOS
# ============================================================

# Compara os resultados do pandas com os cálculos manuais.
# Compara os resultados considerando pequenas diferenças numéricas.
print(
    "MMS:",
    mms_pandas.equals(mms_manual)
    or (mms_pandas - mms_manual).abs().max() < 1e-10
)

print(
    "MME:",
    mme_pandas.equals(mme_manual)
    or (mme_pandas - mme_manual).abs().max() < 1e-10
)

# QUANTIFICAÇÃO DAS DIFERENÇAS

# Calcula a diferença absoluta entre os resultados da MMS.
diferenca_mms = (mms_pandas - mms_manual).abs()

# Calcula a diferença absoluta entre os resultados da MME.
diferenca_mme = (mme_pandas - mme_manual).abs()

# Mostra a maior diferença encontrada em cada indicador.
print("\nQuantificação das diferenças:")
print("Maior diferença na MMS:", diferenca_mms.max())
print("Maior diferença na MME:", diferenca_mme.max())

# Conta quantos resultados apresentam diferenças acima da tolerância.
tolerancia = 1e-10

print(
    "Quantidade de diferenças na MMS:",
    (diferenca_mms > tolerancia).sum()
)

print(
    "Quantidade de diferenças na MME:",
    (diferenca_mme > tolerancia).sum()
)

# =======================
# VERIFICAÇÃO DO RSI
# =======================

# Compara o RSI calculado manualmente com o resultado da TA-Lib.
diferenca_rsi = (rsi - rsi_manual).abs()

print("\nVerificação dos cálculos do RSI:")
print(
    "RSI:",
    diferenca_rsi.dropna().max() < tolerancia
)

# Quantifica as diferenças entre os resultados.
print("\nQuantificação das diferenças do RSI:")
print("Maior diferença no RSI:", diferenca_rsi.max())

print(
    "Quantidade de diferenças no RSI:",
    (diferenca_rsi > tolerancia).sum()
)

# ============================================================
# VERIFICAÇÃO DAS BANDAS DE BOLLINGER
# ============================================================

# Calcula as diferenças entre os resultados da TA-Lib e os manuais.
diferenca_superior = (
    banda_superior_talib - banda_superior_manual
).abs()

diferenca_central = (
    banda_central_talib - banda_central_manual
).abs()

diferenca_inferior = (
    banda_inferior_talib - banda_inferior_manual
).abs()

# Verifica se os resultados são equivalentes.
print("\nVerificação das Bandas de Bollinger:")

print(
    "Banda superior:",
    diferenca_superior.dropna().max() < tolerancia
)

print(
    "Banda central:",
    diferenca_central.dropna().max() < tolerancia
)

print(
    "Banda inferior:",
    diferenca_inferior.dropna().max() < tolerancia
)

# Quantifica as diferenças encontradas.
print("\nQuantificação das diferenças das Bandas de Bollinger:")

print("Maior diferença na banda superior:", diferenca_superior.max())
print("Maior diferença na banda central:", diferenca_central.max())
print("Maior diferença na banda inferior:", diferenca_inferior.max())

print(
    "Quantidade de diferenças na banda superior:",
    (diferenca_superior > tolerancia).sum()
)

print(
    "Quantidade de diferenças na banda central:",
    (diferenca_central > tolerancia).sum()
)

print(
    "Quantidade de diferenças na banda inferior:",
    (diferenca_inferior > tolerancia).sum()
)

# ============================================================
# ARQUIVO DE SAÍDA DOS INDICADORES
# ============================================================

# Organiza os resultados manuais e os resultados das bibliotecas.
resultados = pd.DataFrame({

    "Fechamento": fechamento,

    # Média Móvel Simples.
    "MMS Manual": mms_manual,
    "MMS Pandas": mms_pandas,
    "Diferença Absoluta MMS": (mms_manual - mms_pandas).abs(),

    # Média Móvel Exponencial.
    "MME Manual": mme_manual,
    "MME Pandas": mme_pandas,
    "Diferença Absoluta MME": (mme_manual - mme_pandas).abs(),

    # Índice de Força Relativa.
    "RSI Manual": rsi_manual,
    "RSI TA-Lib": rsi,
    "Diferença Absoluta RSI": (rsi_manual - rsi).abs(),

    # Bandas de Bollinger.
    "Banda Superior Manual": banda_superior_manual,
    "Banda Superior TA-Lib": banda_superior_talib,
    "Diferença Absoluta Superior": (
        banda_superior_manual - banda_superior_talib
    ).abs(),

    "Banda Central Manual": banda_central_manual,
    "Banda Central TA-Lib": banda_central_talib,
    "Diferença Absoluta Central": (
        banda_central_manual - banda_central_talib
    ).abs(),

    "Banda Inferior Manual": banda_inferior_manual,
    "Banda Inferior TA-Lib": banda_inferior_talib,
    "Diferença Absoluta Inferior": (
        banda_inferior_manual - banda_inferior_talib
    ).abs()

})

# Seleciona somente os resultados referentes ao ano de 2025.
resultados_2025 = resultados[
    resultados.index.year == 2025
]

# Gera o arquivo CSV.
resultados_2025.to_csv(
    "BBAS3_comparacao_indicadores.csv",
    index_label="Data"
)

# Gera o arquivo Excel.
resultados_2025.to_excel(
    "BBAS3_comparacao_indicadores.xlsx",
    index_label="Data"
)

print("\nArquivos de comparação gerados com sucesso!")
print("Quantidade de registros:", len(resultados_2025))
print("Primeira data:", resultados_2025.index.min().strftime("%d/%m/%Y"))
print("Última data:", resultados_2025.index.max().strftime("%d/%m/%Y"))

# ============================================================
# GRÁFICO DOS PREÇOS, MÉDIAS MÓVEIS, RSI E BANDAS DE BOLLINGER
# ============================================================

# Seleciona somente os dados de 2025 para exibir nos gráficos.
# Os cálculos continuam usando o histórico de 2024 e 2025.
# Seleciona os resultados manuais dos indicadores referentes a 2025.
fechamento_2025 = fechamento[fechamento.index.year == 2025]

mms_2025 = mms_manual[mms_manual.index.year == 2025]
mme_2025 = mme_manual[mme_manual.index.year == 2025]

rsi_2025 = rsi_manual[rsi_manual.index.year == 2025]

banda_superior_2025 = banda_superior_manual[
    banda_superior_manual.index.year == 2025
]

banda_central_2025 = banda_central_manual[
    banda_central_manual.index.year == 2025
]

banda_inferior_2025 = banda_inferior_manual[
    banda_inferior_manual.index.year == 2025
]

# Cria uma figura com dois painéis.
fig, (ax1, ax2) = plt.subplots(
    2, 1,
    figsize=(14, 9),
    sharex=True,
    gridspec_kw={"height_ratios": [2, 1]}
)

# ------------------------------------------------------------
# PAINEL SUPERIOR: PREÇO DE FECHAMENTO E MÉDIAS MÓVEIS
# ------------------------------------------------------------

ax1.plot(
    fechamento_2025.index,
    fechamento_2025,
    label="BBAS3 - Fechamento"
)

ax1.plot(
    mms_2025.index,
    mms_2025,
    label="MMS - 12 períodos"
)

ax1.plot(
    mme_2025.index,
    mme_2025,
    label="MME - 12 períodos"
)

# Adiciona as Bandas de Bollinger ao gráfico.
ax1.plot(
    banda_superior_2025.index,
    banda_superior_2025,
    label="Banda Superior - Bollinger"
)

ax1.plot(
    banda_central_2025.index,
    banda_central_2025,
    label="Banda Central - Bollinger"
)

ax1.plot(
    banda_inferior_2025.index,
    banda_inferior_2025,
    label="Banda Inferior - Bollinger"
)

ax1.set_title("BBAS3 - Preços, Médias Móveis, Bandas de Bollinger e RSI (2025)")
ax1.set_ylabel("Preço (R$)")
ax1.legend()
ax1.grid(True)

# ------------------------------------------------------------
# PAINEL INFERIOR: ÍNDICE DE FORÇA RELATIVA (RSI)
# ------------------------------------------------------------

ax2.plot(
    rsi_2025.index,
    rsi_2025,
    label="RSI - 14 períodos"
)

# Adiciona os níveis de referência do RSI.
ax2.axhline(
    70,
    linestyle="--",
    label="Sobrecompra (70)"
)

ax2.axhline(
    30,
    linestyle="--",
    label="Sobrevenda (30)"
)

# Define a escala padrão do RSI.
ax2.set_ylim(0, 100)
ax2.set_ylabel("RSI")
ax2.set_xlabel("Data")
ax2.legend()
ax2.grid(True)

# Formata o eixo horizontal para mostrar mês e ano.
# Mostra datas próximas ao início e ao meio de cada mês.
ax2.xaxis.set_major_locator(
    mdates.MonthLocator(bymonthday=[1, 15])
)

# Formata as datas para mostrar dia e mês.
ax2.xaxis.set_major_formatter(
    mdates.DateFormatter("%d/%m")
)

# Inclina os rótulos para facilitar a leitura.
plt.xticks(rotation=45)

# Ajusta o espaço da figura.
plt.tight_layout()

# Exibe os dois painéis na mesma figura.
plt.show()


# ============================================================
# GRÁFICOS DAS DIFERENÇAS ABSOLUTAS DOS INDICADORES
# ============================================================

# Calcula as diferenças absolutas entre os resultados
# manuais e os resultados das bibliotecas.

diferenca_mms = (mms_manual - mms_pandas).abs()
diferenca_mme = (mme_manual - mme_pandas).abs()
diferenca_rsi = (rsi_manual - rsi).abs()

diferenca_banda_superior = (
    banda_superior_manual - banda_superior_talib
).abs()

diferenca_banda_central = (
    banda_central_manual - banda_central_talib
).abs()

diferenca_banda_inferior = (
    banda_inferior_manual - banda_inferior_talib
).abs()


# Seleciona somente os resultados referentes ao ano de 2025.
diferencas_2025 = [
    diferenca_mms[diferenca_mms.index.year == 2025],
    diferenca_mme[diferenca_mme.index.year == 2025],
    diferenca_rsi[diferenca_rsi.index.year == 2025],
    diferenca_banda_superior[
        diferenca_banda_superior.index.year == 2025
    ],
    diferenca_banda_central[
        diferenca_banda_central.index.year == 2025
    ],
    diferenca_banda_inferior[
        diferenca_banda_inferior.index.year == 2025
    ]
]

# Define os títulos dos gráficos.
titulos = [
    "Diferença Absoluta - MMS",
    "Diferença Absoluta - MME",
    "Diferença Absoluta - RSI",
    "Diferença Absoluta - Banda Superior",
    "Diferença Absoluta - Banda Central",
    "Diferença Absoluta - Banda Inferior"
]

# Cria uma figura com seis gráficos.
fig, eixos = plt.subplots(
    3, 2,
    figsize=(18, 13),
    sharex=True
)

# Percorre os gráficos e apresenta as diferenças.
for i, ax in enumerate(eixos.flat):

    ax.plot(
        diferencas_2025[i].index,
        diferencas_2025[i],
        label="Diferença absoluta"
    )

    # Adiciona a linha de referência em zero.
    ax.axhline(
        0,
        linestyle="--",
        color="red",
        label="Diferença zero"
    )

    # Define o título e os nomes dos eixos.
    ax.set_title(
        titulos[i],
        fontsize=11,
        pad=10
    )

    ax.set_ylabel("Diferença absoluta", fontsize=9)

    # Apresenta os valores em notação científica.
    ax.ticklabel_format(
        axis="y",
        style="sci",
        scilimits=(0, 0)
    )

    # Formata as datas para mostrar somente um rótulo por mês.
    ax.xaxis.set_major_locator(
        mdates.MonthLocator(interval=1)
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%m/%Y")
    )

    # Limita o período ao ano de 2025.
    ax.set_xlim(
        pd.Timestamp("2025-01-01"),
        pd.Timestamp("2025-12-31")
    )

    # Ajusta o tamanho dos elementos.
    ax.tick_params(axis="both", labelsize=8)

    ax.legend(fontsize=8)
    ax.grid(True)

# Ajusta a escala quando todas as diferenças são zero.
if diferencas_2025[i].max() == 0:
    ax.set_ylim(-1e-15, 1e-15)

# Define o título geral da figura.
fig.suptitle(
    "BBAS3 - Diferenças Absolutas dos Indicadores (2025)",
    fontsize=15,
    y=0.98
)

# Define o nome do eixo horizontal nos gráficos inferiores.
eixos[2, 0].set_xlabel("Data")
eixos[2, 1].set_xlabel("Data")

# Organiza os espaços entre os gráficos.
fig.subplots_adjust(
    left=0.08,
    right=0.98,
    bottom=0.09,
    top=0.91,
    hspace=0.45,
    wspace=0.25
)

# Exibe todos os gráficos em uma única janela.
plt.show()
