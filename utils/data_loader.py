import pandas as pd
import yfinance as yf

class OHLCVLoader:
    def __init__(self, source: str):
        self.source = source

    def load(self) -> pd.DataFrame:
        if self.source.endswith(".csv"):
            df = pd.read_csv(self.source)
        else:
            df = yf.download(self.source, period="90d", interval="1d")
            df.reset_index(inplace=True)
        df.columns = [col.lower() for col in df.columns]
        return df[["open", "high", "low", "close", "volume"]].copy()