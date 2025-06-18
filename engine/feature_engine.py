from finta import TA
import pandas as pd

class FeatureEngine:
def __init__(self, df: pd.DataFrame):
self.df = df.copy()

def add_indicators(self) -> pd.DataFrame:
self.df["EMA_10"] = TA.EMA(self.df, 10)
self.df["EMA_50"] = TA.EMA(self.df, 50)
self.df["RSI"] = TA.RSI(self.df)
self.df["MACD"] = TA.MACD(self.df)["MACD"]
self.df["OBV"] = TA.OBV(self.df)
return self.df.dropna()
