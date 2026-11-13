import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
from backtesting import gerar_backtesting
from database import salvar_simulacao_db
import pandas as pd
import os

# Mapeamento dos arquivos CSV de cada ativo
ARQUIVOS_ATIVOS = {
    'BBAS3': 'BBAS3_2025.csv',
    'ITUB4': 'ITUB4_2025.csv'
}

# Função auxiliar para ler as datas limite de cada ativo


def obter_limites_datas(caminho_csv):
    if os.path.exists(caminho_csv):
        df = pd.read_csv(caminho_csv)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            min_date = df['Date'].min().strftime('%Y-%m-%d')
            max_date = df['Date'].max().strftime('%Y-%m-%d')
            return min_date, max_date
    return None, None


app = Dash(__name__, suppress_callback_exceptions=True)

# Figura vazia padrão para quando a simulação não estiver ativa
FIGURA_VAZIA = go.Figure()
FIGURA_VAZIA.update_layout(
    xaxis={'visible': False},
    yaxis={'visible': False},
    annotations=[{
        'text': 'Preencha os parâmetros e clique em "Simular"',
        'xref': 'paper',
        'yref': 'paper',
        'showarrow': False,
        'font': {'size': 14, 'color': 'gray'}
    }]
)

# Estilo para os botões de tela cheia
ESTILO_BTN_FULLSCREEN = {
    'position': 'absolute',
    'bottom': '2px',
    'right': '5px',
    'zIndex': '20',
    'padding': '2px 6px',
    'fontSize': '11px',
    'cursor': 'pointer',
    'backgroundColor': '#ffffff',
    'border': '1px solid #ccc',
    'borderRadius': '3px',
    'boxShadow': '0 1px 3px rgba(0,0,0,0.1)'
}

