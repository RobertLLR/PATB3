import pandas as pd


def gerar_backtesting(caminho_csv, capital_inicial=10000.0, data_inicio=None, data_fim=None):
    dados = pd.read_csv(caminho_csv)
    dados.columns = dados.columns.str.strip()

    if dados.iloc[0].astype(str).str.contains(r'\.SA').any():
        dados = dados.iloc[1:].reset_index(drop=True)

    dados['Date'] = pd.to_datetime(dados['Date'])

    if data_inicio:
        dados = dados[dados['Date'] >= pd.to_datetime(data_inicio)]

    if data_fim:
        dados = dados[dados['Date'] <= pd.to_datetime(data_fim)]

    dados = dados.reset_index(drop=True)

    if dados.empty:
        return dados, pd.DataFrame(), 'Nenhum dado encontrado para o período selecionado'

    if 'Volume' in dados.columns:
        if dados['Volume'].dtype == 'object':
            dados['Volume'] = (
                dados['Volume']
                .astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
        dados['Volume'] = pd.to_numeric(dados['Volume'], errors='coerce')

    for col in ['High', 'Low', 'Open', 'Close']:
        if col in dados.columns and dados[col].dtype == 'object':
            dados[col] = (
                dados[col]
                .astype(str)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            dados[col] = pd.to_numeric(dados[col], errors='coerce')

    data_inicial = dados['Date'].min()
    data_final = dados['Date'].max()
    indice_maiorp = dados['High'].idxmax()
    indice_menorp = dados['Low'].idxmin()
    preco_inicial = dados['Open'].iloc[0]
    preco_final = dados['Close'].iloc[-1]
    volume_medio = dados['Volume'].mean()
    indice_volume_max = dados['Volume'].idxmax()

    operacoes_lista = []
    saldo_atual = capital_inicial

    posicao_aberta = False
    preco_compra = 0
    data_compra = None
    qtd_acoes = 0
    dados['executed_signal'] = 0

    # Lista para registar o capital dia a dia
    capital_diario = []

    for i, row in dados.iterrows():
        sinal = row['signal']
        preco = row['Close']
        data = row['Date']

        # 1. Se não estamos posicionados e o sinal for COMPRA (1)
        if not posicao_aberta and sinal == 1:
            qtd_teorica = saldo_atual / preco if preco > 0 else 0
            qtd_acoes = int(qtd_teorica // 100) * 100

            if qtd_acoes > 0:
                custo_compra = qtd_acoes * preco
                saldo_atual -= custo_compra
                preco_compra = preco
                data_compra = data
                posicao_aberta = True
                dados.at[i, 'executed_signal'] = 1

        # 2. Se JÁ ESTAMOS posicionados e o sinal for VENDA (-1)
        elif posicao_aberta and sinal == -1:
            valor_venda = qtd_acoes * preco
            retorno_pct = (preco - preco_compra) / preco_compra
            resultado_reais = valor_venda - (qtd_acoes * preco_compra)
            saldo_atual = saldo_atual + valor_venda

            operacoes_lista.append([
                data_compra,
                preco_compra,
                data,
                preco,
                retorno_pct,
                qtd_acoes,
                resultado_reais,
                saldo_atual
            ])

            posicao_aberta = False
            dados.at[i, 'executed_signal'] = -1

        # Calcular o patrimônio total no dia (Dinheiro em caixa + valor das ações se posicionado)
        patrimonio_dia = saldo_atual + \
            (qtd_acoes * preco if posicao_aberta else 0)
        capital_diario.append(patrimonio_dia)

    dados['capital'] = capital_diario

    operacoes = pd.DataFrame(
        operacoes_lista,
        columns=[
            'Data de compra',
            'Compra',
            'Data de venda',
            'Venda',
            'Retorno (%)',
            'Quantidade',
            'Resultado (R$)',
            'Saldo Acumulado (R$)'
        ]
    )

    if not operacoes.empty:
        operacoes['Data de compra'] = operacoes['Data de compra'].dt.strftime(
            '%Y-%m-%d')
        operacoes['Data de venda'] = operacoes['Data de venda'].dt.strftime(
            '%Y-%m-%d')
        operacoes['Compra'] = operacoes['Compra'].apply(
            lambda x: f'R$ {x:.2f}')
        operacoes['Venda'] = operacoes['Venda'].apply(
            lambda x: f'R$ {x:.2f}')
        operacoes['Quantidade'] = operacoes['Quantidade'].apply(
            lambda x: f'{int(x):,}'.replace(',', '.'))
        operacoes['Retorno (%)'] = operacoes['Retorno (%)'].apply(
            lambda x: f'{x * 100:.2f}%')
        operacoes['Resultado (R$)'] = operacoes['Resultado (R$)'].apply(
            lambda x: f'R$ {x:,.2f}')
        operacoes['Saldo Acumulado (R$)'] = operacoes['Saldo Acumulado (R$)'].apply(
            lambda x: f'R$ {x:,.2f}')

    relatorio = f"""
Período: {data_inicial.date()} até {data_final.date()}
Registros: {len(dados)}

---------------- PREÇOS -------------------
Preço inicial: R$ {preco_inicial:.2f}
Preço final:   R$ {preco_final:.2f}
Maior preço:   R$ {dados.loc[indice_maiorp, 'High']:.2f} em {dados.loc[indice_maiorp, 'Date'].date()}
Menor preço:   R$ {dados.loc[indice_menorp, 'Low']:.2f} em {dados.loc[indice_menorp, 'Date'].date()}

---------------- VOLUME -------------------
Volume médio diário: {volume_medio:,.0f} ações
Volume máximo: {dados.loc[indice_volume_max, 'Volume']:,} em {dados.loc[indice_volume_max, 'Date'].date()}
"""

    return dados, operacoes, relatorio
