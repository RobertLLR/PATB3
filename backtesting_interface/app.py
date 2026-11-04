import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
from backtesting import gerar_backtesting
from database import salvar_simulacao_db
import pandas as pd

# Mapeamento dos arquivos CSV de cada ativo
ARQUIVOS_ATIVOS = {
    'BBAS3': 'BBAS3_2025.csv',
    'ITUB4': 'ITUB4_2025.csv'
}

app = Dash(__name__)

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
                style={'marginBottom': '12px', 'fontSize': '12px'}
            ),

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
            html.H4('Resumo do Ativo', style={
                    'margin': '0 0 8px 0', 'fontSize': '15px'}),
            html.Pre(
                id='saida_relatorio',
                children="",
                style={
                    'whiteSpace': 'pre-wrap',
                    'overflowWrap': 'break-word',
                    'margin': '0',
                    'fontFamily': 'monospace',
                    'fontSize': '11px',
                    'lineHeight': '1.2'
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


# CALLBACK GERENCIADOR DA SIMULAÇÃO E BOTÕES
@app.callback(
    [
        Output('saida_relatorio', 'children'),
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
        State('picker_data', 'start_date'),
        State('picker_data', 'end_date')
    ],
    prevent_initial_call=True
)
def gerenciar_simulacao(n_simular, n_resetar, nome, capital, ativo, data_inicio, data_fim):
    button_id = ctx.triggered_id

    # AÇÃO DE RESETAR / ENCERRAR SIMULAÇÃO
    if button_id == 'botao_resetar':
        return "", FIGURA_VAZIA, FIGURA_VAZIA, [], [], False

    # AÇÃO SIMULAR
    if button_id == 'botao_simular':
        caminho_csv = ARQUIVOS_ATIVOS[ativo]
        capital_valido = capital if capital and capital >= 1000 else 10000.0
        nome_investidor = nome.strip() if nome and nome.strip() else "Não informado"

        dados, operacoes, relatorio_texto = gerar_backtesting(
            caminho_csv, capital_inicial=capital_valido, data_inicio=data_inicio, data_fim=data_fim)

        cabecalho_usuario = f"Investidor: {nome_investidor}\nCapital: R$ {capital_valido:,.2f}\n"
        relatorio_final = cabecalho_usuario + relatorio_texto

        # 1. Gráfico de Preços (com o rangeselector e período preservados)
        grafico = go.Figure()

        grafico.add_trace(go.Scatter(
            x=dados['Date'],
            y=dados['Close'],
            mode='lines',
            name='Preço',
            line=dict(width=1.5)
        ))

        grafico.add_trace(go.Scatter(
            x=dados.loc[dados['executed_signal'] == 1, 'Date'],
            y=dados.loc[dados['executed_signal'] == 1, 'Close'],
            mode='markers',
            name='Compra',
            marker=dict(symbol='triangle-up', size=10, color='green')
        ))

        grafico.add_trace(go.Scatter(
            x=dados.loc[dados['executed_signal'] == -1, 'Date'],
            y=dados.loc[dados['executed_signal'] == -1, 'Close'],
            mode='markers',
            name='Venda',
            marker=dict(symbol='triangle-down', size=10, color='red')
        ))

        grafico.update_layout(
            title=dict(
                text=f'Evolução do Preço - {ativo}',
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
        grafico_capital.update_layout(
            title=dict(text=f'Evolução do Patrimônio - {ativo}', font=dict(
                size=13), x=0.01, y=0.98, xanchor='left', yanchor='top'),
            margin=dict(l=10, r=10, t=35, b=40),
            xaxis={'title': None},
            yaxis={'title': 'Patrimônio (R$)'}
        )

        # 3. Dados da Tabela
        dados_tabela = operacoes.to_dict('records')
        colunas_tabela = [{'name': col, 'id': col}
                          for col in operacoes.columns]

        return relatorio_final, grafico, grafico_capital, dados_tabela, colunas_tabela, True

    return "", FIGURA_VAZIA, FIGURA_VAZIA, [], [], False


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
