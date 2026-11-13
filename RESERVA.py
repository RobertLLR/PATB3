# Importar as estratégias
from ESTRATEGIA import estrategia_RSI, estrategia_media, estrategia_bollinger

import pandas as pd
import matplotlib.pyplot as plt


# Selecionar a estratégia
class seletor_estrategia:
    def selecionar_estrategia(self, estrategia):

        if estrategia == "RSI":
            return estrategia_RSI

        elif estrategia == "medias":
            return estrategia_media

        elif estrategia == "bollinger":
            return estrategia_bollinger

        else:
            raise ValueError("Estratégia não encontrada.")
        return None


# Escolher a estratégia
seletor = seletor_estrategia()

objetivo = seletor.selecionar_estrategia("RSI")

limite_superior = 30
limite_inferior = 70
periodo = 14

# Executar a estratégia escolhida
resultado = objetivo( "teste_RSI_14_para_Amanda.csv", periodo, limite_superior, limite_inferior)

print (resultado)

resultado.to_csv("SAIDA_RSI.csv", index=False)


plt.figure(figsize=(12, 6))

# Linha do preço
plt.plot(resultado["Date"], resultado["Close"],
         label="Preço de fechamento")

# Pontos de compra
compras = resultado[resultado["sinal"] == 1]

plt.scatter(compras["Date"], compras["Close"],
            label="Compra", marker="^")

# Pontos de venda
vendas = resultado[resultado["sinal"] == -1]

plt.scatter(vendas["Date"], vendas["Close"],
            label="Venda", marker="v")

plt.title("Estratégia RSI - Compra e Venda")
plt.xlabel("Data")
plt.ylabel("Preço")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

# Colorir as datas do eixo horizontal
cores = ["blue", "red", "green", "purple", "orange"]

for i, etiqueta in enumerate(ax.get_xticklabels()):
    etiqueta.set_color(cores[i % len(cores)])
    etiqueta.set_fontweight("bold")

plt.tight_layout()