# ESTRUTURA DA PÁGINA ÚNICA
app.layout = html.Div([

    # Cabeçalho Compacto
    html.H2('Plataforma de Backtesting', style={
        'textAlign': 'center',
        'margin': '0 0 10px 0',
        'padding': '0',
        'fontSize': '22px'
    }),

    # SEÇÃO SUPERIOR
    html.Div([

        # 1. PARÂMETROS DA SIMULAÇÃO
        html.Div([
            html.H4('Parâmetros', style={
                    'margin': '0 0 8px 0', 'fontSize': '15px'}),

            html.Label('Nome do Investidor:', style={'fontSize': '12px'}),
            dcc.Input(
                id='input_nome',
                type='text',
                value='',
                placeholder='Digite seu nome...',
                style={'width': '100%', 'marginBottom': '8px', 'padding': '4px',
                       'boxSizing': 'border-box', 'fontSize': '12px'}
            ),
            html.Label('Capital Inicial (R$):', style={'fontSize': '12px'}),
            dcc.Input(
                id='input_capital',
                type='number',
                value=10000,
                min=1000,
                step=1000,
                debounce=True,
                style={'width': '100%', 'marginBottom': '8px', 'padding': '4px',
                       'boxSizing': 'border-box', 'fontSize': '12px'}
            ),

            html.Label('Selecione o Ativo:', style={'fontSize': '12px'}),
            dcc.Dropdown(
                id='dropdown_ativo',
                options=[
                    {'label': 'Banco do Brasil (BBAS3)', 'value': 'BBAS3'},
                    {'label': 'Itaú Unibanco (ITUB4)', 'value': 'ITUB4'}
                ],
                value='BBAS3',
                clearable=False,
                style={'marginBottom': '8px', 'fontSize': '12px'}
            ),

            # ESTRATÉGIA / INDICADOR
            html.Label('Estratégia / Indicador:', style={'fontSize': '12px'}),
            dcc.Dropdown(
                id='dropdown_estrategia',
                options=[
                    {'label': 'RSI', 'value': 'RSI'},
                    {'label': 'Média Aritmética', 'value': 'SMA'},
                    {'label': 'Média Exponencial', 'value': 'EMA'}
                ],
                value=None,
                placeholder='Selecione a estratégia...',
                clearable=True,
                style={'marginBottom': '6px', 'fontSize': '12px'}
            ),

            html.Div(id='container_mini_janela_parametro',
                     style={'marginBottom': '8px'}),

            html.Label('Período da Simulação:', style={'fontSize': '12px'}),
            dcc.DatePickerRange(
                id='picker_data',
                start_date_placeholder_text='Início',
                end_date_placeholder_text='Fim',
                display_format='DD/MM/YYYY',
                style={'width': '100%', 'marginBottom': '12px'}
            ),

            # BOTÃO 1: SIMULAR
            html.Button(
                'Simular',
                id='botao_simular',
                n_clicks=0,
                disabled=False,
                style={
                    'width': '100%',
                    'padding': '6px',
                    'cursor': 'pointer',
                    'fontWeight': 'bold',
                    'fontSize': '12px',
                    'marginBottom': '6px'
                }
            ),

            # BOTÃO 2: SALVAR OPERAÇÕES EM CSV
            html.Button('Salvar Simulação (CSV)', id='botao_salvar', n_clicks=0, style={
                'width': '100%',
                'backgroundColor': '#28a745',
                'color': 'white',
                'marginBottom': '10px',
                'padding': '6px',
                'cursor': 'pointer',
                'fontSize': '12px',
                'border': 'none',
                'borderRadius': '3px'
            }),
            dcc.Download(id="download_operacoes_csv"),
            html.Div(id='status_salvar', style={
                     'fontSize': '12px', 'textAlign': 'center', 'marginBottom': '10px'}),

            # BOTÃO 3: ENCERRAR SIMULAÇÃO
            html.Button(
                'Encerrar Simulação',
                id='botao_resetar',
                n_clicks=0,
                style={
                    'width': '100%',
                    'padding': '6px',
                    'cursor': 'pointer',
                    'fontSize': '12px',
                    'backgroundColor': '#f2f2f2'
                }
            )
        ], style={
            'border': '1px solid black',
            'padding': '12px',
            'width': '220px',
            'borderRadius': '5px',
            'boxSizing': 'border-box',
            'backgroundColor': '#fcfcfc',
            'height': '100%',
            'overflowY': 'auto'
        }),

        # 2. RESUMO DO ATIVO
        html.Div([
            html.Div([
                html.Button('Ativo', id='btn_resumo_ativo', n_clicks=0, style={
                    'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer',
                    'backgroundColor': '#e0e0e0', 'border': '1px solid #ccc', 'borderRadius': '3px 0 0 3px', 'flex': '1'
                }),
                html.Button('Operações', id='btn_resumo_operacoes', n_clicks=0, style={
                    'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer',
                    'backgroundColor': '#ffffff', 'border': '1px solid #ccc', 'borderLeft': 'none', 'flex': '1'
                }),
                html.Button('Risco', id='btn_resumo_risco', n_clicks=0, style={
                    'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer',
                    'backgroundColor': '#ffffff', 'border': '1px solid #ccc', 'borderLeft': 'none', 'borderRadius': '0 3px 3px 0', 'flex': '1'
                })
            ], style={'display': 'flex', 'marginBottom': '6px', 'position': 'relative', 'zIndex': '10'}),

            html.Pre(
                id='saida_relatorio_ativo',
                children="",
                style={
                    'whiteSpace': 'pre-wrap',
                    'overflowWrap': 'break-word',
                    'margin': '0',
                    'fontFamily': 'monospace',
                    'fontSize': '11px',
                    'lineHeight': '1.2',
                    'display': 'block'
                }
            ),

            html.Pre(
                id='saida_relatorio_operacoes',
                children="Nenhuma simulação realizada.",
                style={
                    'whiteSpace': 'pre-wrap',
                    'overflowWrap': 'break-word',
                    'margin': '0',
                    'fontFamily': 'monospace',
                    'fontSize': '11px',
                    'lineHeight': '1.2',
                    'display': 'none'
                }
            ),

            html.Pre(
                id='saida_relatorio_risco',
                children="Nenhuma simulação realizada.",
                style={
                    'whiteSpace': 'pre-wrap',
                    'overflowWrap': 'break-word',
                    'margin': '0',
                    'fontFamily': 'monospace',
                    'fontSize': '11px',
                    'lineHeight': '1.2',
                    'display': 'none'
                }
            )
        ], style={
            'border': '1px solid black',
            'padding': '12px',
            'width': '310px',
            'borderRadius': '5px',
            'boxSizing': 'border-box',
            'overflowY': 'auto',
            'backgroundColor': '#fcfcfc'
        }),

        # 3. GRÁFICO (Com alternância visual direta entre os dois gráficos)
        html.Div([
            html.Div([
                html.Button('📈 Preço', id='btn_grafico_preco', n_clicks=0, style={
                    'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer',
                    'backgroundColor': '#e0e0e0', 'border': '1px solid #ccc', 'borderRadius': '3px 0 0 3px'
                }),
                html.Button('💰 Capital', id='btn_grafico_capital', n_clicks=0, style={
                    'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer',
                    'backgroundColor': '#ffffff', 'border': '1px solid #ccc', 'borderLeft': 'none', 'borderRadius': '0 3px 3px 0', 'marginRight': 'auto'
                })
            ], style={'display': 'flex', 'marginBottom': '4px', 'position': 'relative', 'zIndex': '10'}),

            html.Button('⛶ Tela Cheia', id='btn_fullscreen_grafico',
                        n_clicks=0, style=ESTILO_BTN_FULLSCREEN),

            # Gráfico de Preço (Visível por padrão)
            dcc.Graph(
                id='grafico_precos',
                figure=FIGURA_VAZIA,
                style={'height': 'calc(100% - 25px)',
                       'width': '100%', 'display': 'block'},
                config={
                    'responsive': True,
                    'modeBarButtonsToRemove': [
                        'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoescale2d'
                    ]}
            ),

            # Gráfico de Capital (Oculto por padrão)
            dcc.Graph(
                id='grafico_capital',
                figure=FIGURA_VAZIA,
                style={'height': 'calc(100% - 25px)',
                       'width': '100%', 'display': 'none'},
                config={
                    'responsive': True,
                    'modeBarButtonsToRemove': [
                        'lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoescale2d'
                    ]}
            )
        ],
            id='container_grafico',
            style={
            'position': 'relative',
            'flex': '1',
            'border': '1px solid #ccc',
            'borderRadius': '5px',
            'padding': '5px',
            'boxSizing': 'border-box',
            'backgroundColor': '#ffffff'
        })

    ], style={
        'display': 'flex',
        'gap': '12px',
        'alignItems': 'stretch',
        'height': '50vh',
        'marginBottom': '10px'
    }),

    # SEÇÃO INFERIOR: TABELA DE OPERAÇÕES
    html.Div([
        html.Div([
            html.H4('Operações Realizadas', style={
                    'margin': '0', 'fontSize': '14px', 'display': 'inline-block'}),
            html.Button('⛶ Tela Cheia', id='btn_fullscreen_tabela',
                        n_clicks=0, style=ESTILO_BTN_FULLSCREEN)
        ], style={'marginBottom': '5px', 'position': 'relative'}),

        dash_table.DataTable(
            id='tabela_operacoes',
            fixed_rows={'headers': True},
            style_table={
                'maxHeight': 'calc(38vh - 45px)',
                'overflowY': 'auto',
                'overflowX': 'auto',
                'width': '100%'
            },
            style_cell={
                'fontSize': '11px',
                'padding': '6px 8px',
                'textAlign': 'center',
                'minWidth': '100px'
            },
            style_header={
                'fontWeight': 'bold',
                'backgroundColor': '#f0f0f0',
                'fontSize': '12px',
                'borderBottom': '2px solid #ccc'
            }
        )
    ], id='container_tabela', style={
        'position': 'relative',
        'border': '1px solid black',
        'padding': '10px',
        'width': '100%',
        'height': '38vh',
        'boxSizing': 'border-box',
        'borderRadius': '5px',
        'backgroundColor': '#ffffff'
    })

], style={
    'padding': '10px 15px',
    'height': '100vh',
    'maxHeight': '100vh',
    'boxSizing': 'border-box',
    'overflow': 'hidden'
})


