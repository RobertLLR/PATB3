import pandas as pd


# ============================================================
# FUNÇÃO MANUAL DA MÉDIA MÓVEL SIMPLES (MMS)
# ============================================================

#AQUI ESTA APENAS OS CALCULOS MANUAIS

def media_movel_simples(fechamento, periodo):

    # Cria uma Series para armazenar os resultados,
    # preservando o índice original dos dados.
    mms = pd.Series(float("nan"), index=fechamento.index)

    # Percorre os preços a partir do primeiro período completo.
    for i in range(periodo - 1, len(fechamento)):

        # Inicializa a soma dos preços do período.
        soma = 0.0

        # Soma manualmente os preços de fechamento.
        for j in range(periodo):
            soma += fechamento.iloc[i - j]

        # Calcula a média aritmética do período.
        mms.iloc[i] = soma / periodo

    return mms


# ============================================================
# FUNÇÃO MANUAL DA MÉDIA MÓVEL EXPONENCIAL (MME)
# ============================================================

def media_movel_exponencial(fechamento, periodo):

    # Cria uma Series para armazenar os resultados.
    mme = pd.Series(float("nan"), index=fechamento.index)

    # Evita tentar acessar um preço se a série estiver vazia.
    if len(fechamento) == 0:
        return mme

    # Calcula o fator de suavização.
    alpha = 2 / (periodo + 1)

    # Utiliza o primeiro preço como valor inicial da MME.
    mme.iloc[0] = fechamento.iloc[0]

    # Calcula manualmente os demais valores.
    for i in range(1, len(fechamento)):

        # Aplica a fórmula recursiva da MME.
        mme.iloc[i] = (
            (1 - alpha) * mme.iloc[i - 1]
            + alpha * fechamento.iloc[i]
        )

    return mme


# ============================================================
# FUNÇÃO MANUAL DO ÍNDICE DE FORÇA RELATIVA (RSI)
# ============================================================

def indice_forca_relativa(fechamento, periodo=14):

    # Cria uma série para armazenar os resultados do RSI.
    rsi = pd.Series(float("nan"), index=fechamento.index)

    # Não calcula o RSI se não houver dados suficientes.
    if len(fechamento) <= periodo:
        return rsi

    # Calcula manualmente as variações entre os fechamentos.
    variacoes = fechamento.diff()

    # Separa os ganhos e as perdas.
    ganhos = variacoes.clip(lower=0)
    perdas = -variacoes.clip(upper=0)

    # Calcula os ganhos e as perdas médios iniciais.
    ganho_medio = ganhos.iloc[1:periodo + 1].mean()
    perda_media = perdas.iloc[1:periodo + 1].mean()

    # Calcula o primeiro RSI considerando os casos especiais.
    if ganho_medio == 0 and perda_media == 0:
        rsi.iloc[periodo] = 50.0

    elif perda_media == 0:
        rsi.iloc[periodo] = 100.0

    elif ganho_medio == 0:
        rsi.iloc[periodo] = 0.0

    else:
        forca_relativa = ganho_medio / perda_media
        rsi.iloc[periodo] = 100 - (100 / (1 + forca_relativa))

    # Atualiza as médias usando a suavização de Wilder.
    for i in range(periodo + 1, len(fechamento)):

        ganho_medio = (
            ganho_medio * (periodo - 1) + ganhos.iloc[i]
        ) / periodo

        perda_media = (
            perda_media * (periodo - 1) + perdas.iloc[i]
        ) / periodo

        # Calcula o RSI considerando os casos especiais.
        if ganho_medio == 0 and perda_media == 0:
            rsi.iloc[i] = 50.0

        elif perda_media == 0:
            rsi.iloc[i] = 100.0

        elif ganho_medio == 0:
            rsi.iloc[i] = 0.0

        else:
            forca_relativa = ganho_medio / perda_media
            rsi.iloc[i] = 100 - (100 / (1 + forca_relativa))

    return rsi

# ============================================================
# FUNÇÃO MANUAL DAS BANDAS DE BOLLINGER
# ============================================================

def bandas_de_bollinger(fechamento, periodo=20, desvios=2):

    # Calcula a média móvel simples (banda central).
    banda_central = fechamento.rolling(
        window=periodo
    ).mean()

    # Calcula o desvio-padrão dos preços de fechamento.
    desvio_padrao = fechamento.rolling(
        window=periodo
    ).std(ddof=0)

    # Calcula a banda superior.
    banda_superior = banda_central + (desvios * desvio_padrao)

    # Calcula a banda inferior.
    banda_inferior = banda_central - (desvios * desvio_padrao)

    return banda_superior, banda_central, banda_inferior