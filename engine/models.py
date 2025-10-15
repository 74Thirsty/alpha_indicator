"""Model utilities for the Alpha Indicator research engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

import numpy as np
import xgboost as xgb
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import train_test_split


@dataclass
class AlphaModel:
    """Wrapper around an XGBoost classifier with sensible defaults."""

    model: xgb.XGBClassifier = field(
        default_factory=lambda: xgb.XGBClassifier(
            use_label_encoder=False,
            eval_metric="logloss",
            enable_categorical=True,
            tree_method="hist",
        )
    )

    def train(
        self,
        X,
        y,
        *,
        test_size: float = 0.2,
        shuffle: bool = False,
        random_state: Optional[int] = None,
    ) -> Dict[str, float]:
        """Fit the classifier and return validation metrics.

        The default behaviour avoids shuffling to respect the temporal nature of
        most OHLCV datasets.  A dictionary containing the accuracy and log-loss
        is returned so callers can persist or log the diagnostics easily.
        """

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            shuffle=shuffle,
            random_state=random_state,
        )

        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        metrics = {"accuracy": float(accuracy_score(y_test, y_pred))}

        if hasattr(self.model, "predict_proba"):
            y_proba = self.model.predict_proba(X_test)
            metrics["log_loss"] = float(log_loss(y_test, y_proba, labels=np.unique(y)))

        return metrics

    def predict(self, X) -> np.ndarray:
        """Return class predictions for the provided feature matrix."""

        return self.model.predict(X)

    def predict_proba(self, X) -> np.ndarray:
        """Return class probabilities when the underlying model supports it."""

        if not hasattr(self.model, "predict_proba"):
            raise AttributeError("Underlying model does not expose predict_proba")
        return self.model.predict_proba(X)

    def feature_importances(self) -> Iterable[float]:
        """Return the feature importances if available."""

        if hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        raise AttributeError("Model does not provide feature importances")
