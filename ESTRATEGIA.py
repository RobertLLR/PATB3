import pandas as pd

def estrategia_RSI(arquivo, periodo, limite_superior, limite_inferior):

        df = pd.read_csv(arquivo)
        df["sinal"] = 0

        df.loc[df["RSI_14"] <= limite_superior, "sinal"] = 1
        df.loc[df["RSI_14"] >= limite_inferior, "sinal"] = -1

        resultado = df[["Date", "Ticker", "Open", "High","Low", "Close", "Volume", "RSI_14", "sinal"]].copy()

    
        return resultado

def estrategia_media():
        pass

def estrategia_bollinger():
        pass
 