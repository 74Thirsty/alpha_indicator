import numpy as np
import pandas as pd

from engine.feature_engine import FeatureEngine
from engine.strategy_runner import StrategyRunner


def _constant_frame(rows: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    close = np.cumsum(rng.normal(0, 0.5, rows)) + 100
    open_ = close + rng.normal(0, 0.1, rows)
    high = np.maximum(open_, close) + rng.normal(0.2, 0.1, rows)
    low = np.minimum(open_, close) - rng.normal(0.2, 0.1, rows)
    volume = rng.integers(1_000, 5_000, rows)
    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


def test_add_indicators_produces_expected_columns():
    df = _constant_frame()
    fe = FeatureEngine(df)
    enriched = fe.add_indicators()

    expected_columns = {
        "EMA_10",
        "EMA_50",
        "SMA_20",
        "RSI",
        "MACD",
        "MACD_SIGNAL",
        "OBV",
        "BB_UPPER",
        "BB_LOWER",
        "ATR_14",
        "STOCH_K",
        "STOCH_D",
    }

    assert expected_columns.issubset(enriched.columns)
    assert not enriched.isnull().values.any()


def test_strategy_runner_generates_trades():
    df = _constant_frame()
    fe = FeatureEngine(df)
    enriched = fe.add_indicators()

    runner = StrategyRunner(enriched)
    results = runner.run_backtest(entry_rule="RSI < 40", exit_rule="RSI > 60", sl=0.05, tp=0.1)

    assert "ledger" in results
    assert isinstance(results["ledger"], list)
    assert results["trades"] == len(results["ledger"])
    assert results["max_drawdown"] >= 0