# CALLBACK: ATUALIZAR INTERVALO DE DATAS AO MUDAR O ATIVO
@app.callback(
    [
        Output('picker_data', 'min_date_allowed'),
        Output('picker_data', 'max_date_allowed'),
        Output('picker_data', 'start_date'),
        Output('picker_data', 'end_date')
    ],
    Input('dropdown_ativo', 'value')
)
def atualizar_datas_picker(ativo):
    caminho_csv = ARQUIVOS_ATIVOS.get(ativo)
    min_date, max_date = obter_limites_datas(caminho_csv)
    return min_date, max_date, min_date, max_date


# CALLBACK: TELA CHEIA DO GRÁFICO
@app.callback(
    [
        Output('container_grafico', 'style'),
        Output('btn_fullscreen_grafico', 'children')
    ],
    [Input('btn_fullscreen_grafico', 'n_clicks')],
    [State('container_grafico', 'style')],
    prevent_initial_call=True
)
def toggle_fullscreen_grafico(n_clicks, style_atual):
    novo_estilo = style_atual.copy()

    if novo_estilo.get('position') == 'fixed':
        novo_estilo.update({
            'position': 'relative',
            'top': 'auto',
            'left': 'auto',
            'width': 'auto',
            'height': '100%',
            'zIndex': '1'
        })
        return novo_estilo, '⛶ Tela Cheia'
    else:
        novo_estilo.update({
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100vw',
            'height': '100vh',
            'zIndex': '9999'
        })
        return novo_estilo, '✖ Sair da Tela Cheia'


