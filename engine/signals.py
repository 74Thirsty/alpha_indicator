"""Signal definitions leveraging engineered features."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

import pandas as pd


SignalCallable = Callable[..., pd.Series]


@dataclass(frozen=True)
class SignalBook:
    """Library of reusable indicator-driven signals."""

    registry: Dict[str, SignalCallable]

    def __init__(self, registry: Dict[str, SignalCallable] | None = None) -> None:
        object.__setattr__(self, "registry", registry or self._default_registry())

    @staticmethod
    def _default_registry() -> Dict[str, SignalCallable]:
        return {
            "rsi_extreme": SignalBook.rsi_extreme,
            "ema_bullish_cross": SignalBook.ema_bullish_cross,
            "ema_bearish_cross": SignalBook.ema_bearish_cross,
            "bollinger_breakout": SignalBook.bollinger_breakout,
            "stochastic_reversal": SignalBook.stochastic_reversal,
        }

    @staticmethod
    def rsi_extreme(df: pd.DataFrame, low: float = 30, high: float = 70) -> pd.Series:
        """Return points where RSI is outside of the provided bounds."""

        return (df["RSI"] < low) | (df["RSI"] > high)

    @staticmethod
    def ema_bullish_cross(df: pd.DataFrame, fast: int = 10, slow: int = 50) -> pd.Series:
        """Fast EMA crossing above slow EMA signals bullish momentum."""

        fast_series = df[f"EMA_{fast}"]
        slow_series = df[f"EMA_{slow}"]
        return (fast_series > slow_series) & (fast_series.shift(1) <= slow_series.shift(1))

    @staticmethod
    def ema_bearish_cross(df: pd.DataFrame, fast: int = 10, slow: int = 50) -> pd.Series:
        """Fast EMA crossing below slow EMA signals bearish momentum."""

        fast_series = df[f"EMA_{fast}"]
        slow_series = df[f"EMA_{slow}"]
        return (fast_series < slow_series) & (fast_series.shift(1) >= slow_series.shift(1))

    @staticmethod
    def bollinger_breakout(df: pd.DataFrame) -> pd.Series:
        """Price closing outside Bollinger bands often signals volatility expansion."""

        return (df["close"] > df["BB_UPPER"]) | (df["close"] < df["BB_LOWER"])

    @staticmethod
    def stochastic_reversal(
        df: pd.DataFrame, oversold: float = 20, overbought: float = 80
    ) -> pd.Series:
        """Detect reversals using the Stochastic oscillator."""

        return ((df["STOCH_K"] < oversold) & (df["STOCH_D"] > df["STOCH_K"])) | (
            (df["STOCH_K"] > overbought) & (df["STOCH_D"] < df["STOCH_K"])
        )

    def evaluate(self, name: str, df: pd.DataFrame, **kwargs) -> pd.Series:
        """Compute a registered signal by name."""

        if name not in self.registry:
            raise KeyError(f"Signal '{name}' is not registered")
        return self.registry[name](df, **kwargs)

    def register(self, name: str, func: SignalCallable) -> None:
        """Register a custom signal at runtime."""

        self.registry[name] = func
