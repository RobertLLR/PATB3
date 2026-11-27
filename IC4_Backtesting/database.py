import sqlite3
from datetime import datetime
from pathlib import Path

PASTA_BASE = Path(__file__).resolve().parent


def salvar_simulacao_db(nome, ativo, capital_inicial, data_inicio, data_fim, relatorio_texto):
    conexao = sqlite3.connect(PASTA_BASE / 'simulacoes_b3.db')
    cursor = conexao.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_simulacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_execucao TEXT,
            nome TEXT,
            ativo TEXT,
            capital_inicial REAL,
            data_inicio TEXT,
            data_fim TEXT,
            relatorio TEXT
        )
    ''')

    cursor.execute('''
        INSERT INTO historico_simulacoes (data_execucao, nome, ativo, capital_inicial, data_inicio, data_fim, relatorio)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        nome,
        ativo,
        capital_inicial,
        str(data_inicio),
        str(data_fim),
        relatorio_texto
    ))

    conexao.commit()
    conexao.close()