# CALLBACK: TELA CHEIA DA TABELA
@app.callback(
    [
        Output('container_tabela', 'style'),
        Output('tabela_operacoes', 'style_table'),
        Output('btn_fullscreen_tabela', 'children')
    ],
    [Input('btn_fullscreen_tabela', 'n_clicks')],
    [
        State('container_tabela', 'style'),
        State('tabela_operacoes', 'style_table')
    ],
    prevent_initial_call=True
)
def toggle_fullscreen_tabela(n_clicks, style_container, style_tabela):
    novo_container = style_container.copy()
    nova_tabela = style_tabela.copy()

    if novo_container.get('position') == 'fixed':
        novo_container.update({
            'position': 'relative',
            'top': 'auto',
            'left': 'auto',
            'width': '100%',
            'height': '38vh',
            'zIndex': '1'
        })
        nova_tabela['maxHeight'] = 'calc(38vh - 45px)'
        return novo_container, nova_tabela, '⛶ Tela Cheia'
    else:
        novo_container.update({
            'position': 'fixed',
            'top': '0',
            'left': '0',
            'width': '100vw',
            'height': '100vh',
            'zIndex': '9999'
        })
        nova_tabela['maxHeight'] = 'calc(100vh - 65px)'
        return novo_container, nova_tabela, '✖ Sair da Tela Cheia'


# CALLBACK: EXIBIR MINI JANELA DE PARÂMETROS
@app.callback(
    Output('container_mini_janela_parametro', 'children'),
    Input('dropdown_estrategia', 'value')
)
def exibir_mini_janela_parametros(estrategia):
    if estrategia == 'RSI':
        return html.Div([
            html.Label('Parâmetro do RSI:', style={
                       'fontSize': '11px', 'color': '#555'}),
            dcc.Dropdown(
                id='dropdown_parametro_rsi',
                options=[
                    {'label': 'RSI 14', 'value': 14}
                ],
                value=14,
                clearable=False,
                style={'fontSize': '11px'}
            )
        ], style={
            'border': '1px dashed #ccc',
            'padding': '5px',
            'borderRadius': '3px',
            'backgroundColor': '#f9f9f9'
        })
    return []


