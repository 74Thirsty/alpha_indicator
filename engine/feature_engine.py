"""Feature engineering helpers for Alpha Indicator.

This module centralises the computation of technical indicators that power the
rest of the trading research workflow.  It is deliberately designed to be
extensible so the CLI (``main.py``), notebooks, or external services can add or
override indicators without rewriting the engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Mapping, Optional

import pandas as pd
from finta import TA


IndicatorCallable = Callable[[pd.DataFrame, pd.DataFrame], pd.Series]


def _ensure_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Validate that the dataframe exposes the OHLCV columns required by Finta."""

    required = {"open", "high", "low", "close", "volume"}
    missing = required.difference(col.lower() for col in df.columns)
    if missing:
        raise ValueError(
            "Dataframe is missing required OHLCV columns: " + ", ".join(sorted(missing))
        )
    return df


def _uppercase_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe copy whose columns are upper-cased for Finta."""

    renamed = {col: col.upper() for col in df.columns}
    return df.rename(columns=renamed)


def _ema(period: int) -> IndicatorCallable:
    return lambda finta_df, _raw_df: TA.EMA(finta_df, period)


def _sma(period: int) -> IndicatorCallable:
    return lambda finta_df, _raw_df: TA.SMA(finta_df, period)


def _bollinger(period: int, band: str) -> IndicatorCallable:
    def calculate(finta_df: pd.DataFrame, _raw_df: pd.DataFrame) -> pd.Series:
        bands = TA.BBANDS(finta_df, period=period)
        return bands[band]

    return calculate


def _atr(period: int) -> IndicatorCallable:
    return lambda finta_df, _raw_df: TA.ATR(finta_df, period=period)


def _stochastic_k(period: int) -> IndicatorCallable:
    return lambda finta_df, _raw_df: TA.STOCH(finta_df, period=period).rename("STOCH_K")


def _stochastic_d(period: int, stoch_period: int) -> IndicatorCallable:
    return lambda finta_df, _raw_df: TA.STOCHD(finta_df, period=period, stoch_period=stoch_period).rename(
        "STOCH_D"
    )


DEFAULT_INDICATORS: Mapping[str, IndicatorCallable] = {
    "EMA_10": _ema(10),
    "EMA_50": _ema(50),
    "SMA_20": _sma(20),
    "RSI": lambda finta_df, _raw_df: TA.RSI(finta_df),
    "MACD": lambda finta_df, _raw_df: TA.MACD(finta_df)["MACD"],
    "MACD_SIGNAL": lambda finta_df, _raw_df: TA.MACD(finta_df)["SIGNAL"],
    "OBV": lambda finta_df, raw_df: TA.OBV(raw_df),
    "BB_UPPER": _bollinger(period=20, band="BB_UPPER"),
    "BB_LOWER": _bollinger(period=20, band="BB_LOWER"),
    "ATR_14": _atr(14),
    "STOCH_K": _stochastic_k(period=14),
    "STOCH_D": _stochastic_d(period=3, stoch_period=14),
}


@dataclass
class FeatureEngine:
    """Compute and append technical indicators to OHLCV datasets."""

    df: pd.DataFrame
    indicators: Mapping[str, IndicatorCallable] = field(default_factory=lambda: DEFAULT_INDICATORS)
    dropna: bool = True

    def __post_init__(self) -> None:
        _ensure_required_columns(self.df)
        # Work on a copy to avoid mutating user supplied dataframes.
        self.df = self.df.copy()

    def add_indicators(
        self,
        extra_indicators: Optional[Mapping[str, IndicatorCallable]] = None,
        overwrite: bool = False,
    ) -> pd.DataFrame:
        """Return a dataframe enriched with the configured indicators.

        Parameters
        ----------
        extra_indicators:
            Additional indicator callables keyed by output column name.  These
            are merged with the engine's configured indicators at runtime.
        overwrite:
            If ``True`` existing columns will be replaced; otherwise we will
            skip indicators whose target column already exists.
        """

        indicators: Dict[str, IndicatorCallable]
        indicators = dict(self.indicators)
        if extra_indicators:
            indicators.update(extra_indicators)

        raw_df = self.df.copy()
        finta_ready = _uppercase_columns(raw_df)

        for column, indicator in indicators.items():
            if not overwrite and column in raw_df.columns:
                continue
            series = indicator(finta_ready, raw_df)
            raw_df[column] = series.astype(float)

        if self.dropna:
            raw_df = raw_df.dropna().reset_index(drop=True)

        return raw_df

    def available_indicators(self) -> Iterable[str]:
        """Return the indicator names currently configured on this engine."""

        return self.indicators.keys()
