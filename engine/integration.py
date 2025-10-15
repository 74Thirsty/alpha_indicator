"""Utilities for scoring arbitrage paths using trained models."""

from __future__ import annotations

from typing import Iterable, List, MutableMapping

import numpy as np


class ArbitragePathScorer:
    """Attach model-driven scores to arbitrage paths."""

    def __init__(self, model):
        self.model = model

    def score_paths(
        self,
        paths: Iterable[MutableMapping[str, object]],
        *,
        default_score: float = 0.0,
    ) -> List[MutableMapping[str, object]]:
        """Return paths sorted by descending score.

        Each ``path`` should expose a ``features`` key containing the feature
        vector expected by the fitted model.
        """

        scored_paths: List[MutableMapping[str, object]] = []
        for path in paths:
            features = path.get("features")
            if features is None:
                path["score"] = default_score
                scored_paths.append(path)
                continue

            features_array = np.asarray(features).reshape(1, -1)

            if hasattr(self.model, "predict_proba"):
                probabilities = self.model.predict_proba(features_array)[0]
                path["score"] = float(probabilities[-1])
            else:
                prediction = self.model.predict(features_array)[0]
                path["score"] = float(prediction)

            scored_paths.append(path)

        return sorted(scored_paths, key=lambda candidate: candidate.get("score", default_score), reverse=True)
