"""Data loading utilities for Alpha Indicator."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf


@dataclass
class OHLCVLoader:
    """Load OHLCV data from CSV files or directly from yfinance."""

    source: str
    date_column: str = "date"

    def load(self) -> pd.DataFrame:
        if self.source.lower().endswith(".csv"):
            df = pd.read_csv(Path(self.source))
        else:
            df = yf.download(self.source, period="180d", interval="1d")
            df = df.reset_index()

        df.columns = [col.lower() for col in df.columns]

        if self.date_column in df.columns:
            df[self.date_column] = pd.to_datetime(df[self.date_column])
            df = df.sort_values(self.date_column).drop_duplicates(self.date_column)

        columns = ["open", "high", "low", "close", "volume"]
        missing = [col for col in columns if col not in df.columns]
        if missing:
            raise ValueError(f"Data source missing required columns: {missing}")

        return df[columns].reset_index(drop=True)
