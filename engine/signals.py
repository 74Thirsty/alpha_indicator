import pandas as pd

class SignalBook:
@staticmethod
def rsi_cross(df: pd.DataFrame, low=30, high=70):
return (df["RSI"] < low) | (df["RSI"] > high)

@staticmethod
def ema_crossover(df: pd.DataFrame, fast=10, slow=50):
fast_ema = df[f"EMA_{fast}"]
slow_ema = df[f"EMA_{slow}"]
return (fast_ema > slow_ema) & (fast_ema.shift(1) <= slow_ema.shift(1))
