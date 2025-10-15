"""Backtesting utilities for Alpha Indicator strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence

import numpy as np
import pandas as pd


Condition = Callable[[pd.Series], bool]


@dataclass
class Trade:
    entry_index: int
    exit_index: int
    entry_price: float
    exit_price: float
    return_pct: float
    reason: str

    def to_dict(self) -> Dict[str, float | int | str]:
        return {
            "entry_index": self.entry_index,
            "exit_index": self.exit_index,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "return_pct": self.return_pct,
            "reason": self.reason,
        }


class StrategyRunner:
    """Execute simple long-only strategies using indicator-driven rules."""

    def __init__(self, df: pd.DataFrame):
        if "close" not in df.columns:
            raise ValueError("Dataframe must contain a 'close' column for PnL calculations")
        self.df = df.reset_index(drop=True).copy()

    @staticmethod
    def _resolve_condition(rule, df: pd.DataFrame) -> Sequence[bool] | Condition:
        if callable(rule):
            return rule
        if isinstance(rule, str):
            # Evaluate the rule vectorised for efficiency and safety.
            return df.eval(rule)
        raise TypeError("Rules must be either callables or pandas eval strings")

    def run_backtest(
        self,
        *,
        entry_rule,
        exit_rule,
        sl: float,
        tp: float,
    ) -> Dict[str, object]:
        """Run the backtest returning summary statistics and trade ledger."""

        entry_condition = self._resolve_condition(entry_rule, self.df)
        exit_condition = self._resolve_condition(exit_rule, self.df)

        trades: List[Trade] = []
        position_open = False
        entry_price = 0.0
        entry_index = 0

        def condition_at(rule, idx: int) -> bool:
            if callable(rule):
                return bool(rule(self.df.iloc[idx]))
            return bool(rule.iloc[idx])

        for idx in range(len(self.df)):
            price = float(self.df.iloc[idx]["close"])

            if not position_open:
                if condition_at(entry_condition, idx):
                    position_open = True
                    entry_price = price
                    entry_index = idx
                continue

            change = (price - entry_price) / entry_price
            should_exit = condition_at(exit_condition, idx)
            reason = None

            if change <= -sl:
                reason = "stop_loss"
            elif change >= tp:
                reason = "take_profit"
            elif should_exit:
                reason = "rule_exit"

            if reason:
                trades.append(
                    Trade(
                        entry_index=entry_index,
                        exit_index=idx,
                        entry_price=entry_price,
                        exit_price=price,
                        return_pct=change,
                        reason=reason,
                    )
                )
                position_open = False

        if position_open:
            # Force close any open position at the last available price.
            final_price = float(self.df.iloc[-1]["close"])
            change = (final_price - entry_price) / entry_price
            trades.append(
                Trade(
                    entry_index=entry_index,
                    exit_index=len(self.df) - 1,
                    entry_price=entry_price,
                    exit_price=final_price,
                    return_pct=change,
                    reason="end_of_data",
                )
            )

        returns = np.array([trade.return_pct for trade in trades], dtype=float)
        equity_curve = np.cumprod(1 + returns) if len(returns) else np.array([])
        max_drawdown = self._calculate_max_drawdown(equity_curve)

        wins = (returns > 0).sum() if len(returns) else 0
        win_rate = float(wins / len(returns)) if len(returns) else 0.0

        return {
            "trades": len(trades),
            "win_rate": win_rate,
            "average_return": float(returns.mean()) if len(returns) else 0.0,
            "cumulative_return": float(returns.sum()) if len(returns) else 0.0,
            "max_drawdown": max_drawdown,
            "equity_curve": equity_curve.tolist(),
            "ledger": [trade.to_dict() for trade in trades],
        }

    @staticmethod
    def _calculate_max_drawdown(equity_curve: np.ndarray) -> float:
        if equity_curve.size == 0:
            return 0.0
        peaks = np.maximum.accumulate(equity_curve)
        drawdowns = 1 - (equity_curve / peaks)
        return float(drawdowns.max())