# CALLBACK GERENCIADOR DA SIMULAÇÃO E BOTÕES
@app.callback(
    [
        Output('saida_relatorio_ativo', 'children'),
        Output('saida_relatorio_operacoes', 'children'),
        Output('saida_relatorio_risco', 'children'),
        Output('grafico_precos', 'figure'),
        Output('grafico_capital', 'figure'),
        Output('tabela_operacoes', 'data'),
        Output('tabela_operacoes', 'columns'),
        Output('botao_simular', 'disabled')
    ],
    [
        Input('botao_simular', 'n_clicks'),
        Input('botao_resetar', 'n_clicks')
    ],
    [
        State('input_nome', 'value'),
        State('input_capital', 'value'),
        State('dropdown_ativo', 'value'),
        State('dropdown_estrategia', 'value'),
        State('dropdown_parametro_rsi', 'value'),
        State('picker_data', 'start_date'),
        State('picker_data', 'end_date')
    ],
    prevent_initial_call=True
)
def gerenciar_simulacao(n_simular, n_resetar, nome, capital, ativo, estrategia, param_rsi, data_inicio, data_fim):
    button_id = ctx.triggered_id

    # AÇÃO DE RESETAR / ENCERRAR SIMULAÇÃO
    if button_id == 'botao_resetar':
        return "", "Nenhuma simulação realizada.", "Nenhuma simulação realizada.", FIGURA_VAZIA, FIGURA_VAZIA, [], [], False

    # AÇÃO SIMULAR
    if button_id == 'botao_simular':
        caminho_csv = ARQUIVOS_ATIVOS[ativo]
        capital_valido = capital if capital and capital >= 1000 else 10000.0
        nome_investidor = nome.strip() if nome and nome.strip() else "Não informado"

        if estrategia == 'RSI':
            estrategia_texto = f"RSI ({param_rsi if param_rsi else 14})"
        elif estrategia == 'SMA':
            estrategia_texto = "Média Aritmética"
        elif estrategia == 'EMA':
            estrategia_texto = "Média Exponencial"
        else:
            estrategia_texto = "Nenhuma selecionada"

        dados, operacoes, relatorio_ativo_texto, info_operacao = gerar_backtesting(
            caminho_csv, capital_inicial=capital_valido, data_inicio=data_inicio, data_fim=data_fim)

        # Cálculo direto dos trades vencedores e perdedores a partir da tabela de operações
        trades_lucro = 0
        trades_prejuizo = 0
        if not operacoes.empty and 'Resultado (R$)' in operacoes.columns:
            resultado_num = (
                operacoes['Resultado (R$)']
                .astype(str)
                .str.replace('R$', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.strip()
            )
            resultado_num = pd.to_numeric(resultado_num, errors='coerce')
            trades_lucro = int((resultado_num > 0).sum())
            trades_prejuizo = int((resultado_num < 0).sum())

        relatorio_ativo_final = f"Investidor: {nome_investidor}\n" + \
            relatorio_ativo_texto

        relatorio_operacoes_final = f"""Investidor: {nome_investidor}
Estratégia: {estrategia_texto}
Capital Inicial: R$ {capital_valido:,.2f}
Capital Final: R$ {info_operacao['capital_final']:,.2f}
Total de Operações: {info_operacao['total_operacoes']}
Trades Vencedores (Lucro): {trades_lucro}
Trades Perdedores (Prejuízo): {trades_prejuizo}

---------------- PERÍODO ----------------
Início: {info_operacao['data_inicio']}
Fim:    {info_operacao['data_fim']}
"""

        relatorio_risco_final = "Nenhuma métrica de risco configurada no momento."

        # Identificação dos índices de compra e venda
        indices_compra = dados.index[dados['executed_signal'] == 1].tolist()
        indices_venda = dados.index[dados['executed_signal'] == -1].tolist()

        # Verifica se há compra após a última venda (posição em aberto no final)
        tem_compra_apos_venda = False
        if len(indices_compra) > 0:
            if len(indices_venda) == 0:
                tem_compra_apos_venda = True
            elif indices_compra[-1] > indices_venda[-1]:
                tem_compra_apos_venda = True

        # 1. Gráfico de Preços
        grafico = go.Figure()

        grafico.add_trace(go.Scatter(
            x=dados['Date'],
            y=dados['Close'],
            mode='lines',
            name='Preço',
            line=dict(width=1.5, color='#1f77b4')
        ))

        # Adicionar compras com círculo roxo apenas se houver compra após a última venda
        if len(indices_compra) > 0:
            if tem_compra_apos_venda:
                indices_compras_normais = indices_compra[:-1]
                indice_ultima_compra = indices_compra[-1]

                if len(indices_compras_normais) > 0:
                    grafico.add_trace(go.Scatter(
                        x=dados.loc[indices_compras_normais, 'Date'],
                        y=dados.loc[indices_compras_normais, 'Close'],
                        mode='markers',
                        name='Compra',
                        marker=dict(symbol='triangle-up',
                                    size=10, color='green')
                    ))

                grafico.add_trace(go.Scatter(
                    x=dados.loc[[indice_ultima_compra], 'Date'],
                    y=dados.loc[[indice_ultima_compra], 'Close'],
                    mode='markers',
                    name='Última Compra',
                    marker=dict(symbol='circle', size=12, color='purple')
                ))
            else:
                grafico.add_trace(go.Scatter(
                    x=dados.loc[indices_compra, 'Date'],
                    y=dados.loc[indices_compra, 'Close'],
                    mode='markers',
                    name='Compra',
                    marker=dict(symbol='triangle-up', size=10, color='green')
                ))

        if len(indices_venda) > 0:
            indices_vendas_normais = indices_venda[:-1]
            indice_ultima_venda = indices_venda[-1]

            if len(indices_vendas_normais) > 0:
                grafico.add_trace(go.Scatter(
                    x=dados.loc[indices_vendas_normais, 'Date'],
                    y=dados.loc[indices_vendas_normais, 'Close'],
                    mode='markers',
                    name='Venda',
                    marker=dict(symbol='triangle-down', size=10, color='red')
                ))

            grafico.add_trace(go.Scatter(
                x=dados.loc[[indice_ultima_venda], 'Date'],
                y=dados.loc[[indice_ultima_venda], 'Close'],
                mode='markers',
                name='Última Venda',
                marker=dict(symbol='triangle-down', size=16, color='red')
            ))

        grafico.update_layout(
            title=dict(
                text=f'Evolução do Preço - {ativo} ({estrategia_texto})',
                font=dict(size=13),
                x=0.01,
                y=0.98,
                xanchor='left',
                yanchor='top'
            ),
            margin=dict(l=10, r=10, t=35, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=0.82
            ),
            xaxis={
                'title': None,
                'rangeselector': {
                    'y': -0.22,
                    'x': 0.0,
                    'xanchor': 'left',
                    'yanchor': 'top',
                    'buttons': [
                        {'count': 1, 'label': '1M', 'step': 'month',
                            'stepmode': 'backward'},
                        {'count': 3, 'label': '3M', 'step': 'month',
                            'stepmode': 'backward'},
                        {'count': 6, 'label': '6M', 'step': 'month',
                            'stepmode': 'backward'},
                        {'count': 1, 'label': '1A', 'step': 'year',
                            'stepmode': 'backward'},
                        {'step': 'all', 'label': 'Tudo'}
                    ]
                }
            },
            yaxis={'title': 'Preço (R$)'}
        )

        # 2. Gráfico de Evolução do Capital
        grafico_capital = go.Figure()

        grafico_capital.add_trace(go.Scatter(
            x=dados['Date'],
            y=dados['capital'],
            mode='lines',
            name='Patrimônio (R$)',
            line=dict(width=2, color='#28a745')
        ))

        if len(indices_compra) > 0:
            if tem_compra_apos_venda:
                indices_compras_normais = indices_compra[:-1]
                indice_ultima_compra = indices_compra[-1]

                if len(indices_compras_normais) > 0:
                    grafico_capital.add_trace(go.Scatter(
                        x=dados.loc[indices_compras_normais, 'Date'],
                        y=dados.loc[indices_compras_normais, 'capital'],
                        mode='markers',
                        name='Compra',
                        marker=dict(symbol='triangle-up',
                                    size=10, color='green')
                    ))

                grafico_capital.add_trace(go.Scatter(
                    x=dados.loc[[indice_ultima_compra], 'Date'],
                    y=dados.loc[[indice_ultima_compra], 'capital'],
                    mode='markers',
                    name='Última Compra',
                    marker=dict(symbol='circle', size=12, color='purple')
                ))
            else:
                grafico_capital.add_trace(go.Scatter(
                    x=dados.loc[indices_compra, 'Date'],
                    y=dados.loc[indices_compra, 'capital'],
                    mode='markers',
                    name='Compra',
                    marker=dict(symbol='triangle-up', size=10, color='green')
                ))

        if len(indices_venda) > 0:
            indices_vendas_normais = indices_venda[:-1]
            indice_ultima_venda = indices_venda[-1]

            if len(indices_vendas_normais) > 0:
                grafico_capital.add_trace(go.Scatter(
                    x=dados.loc[indices_vendas_normais, 'Date'],
                    y=dados.loc[indices_vendas_normais, 'capital'],
                    mode='markers',
                    name='Venda',
                    marker=dict(symbol='triangle-down', size=10, color='red')
                ))

            grafico_capital.add_trace(go.Scatter(
                x=dados.loc[[indice_ultima_venda], 'Date'],
                y=dados.loc[[indice_ultima_venda], 'capital'],
                mode='markers',
                name='Última Venda',
                marker=dict(symbol='triangle-down', size=16, color='red')
            ))

        grafico_capital.update_layout(
            title=dict(text=f'Evolução do Patrimônio - {ativo} ({estrategia_texto})', font=dict(
                size=13), x=0.01, y=0.98, xanchor='left', yanchor='top'),
            margin=dict(l=10, r=10, t=35, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=0.82
            ),
            xaxis={'title': None},
            yaxis={'title': 'Patrimônio (R$)'}
        )

        # 3. Dados da Tabela
        dados_tabela = operacoes.to_dict('records')
        colunas_tabela = [{'name': col, 'id': col}
                          for col in operacoes.columns]

        return relatorio_ativo_final, relatorio_operacoes_final, relatorio_risco_final, grafico, grafico_capital, dados_tabela, colunas_tabela, True

    return "", "Nenhuma simulação realizada.", "Nenhuma simulação realizada.", FIGURA_VAZIA, FIGURA_VAZIA, [], [], False


# CALLBACK: ALTERNAR VISIBILIDADE ENTRE OS GRÁFICOS E ESTILO DOS BOTÕES
@app.callback(
    [
        Output('grafico_precos', 'style'),
        Output('grafico_capital', 'style'),
        Output('btn_grafico_preco', 'style'),
        Output('btn_grafico_capital', 'style')
    ],
    [
        Input('btn_grafico_preco', 'n_clicks'),
        Input('btn_grafico_capital', 'n_clicks')
    ]
)
def alternar_visibilidade_graficos(n_preco, n_capital):
    triggered_id = ctx.triggered_id

    estilo_base_grafico = {'height': 'calc(100% - 25px)', 'width': '100%'}
    estilo_preco_ativo = {'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer',
                          'backgroundColor': '#e0e0e0', 'border': '1px solid #ccc', 'borderRadius': '3px 0 0 3px'}
    estilo_capital_inativo = {'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer', 'backgroundColor': '#ffffff',
                              'border': '1px solid #ccc', 'borderLeft': 'none', 'borderRadius': '0 3px 3px 0', 'marginRight': 'auto'}

    estilo_preco_inativo = {'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer',
                            'backgroundColor': '#ffffff', 'border': '1px solid #ccc', 'borderRadius': '3px 0 0 3px'}
    estilo_capital_ativo = {'padding': '2px 8px', 'fontSize': '11px', 'cursor': 'pointer', 'backgroundColor': '#e0e0e0',
                            'border': '1px solid #ccc', 'borderLeft': 'none', 'borderRadius': '0 3px 3px 0', 'marginRight': 'auto'}

    if triggered_id == 'btn_grafico_capital':
        estilo_preco = {**estilo_base_grafico, 'display': 'none'}
        estilo_capital = {**estilo_base_grafico, 'display': 'block'}
        return estilo_preco, estilo_capital, estilo_preco_inativo, estilo_capital_ativo
    else:
        estilo_preco = {**estilo_base_grafico, 'display': 'block'}
        estilo_capital = {**estilo_base_grafico, 'display': 'none'}
        return estilo_preco, estilo_capital, estilo_preco_ativo, estilo_capital_inativo


# CALLBACK: ALTERNAR VISIBILIDADE ENTRE OS RESUMOS (ATIVO / OPERAÇÕES / RISCO)
@app.callback(
    [
        Output('saida_relatorio_ativo', 'style'),
        Output('saida_relatorio_operacoes', 'style'),
        Output('saida_relatorio_risco', 'style'),
        Output('btn_resumo_ativo', 'style'),
        Output('btn_resumo_operacoes', 'style'),
        Output('btn_resumo_risco', 'style')
    ],
    [
        Input('btn_resumo_ativo', 'n_clicks'),
        Input('btn_resumo_operacoes', 'n_clicks'),
        Input('btn_resumo_risco', 'n_clicks')
    ]
)
def alternar_visibilidade_resumos(n_ativo, n_operacoes, n_risco):
    triggered_id = ctx.triggered_id

    estilo_base_texto = {
        'whiteSpace': 'pre-wrap', 'overflowWrap': 'break-word',
        'margin': '0', 'fontFamily': 'monospace', 'fontSize': '11px', 'lineHeight': '1.2'
    }

    estilo_btn_ativo = {'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer',
                        'backgroundColor': '#e0e0e0', 'border': '1px solid #ccc', 'borderRadius': '3px 0 0 3px', 'flex': '1'}
    estilo_btn_meio = {'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer',
                       'backgroundColor': '#ffffff', 'border': '1px solid #ccc', 'borderLeft': 'none', 'flex': '1'}
    estilo_btn_fim = {'padding': '2px 6px', 'fontSize': '11px', 'cursor': 'pointer', 'backgroundColor': '#ffffff',
                      'border': '1px solid #ccc', 'borderLeft': 'none', 'borderRadius': '0 3px 3px 0', 'flex': '1'}

    if triggered_id == 'btn_resumo_operacoes':
        return (
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_base_texto, 'display': 'block'},
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_btn_meio, 'backgroundColor': '#ffffff'},
            {**estilo_btn_meio, 'backgroundColor': '#e0e0e0'},
            {**estilo_btn_fim, 'backgroundColor': '#ffffff'}
        )
    elif triggered_id == 'btn_resumo_risco':
        return (
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_base_texto, 'display': 'block'},
            {**estilo_btn_ativo, 'backgroundColor': '#ffffff'},
            {**estilo_btn_meio, 'backgroundColor': '#ffffff'},
            {**estilo_btn_fim, 'backgroundColor': '#e0e0e0'}
        )
    else:
        return (
            {**estilo_base_texto, 'display': 'block'},
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_base_texto, 'display': 'none'},
            {**estilo_btn_ativo, 'backgroundColor': '#e0e0e0'},
            {**estilo_btn_meio, 'backgroundColor': '#ffffff'},
            {**estilo_btn_fim, 'backgroundColor': '#ffffff'}
        )


# Callback do botão salvar
@app.callback(
    [
        Output("download_operacoes_csv", "data"),
        Output("status_salvar", "children")
    ],
    Input("botao_salvar", "n_clicks"),
    [
        State("tabela_operacoes", "data"),
        State("dropdown_ativo", "value")
    ],
    prevent_initial_call=True
)
def baixar_operacoes_csv(n_clicks, dados_tabela, ativo):
    if not n_clicks:
        return None, ""
    if not dados_tabela:
        return None, "Nenhuma operação para salvar! Simule primeiro."
    df_operacoes = pd.DataFrame(dados_tabela)
    nome_arquivo = f"operacoes_{ativo}.csv"
    return dcc.send_data_frame(df_operacoes.to_csv, nome_arquivo, index=False), "CSV gerado com sucesso!"


if __name__ == '__main__':
    app.run(debug=True)
