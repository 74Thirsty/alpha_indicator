"""Example workflow that stitches together the Alpha Indicator components."""

from __future__ import annotations

import argparse

import numpy as np

from engine.feature_engine import FeatureEngine
from engine.models import AlphaModel
from engine.strategy_runner import StrategyRunner
from utils.data_loader import OHLCVLoader


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Alpha Indicator demo pipeline")
    parser.add_argument("source", help="CSV path or yfinance ticker symbol")
    parser.add_argument("--train-test-split", type=float, default=0.2, dest="test_size")
    parser.add_argument("--take-profit", type=float, default=0.1)
    parser.add_argument("--stop-loss", type=float, default=0.05)
    return parser.parse_args()


def build_targets(close_prices: np.ndarray, threshold: float = 0.0) -> np.ndarray:
    future_returns = np.roll(close_prices, -1) / close_prices - 1
    future_returns[-1] = 0  # last value has no look-ahead
    return (future_returns > threshold).astype(int)


def main() -> None:
    args = parse_args()

    loader = OHLCVLoader(args.source)
    df = loader.load()

    engine = FeatureEngine(df)
    enriched_df = engine.add_indicators()

    targets = build_targets(enriched_df["close"].to_numpy(), threshold=0.01)
    enriched_df = enriched_df.iloc[:-1].copy()
    targets = targets[:-1]

    feature_columns = [
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
    ]
    X = enriched_df[feature_columns]

    model = AlphaModel()
    metrics = model.train(X, targets, test_size=args.test_size)
    print("Model metrics:", metrics)

    runner = StrategyRunner(enriched_df)
    backtest = runner.run_backtest(
        entry_rule="RSI < 35",
        exit_rule="RSI > 65",
        sl=args.stop_loss,
        tp=args.take_profit,
    )
    print("Backtest summary:", backtest)


if __name__ == "__main__":
    main()
